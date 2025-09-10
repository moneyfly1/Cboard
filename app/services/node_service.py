import re
import json
import base64
import yaml
import urllib.parse
import random
from typing import List, Dict, Any
from app.core.database import SessionLocal
from app.models.config import SystemConfig


class NodeService:
    def __init__(self, db=None):
        self.db = db or SessionLocal()
        self._nodes_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 缓存5分钟
    
    def get_nodes_from_clash_config(self) -> List[Dict[str, Any]]:
        """从数据库中的Clash配置解析节点信息"""
        try:
            # 检查缓存
            import time
            current_time = time.time()
            if (self._nodes_cache is not None and 
                self._cache_timestamp is not None and 
                current_time - self._cache_timestamp < self._cache_ttl):
                return self._nodes_cache
            # 从system_configs表获取Clash配置
            clash_config = self.db.query(SystemConfig).filter(
                SystemConfig.key == "clash_config"
            ).first()

            if not clash_config or not clash_config.value:
                print("未找到Clash配置")
                return []

            # 使用YAML解析器解析Clash配置
            try:
                config_data = yaml.safe_load(clash_config.value)
                if not config_data or 'proxies' not in config_data:
                    print("Clash配置格式错误或没有proxies部分")
                    return []
                
                proxies = config_data['proxies']
                if not isinstance(proxies, list):
                    print("proxies部分不是列表格式")
                    return []
                
                nodes = []
                for i, proxy in enumerate(proxies, 1):
                    if not isinstance(proxy, dict):
                        continue
                    
                    node_data = self._build_node_data_from_proxy(proxy, i)
                    if node_data:
                        nodes.append(node_data)
                
                # 注释掉重复的日志输出，避免与配置更新服务重复
                # print(f"成功解析 {len(nodes)} 个节点")
                
                # 更新缓存
                self._nodes_cache = nodes
                self._cache_timestamp = current_time
                return nodes
                
            except yaml.YAMLError as e:
                print(f"YAML解析失败: {e}")
                # 如果YAML解析失败，尝试手动解析
                return self._parse_clash_config_manually(clash_config.value)

        except Exception as e:
            print(f"解析Clash配置失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _build_node_data_from_proxy(self, proxy: dict, node_id: int) -> Dict[str, Any]:
        """从Clash代理配置构建节点数据"""
        try:
            node_name = proxy.get('name', '')
            node_type = proxy.get('type', '')
            server = proxy.get('server', '')
            port = proxy.get('port', '')
            
            if not node_name or not node_type or not server:
                return None
            
            return {
                "id": node_id,
                "name": node_name,
                "region": self._detect_region(node_name),
                "type": node_type,
                "status": "online",  # 默认在线
                "load": self._generate_load(),  # 生成负载数据
                "speed": 0.0,
                "uptime": 0,
                "latency": 0,
                "description": f"从Clash配置解析的{node_type}节点",
                "is_recommended": self._is_recommended(node_name),
                "is_active": True,
                "server": server,
                "port": port
            }
        except Exception as e:
            print(f"构建节点数据失败: {e}")
            return None
    
    def _parse_clash_config_manually(self, config_text: str) -> List[Dict[str, Any]]:
        """手动解析Clash配置（备用方案）"""
        try:
            # 找到proxies部分
            proxies_start = config_text.find('proxies:')
            if proxies_start == -1:
                print("未找到proxies部分")
                return []
            
            # 找到proxy-groups部分（proxies部分的结束）
            proxy_groups_start = config_text.find('proxy-groups:', proxies_start)
            if proxy_groups_start == -1:
                # 如果没有proxy-groups，找到rules部分
                rules_start = config_text.find('rules:', proxies_start)
                if rules_start == -1:
                    print("未找到proxies部分的结束位置")
                    return []
                proxies_section = config_text[proxies_start:rules_start]
            else:
                proxies_section = config_text[proxies_start:proxy_groups_start]
            
            # 解析每个代理节点
            nodes = []
            lines = proxies_section.split('\n')
            current_node = {}
            node_id = 1
            
            for line in lines:
                line = line.strip()
                if line.startswith('- name:'):
                    # 保存上一个节点
                    if current_node and 'name' in current_node:
                        node_data = self._build_node_data_from_manual_parse(current_node, node_id)
                        if node_data:
                            nodes.append(node_data)
                        node_id += 1
                    
                    # 开始新节点
                    current_node = {'name': line.replace('- name:', '').strip()}
                elif line.startswith('type:'):
                    current_node['type'] = line.replace('type:', '').strip()
                elif line.startswith('server:'):
                    current_node['server'] = line.replace('server:', '').strip()
                elif line.startswith('port:'):
                    current_node['port'] = line.replace('port:', '').strip()
                elif line.startswith('uuid:'):
                    current_node['uuid'] = line.replace('uuid:', '').strip()
                elif line.startswith('password:'):
                    current_node['password'] = line.replace('password:', '').strip()
                elif line.startswith('cipher:'):
                    current_node['cipher'] = line.replace('cipher:', '').strip()
                elif line.startswith('network:'):
                    current_node['network'] = line.replace('network:', '').strip()
                elif line.startswith('ws-path:'):
                    current_node['ws-path'] = line.replace('ws-path:', '').strip()
                elif line.startswith('ws-headers:'):
                    current_node['ws-headers'] = line.replace('ws-headers:', '').strip()
                elif line.startswith('tls:'):
                    current_node['tls'] = line.replace('tls:', '').strip()
                elif line.startswith('udp:'):
                    current_node['udp'] = line.replace('udp:', '').strip()
            
            # 保存最后一个节点
            if current_node and 'name' in current_node:
                node_data = self._build_node_data_from_manual_parse(current_node, node_id)
                if node_data:
                    nodes.append(node_data)
            
            # 注释掉重复的日志输出，避免与配置更新服务重复
            # print(f"手动解析成功 {len(nodes)} 个节点")
            
            # 更新缓存
            self._nodes_cache = nodes
            self._cache_timestamp = current_time
            return nodes
            
        except Exception as e:
            print(f"手动解析失败: {e}")
            return []
    
    def _build_node_data_from_manual_parse(self, node_info: dict, node_id: int) -> Dict[str, Any]:
        """从手动解析的节点信息构建节点数据"""
        try:
            node_name = node_info.get('name', '')
            node_type = node_info.get('type', '')
            server = node_info.get('server', '')
            port = node_info.get('port', '')
            
            if not node_name or not node_type or not server:
                return None
            
            return {
                "id": node_id,
                "name": node_name,
                "region": self._detect_region(node_name),
                "type": node_type,
                "status": "online",  # 默认在线
                "load": self._generate_load(),  # 生成负载数据
                "speed": 0.0,
                "uptime": 0,
                "latency": 0,
                "description": f"从Clash配置解析的{node_type}节点",
                "is_recommended": self._is_recommended(node_name),
                "is_active": True,
                "server": server,
                "port": port
            }
        except Exception as e:
            print(f"构建节点数据失败: {e}")
            return None
    
    def _build_node_data(self, node_info: dict, node_id: int) -> Dict[str, Any]:
        """构建节点数据"""
        node_name = node_info.get('name', '')
        node_type = node_info.get('type', '')
        server = node_info.get('server', '')
        port = node_info.get('port', '')
        
        return {
            "id": node_id,
            "name": node_name,
            "region": self._detect_region(node_name),
            "type": node_type,
            "status": "online",  # 默认在线
            "load": self._generate_load(),  # 生成负载数据
            "speed": 0.0,
            "uptime": 0,
            "latency": 0,
            "description": f"从Clash配置解析的{node_type}节点",
            "is_recommended": self._is_recommended(node_name),
            "is_active": True,
            "server": server,
            "port": port
        }
    
    def _detect_region(self, node_name: str) -> str:
        """从节点名称检测地区"""
        region_keywords = {
            '香港': ['香港', 'HK', 'Hong Kong', 'hongkong'],
            '美国': ['美国', 'US', 'United States', 'america', 'usa'],
            '日本': ['日本', 'JP', 'Japan', 'japan'],
            '新加坡': ['新加坡', 'SG', 'Singapore', 'singapore'],
            '英国': ['英国', 'UK', 'United Kingdom', 'britain'],
            '德国': ['德国', 'DE', 'Germany', 'germany'],
            '法国': ['法国', 'FR', 'France', 'france'],
            '加拿大': ['加拿大', 'CA', 'Canada', 'canada'],
            '澳洲': ['澳洲', 'AU', 'Australia', 'australia'],
            '台湾': ['台湾', 'TW', 'Taiwan', 'taiwan'],
            '韩国': ['韩国', 'KR', 'Korea', 'korea'],
            '俄罗斯': ['俄罗斯', 'RU', 'Russia', 'russia'],
            '印度': ['印度', 'IN', 'India', 'india'],
            '巴西': ['巴西', 'BR', 'Brazil', 'brazil'],
            '荷兰': ['荷兰', 'NL', 'Netherlands', 'netherlands'],
            '瑞士': ['瑞士', 'CH', 'Switzerland', 'switzerland'],
            '瑞典': ['瑞典', 'SE', 'Sweden', 'sweden'],
            '挪威': ['挪威', 'NO', 'Norway', 'norway'],
            '丹麦': ['丹麦', 'DK', 'Denmark', 'denmark'],
            '芬兰': ['芬兰', 'FI', 'Finland', 'finland'],
            '意大利': ['意大利', 'IT', 'Italy', 'italy'],
            '西班牙': ['西班牙', 'ES', 'Spain', 'spain'],
            '波兰': ['波兰', 'PL', 'Poland', 'poland'],
            '捷克': ['捷克', 'CZ', 'Czech', 'czech'],
            '奥地利': ['奥地利', 'AT', 'Austria', 'austria'],
            '比利时': ['比利时', 'BE', 'Belgium', 'belgium'],
            '葡萄牙': ['葡萄牙', 'PT', 'Portugal', 'portugal'],
            '希腊': ['希腊', 'GR', 'Greece', 'greece'],
            '土耳其': ['土耳其', 'TR', 'Turkey', 'turkey'],
            '以色列': ['以色列', 'IL', 'Israel', 'israel'],
            '阿联酋': ['阿联酋', 'AE', 'UAE', 'uae'],
            '沙特': ['沙特', 'SA', 'Saudi', 'saudi'],
            '埃及': ['埃及', 'EG', 'Egypt', 'egypt'],
            '南非': ['南非', 'ZA', 'South Africa', 'south africa'],
            '阿根廷': ['阿根廷', 'AR', 'Argentina', 'argentina'],
            '智利': ['智利', 'CL', 'Chile', 'chile'],
            '墨西哥': ['墨西哥', 'MX', 'Mexico', 'mexico'],
            '泰国': ['泰国', 'TH', 'Thailand', 'thailand'],
            '越南': ['越南', 'VN', 'Vietnam', 'vietnam'],
            '菲律宾': ['菲律宾', 'PH', 'Philippines', 'philippines'],
            '印尼': ['印尼', 'ID', 'Indonesia', 'indonesia'],
            '马来西亚': ['马来西亚', 'MY', 'Malaysia', 'malaysia'],
            '新西兰': ['新西兰', 'NZ', 'New Zealand', 'new zealand']
        }
        
        node_name_lower = node_name.lower()
        for region, keywords in region_keywords.items():
            for keyword in keywords:
                if keyword.lower() in node_name_lower:
                    return region
        
        return '未知'
    
    def _generate_load(self) -> float:
        """生成负载数据（0-100之间的随机数）"""
        import random
        return round(random.uniform(5, 25), 1)  # 负载在5-25%之间
    
    def _is_recommended(self, node_name: str) -> bool:
        """判断是否为推荐节点"""
        recommended_keywords = ['推荐', 'recommended', 'premium', 'premium', '高速', 'fast', '稳定', 'stable']
        node_name_lower = node_name.lower()
        return any(keyword.lower() in node_name_lower for keyword in recommended_keywords)
    
    def get_node_statistics(self) -> Dict[str, Any]:
        """获取节点统计信息"""
        nodes = self.get_nodes_from_clash_config()
        
        if not nodes:
            return {
                "total_nodes": 0,
                "online_nodes": 0,
                "offline_nodes": 0,
                "regions": 0,
                "regions_list": []
            }
        
        total_nodes = len(nodes)
        online_nodes = len([n for n in nodes if n["status"] == "online"])
        offline_nodes = total_nodes - online_nodes
        regions = list(set([n["region"] for n in nodes if n["region"] != "未知"]))
        
        return {
            "total_nodes": total_nodes,
            "online_nodes": online_nodes,
            "offline_nodes": offline_nodes,
            "regions": len(regions),
            "regions_list": regions
        }
    
    def clear_cache(self):
        """清除节点缓存"""
        self._nodes_cache = None
        self._cache_timestamp = None
    
    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()
