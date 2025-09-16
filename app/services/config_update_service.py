"""
配置更新服务
"""

import os
import json
import base64
import subprocess
import threading
import time
import yaml
import requests
import urllib.parse
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.models.config import SystemConfig
import logging

logger = logging.getLogger(__name__)

def unicode_decode(s):
    """Unicode解码函数"""
    try:
        return json.loads(f'"{s}"')
    except Exception:
        return s

def clean_name(name, filter_keywords=None):
    """清理节点名称 - 按照老代码逻辑，使用动态过滤关键词"""
    import re
    if not name:
        return name

    # 检查是否是重命名后的格式（如：英国-Trojan-001, 香港-SS-001等）
    # 如果是这种格式，直接返回，不进行清理
    if re.match(r'^[^\s]+-[A-Za-z]+-\d+$', name):
        return name

    # 如果提供了过滤关键词，使用动态关键词；否则使用默认关键词
    if filter_keywords and isinstance(filter_keywords, list):
        # 将过滤关键词转换为正则表达式
        keywords_str = '|'.join(re.escape(keyword) for keyword in filter_keywords)
    else:
        # 默认关键词（保持向后兼容）
        keywords_str = '官网|网址|连接|试用|导入|免费|Hoshino|Network|续|费|qq|超时|请更新|订阅|通知|域名|套餐|剩余|到期|流量|GB|TB|过期|expire|traffic|remain|迅云加速|快云加速|脉冲云|闪连一元公益机场|一元公益机场|公益机场|机场|加速|云'

    # 更强的机场后缀清理，支持多种常见无用后缀
    patterns = [
        f'[\\s]*[-_][\\s]*({keywords_str})[\\s]*$',
        r'[\s]*[-_][\s]*[0-9]+[\s]*$',
        r'[\s]*[-_][\s]*[A-Za-z]+[\s]*$',
        # 直接以这些词结尾也去除
        f'({keywords_str})$',
        # 处理没有空格的情况，如"-迅云加速"
        f'[-_]({keywords_str})$'
    ]
    for pattern in patterns:
        name = re.sub(pattern, '', name)

    # 去掉所有空格
    name = re.sub(r'[\s]+', '', name)
    name = name.strip()
    return name

def get_unique_name(name, name_count, node_type="节点", server=None, filter_keywords=None):
    """获取唯一名称 - 按照老代码逻辑，使用中文名称"""
    # 先清理名称
    name = clean_name(name, filter_keywords)
    name = name.strip()
    
    # 如果名称为空或只有默认名称，根据协议和地区重命名
    if not name or name in ["节点", "VLESS节点", "SS节点", "Trojan节点", "VMess节点", "SSR节点", "Hysteria2节点", "TUIC节点"]:
        # 从原始名称或服务器地址中提取地区信息
        region = extract_region_from_name(name, server)
        if not region:
            region = "未知地区"
        
        # 生成新的名称格式：地区-协议-编号
        name = f"{region}-{node_type}-001"
    
    # 检查名称是否已存在，如果存在则添加编号
    original_name = name
    counter = 1
    while name in name_count:
        counter += 1
        if "-" in original_name and original_name.split("-")[-1].isdigit():
            # 如果已经是编号格式，替换最后的编号
            parts = original_name.split("-")
            parts[-1] = f"{counter:03d}"
            name = "-".join(parts)
        else:
            # 否则添加编号
            name = f"{original_name}{counter:02d}"
    
    # 记录使用的名称
    name_count[name] = True
    return name

def extract_region_from_name(name, server=None):
    """从节点名称或服务器地址中提取地区信息"""
    import re
    
    # 地区关键词映射（中文名称）
    region_keywords = {
        '香港': ['香港', 'HK', 'Hong Kong', '🇭🇰', 'hk', 'hongkong'],
        '台湾': ['台湾', 'TW', 'Taiwan', '🇹🇼', 'tw', 'taiwan'],
        '日本': ['日本', 'JP', 'Japan', '🇯🇵', 'jp', 'japan', 'tokyo', 'osaka'],
        '韩国': ['韩国', 'KR', 'Korea', '🇰🇷', 'kr', 'korea', 'seoul'],
        '新加坡': ['新加坡', 'SG', 'Singapore', '🇸🇬', 'sg', 'singapore'],
        '美国': ['美国', 'US', 'USA', 'United States', '🇺🇸', 'us', 'usa', 'america', 'newyork', 'losangeles', 'chicago', 'miami'],
        '英国': ['英国', 'UK', 'United Kingdom', '🇬🇧', 'uk', 'london', 'britain'],
        '德国': ['德国', 'DE', 'Germany', '🇩🇪', 'de', 'germany', 'berlin', 'frankfurt'],
        '法国': ['法国', 'FR', 'France', '🇫🇷', 'fr', 'france', 'paris'],
        '加拿大': ['加拿大', 'CA', 'Canada', '🇨🇦', 'ca', 'canada', 'toronto', 'vancouver'],
        '澳大利亚': ['澳大利亚', 'AU', 'Australia', '🇦🇺', 'au', 'australia', 'sydney', 'melbourne'],
        '荷兰': ['荷兰', 'NL', 'Netherlands', '🇳🇱', 'nl', 'netherlands', 'amsterdam'],
        '瑞士': ['瑞士', 'CH', 'Switzerland', '🇨🇭', 'ch', 'switzerland', 'zurich'],
        '瑞典': ['瑞典', 'SE', 'Sweden', '🇸🇪', 'se', 'sweden', 'stockholm'],
        '挪威': ['挪威', 'NO', 'Norway', '🇳🇴', 'no', 'norway', 'oslo'],
        '丹麦': ['丹麦', 'DK', 'Denmark', '🇩🇰', 'dk', 'denmark', 'copenhagen'],
        '芬兰': ['芬兰', 'FI', 'Finland', '🇫🇮', 'fi', 'finland', 'helsinki'],
        '意大利': ['意大利', 'IT', 'Italy', '🇮🇹', 'it', 'italy', 'rome', 'milan'],
        '西班牙': ['西班牙', 'ES', 'Spain', '🇪🇸', 'es', 'spain', 'madrid', 'barcelona'],
        '俄罗斯': ['俄罗斯', 'RU', 'Russia', '🇷🇺', 'ru', 'russia', 'moscow'],
        '印度': ['印度', 'IN', 'India', '🇮🇳', 'in', 'india', 'mumbai', 'delhi'],
        '巴西': ['巴西', 'BR', 'Brazil', '🇧🇷', 'br', 'brazil', 'sao paulo', 'rio'],
        '阿根廷': ['阿根廷', 'AR', 'Argentina', '🇦🇷', 'ar', 'argentina', 'buenos aires'],
        '智利': ['智利', 'CL', 'Chile', '🇨🇱', 'cl', 'chile', 'santiago'],
        '墨西哥': ['墨西哥', 'MX', 'Mexico', '🇲🇽', 'mx', 'mexico', 'mexico city'],
        '土耳其': ['土耳其', 'TR', 'Turkey', '🇹🇷', 'tr', 'turkey', 'istanbul'],
        '以色列': ['以色列', 'IL', 'Israel', '🇮🇱', 'il', 'israel', 'tel aviv'],
        '南非': ['南非', 'ZA', 'South Africa', '🇿🇦', 'za', 'south africa', 'cape town'],
        '埃及': ['埃及', 'EG', 'Egypt', '🇪🇬', 'eg', 'egypt', 'cairo'],
        '泰国': ['泰国', 'TH', 'Thailand', '🇹🇭', 'th', 'thailand', 'bangkok'],
        '马来西亚': ['马来西亚', 'MY', 'Malaysia', '🇲🇾', 'my', 'malaysia', 'kuala lumpur'],
        '印度尼西亚': ['印度尼西亚', 'ID', 'Indonesia', '🇮🇩', 'id', 'indonesia', 'jakarta'],
        '菲律宾': ['菲律宾', 'PH', 'Philippines', '🇵🇭', 'ph', 'philippines', 'manila'],
        '越南': ['越南', 'VN', 'Vietnam', '🇻🇳', 'vn', 'vietnam', 'ho chi minh'],
        '中国': ['中国', 'CN', 'China', '🇨🇳', 'cn', 'china', 'beijing', 'shanghai', 'guangzhou', 'shenzhen']
    }
    
    # 首先从名称中检查
    if name:
        for region, keywords in region_keywords.items():
            for keyword in keywords:
                if keyword.lower() in name.lower():
                    return region
    
    # 如果名称中没有找到，从服务器地址中检查
    if server:
        for region, keywords in region_keywords.items():
            for keyword in keywords:
                if keyword.lower() in server.lower():
                    return region
    
    return None

class ConfigUpdateService:
    def __init__(self, db: Session):
        self.db = db
        self.is_running_flag = False
        self.scheduled_task = None
        self.scheduled_thread = None
        self.logs = []
        self.max_logs = 1000
        
        # 默认配置（仅作为备用，实际使用后台配置）
        self.default_config = {
            "urls": [],
            "target_dir": "./uploads/config",
            "v2ray_file": "xr",
            "clash_file": "clash.yaml",
            "update_interval": 3600,  # 1小时
            "enable_schedule": False,
            "filter_keywords": []
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "is_running": self.is_running_flag,
            "scheduled_enabled": self.scheduled_task is not None,
            "last_update": self._get_last_update_time(),
            "next_update": self._get_next_update_time(),
            "config_exists": self._check_config_files_exist()
        }
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.is_running_flag
    
    def run_update_task(self):
        """运行更新任务"""
        if self.is_running_flag:
            self._add_log("任务已在运行中", "warning")
            return
        
        self.is_running_flag = True
        self._add_log("开始执行配置更新任务", "info")
        
        # 在后台任务中创建新的数据库连接
        db = SessionLocal()
        try:
            # 更新数据库连接
            self.db = db
            
            # 获取配置
            config = self.get_config()
            
            # 创建目标目录
            target_dir = config.get("target_dir", "./uploads/config")
            os.makedirs(target_dir, exist_ok=True)
            
            # 下载和处理节点
            nodes = self._download_and_process_nodes(config)
            
            # 生成配置文件
            if nodes:
                self._add_log(f"📝 开始生成配置文件，共 {len(nodes)} 个节点", "info")
                
                # 生成v2ray配置
                v2ray_file = os.path.join(target_dir, config.get("v2ray_file", "xr"))
                self._add_log(f"🔧 正在生成V2Ray配置文件: {v2ray_file}", "info")
                self._generate_v2ray_config(nodes, v2ray_file)
                
                # 生成clash配置
                clash_file = os.path.join(target_dir, config.get("clash_file", "clash.yaml"))
                self._add_log(f"🔧 正在生成Clash配置文件: {clash_file}", "info")
                filter_keywords = config.get("filter_keywords", [])
                self._generate_clash_config(nodes, clash_file, filter_keywords)
                
                self._add_log(f"🎉 配置更新完成！成功处理了 {len(nodes)} 个节点", "success")
                self._update_last_update_time()
            else:
                self._add_log("❌ 未获取到有效节点，跳过配置文件生成", "error")
            
            self._add_log("配置更新任务完成", "success")
                
        except Exception as e:
            self._add_log(f"配置更新失败: {str(e)}", "error")
            logger.error(f"配置更新失败: {str(e)}", exc_info=True)
        finally:
            # 添加短暂延迟，确保前端能获取到运行状态
            import time
            time.sleep(1)
            self.is_running_flag = False
            # 关闭数据库连接
            if db:
                db.close()
    
    def run_test_task(self):
        """运行测试任务（不保存文件）"""
        if self.is_running_flag:
            self._add_log("任务已在运行中", "warning")
            return
        
        self.is_running_flag = True
        self._add_log("开始执行测试任务", "info")
        
        # 在后台任务中创建新的数据库连接
        db = SessionLocal()
        try:
            # 更新数据库连接
            self.db = db
            
            # 获取配置
            config = self.get_config()
            
            # 下载和处理节点（测试模式）
            nodes = self._download_and_process_nodes(config)
            
            if nodes:
                self._add_log(f"测试完成，处理了 {len(nodes)} 个节点", "success")
            else:
                self._add_log("测试失败，未获取到有效节点", "error")
            
            self._add_log("测试任务完成", "success")
                
        except Exception as e:
            self._add_log(f"测试失败: {str(e)}", "error")
            logger.error(f"测试失败: {str(e)}", exc_info=True)
        finally:
            self.is_running_flag = False
            # 关闭数据库连接
            if db:
                db.close()
    
    def stop_update_task(self):
        """停止更新任务"""
        if self.is_running_flag:
            self.is_running_flag = False
            self._add_log("任务已停止", "info")
        else:
            self._add_log("任务未在运行", "warning")
    
    def _download_and_process_nodes(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """下载和处理节点，返回带来源信息的节点列表"""
        urls = config.get("urls", [])
        filter_keywords = config.get("filter_keywords", [])
        nodes = []
        
        # 检查是否配置了节点源URL
        if not urls:
            self._add_log("❌ 错误：未配置节点源URL，请在后台设置中添加节点源", "error")
            raise ValueError("未配置节点源URL，请在后台设置中添加节点源")
        
        self._add_log(f"🚀 开始节点采集，共 {len(urls)} 个节点源", "info")
        
        # 检查是否配置了过滤关键词
        if not filter_keywords:
            self._add_log("⚠️ 警告：未配置过滤关键词，将不过滤任何节点", "warning")
        else:
            self._add_log(f"🔍 过滤关键词: {', '.join(filter_keywords)}", "info")
        
        for i, url in enumerate(urls, 1):
            try:
                self._add_log(f"📥 [{i}/{len(urls)}] 正在下载节点源: {url}", "info")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                content = response.text
                content_size = len(content)
                self._add_log(f"📊 下载完成，内容大小: {content_size} 字符", "info")
                
                # 检查是否是base64编码
                if self._is_base64(content):
                    try:
                        content = base64.b64decode(content).decode('utf-8')
                        self._add_log(f"🔓 Base64解码成功，解码后大小: {len(content)} 字符", "info")
                    except:
                        self._add_log(f"⚠️ Base64解码失败，使用原始内容", "warning")
                
                # 提取节点链接
                node_links = self._extract_node_links(content)
                self._add_log(f"🔗 从 {url} 提取到 {len(node_links)} 个节点链接", "info")
                
                # 显示节点类型统计
                if node_links:
                    type_count = {}
                    for link in node_links:
                        if link.startswith('ss://'):
                            type_count['SS'] = type_count.get('SS', 0) + 1
                        elif link.startswith('ssr://'):
                            type_count['SSR'] = type_count.get('SSR', 0) + 1
                        elif link.startswith('vmess://'):
                            type_count['VMess'] = type_count.get('VMess', 0) + 1
                        elif link.startswith('trojan://'):
                            type_count['Trojan'] = type_count.get('Trojan', 0) + 1
                        elif link.startswith('vless://'):
                            type_count['VLESS'] = type_count.get('VLESS', 0) + 1
                        elif link.startswith('hysteria2://') or link.startswith('hy2://'):
                            type_count['Hysteria2'] = type_count.get('Hysteria2', 0) + 1
                        elif link.startswith('tuic://'):
                            type_count['TUIC'] = type_count.get('TUIC', 0) + 1
                    
                    if type_count:
                        type_info = ', '.join([f"{k}: {v}" for k, v in type_count.items()])
                        self._add_log(f"📈 节点类型统计: {type_info}", "info")
                
                # 过滤节点
                if filter_keywords:
                    filtered_links = self._filter_nodes(node_links, filter_keywords)
                    filtered_count = len(node_links) - len(filtered_links)
                    self._add_log(f"🔍 过滤掉 {filtered_count} 个节点，保留 {len(filtered_links)} 个节点", "info")
                else:
                    filtered_links = node_links
                    self._add_log(f"✅ 未设置过滤条件，保留所有 {len(filtered_links)} 个节点", "info")
                
                # 为每个节点添加来源信息
                for link in filtered_links:
                    nodes.append({
                        'url': link,
                        'source_index': i - 1,  # 0-based index
                        'source_url': url,
                        'is_first_source': i == 1  # 标记是否是第一个源
                    })
                
                self._add_log(f"✅ [{i}/{len(urls)}] 从 {url} 成功获取 {len(filtered_links)} 个有效节点", "success")
                
            except Exception as e:
                self._add_log(f"❌ [{i}/{len(urls)}] 下载 {url} 失败: {str(e)}", "error")
        
        # 不在这里进行全局去重，保持所有节点，在生成配置时分别处理
        total_count = len(nodes)
        self._add_log(f"🎉 节点采集完成！总共获得 {total_count} 个节点", "success")
        
        return nodes
    
    def _is_base64(self, text: str) -> bool:
        """检查文本是否是base64编码"""
        try:
            # 移除空白字符，但保留换行符
            clean_text = ''.join(text.split())
            # 检查是否只包含base64字符
            if len(clean_text) % 4 != 0:
                return False
            # 尝试解码
            base64.b64decode(clean_text)
            return True
        except:
            # 如果上面的方法失败，尝试直接解码原始文本
            try:
                base64.b64decode(text)
                return True
            except:
                return False
    
    def _extract_node_links(self, content: str) -> List[str]:
        """提取节点链接"""
        import re
        # 使用更精确的正则表达式，避免误匹配
        patterns = [
            r'vmess://[A-Za-z0-9+/=]+',
            r'vless://[A-Za-z0-9+/=@:?#.-]+',  # 添加点号支持域名
            r'ss://[A-Za-z0-9+/=@:?#.-]+',  # 添加点号支持域名
            r'ssr://[A-Za-z0-9+/=]+',
            r'trojan://[A-Za-z0-9-]+@[^:\s]+:\d+(?:[?&][^#\s]*)?(?:#[^\s]*)?',  # 精确匹配Trojan格式
            r'hysteria2://[A-Za-z0-9+/=@:?#.-]+',  # 添加点号支持域名
            r'hy2://[A-Za-z0-9+/=@:?#.-]+',  # 添加点号支持域名
            r'tuic://[A-Za-z0-9+/=@:?#.-]+'  # 添加点号支持域名
        ]
        
        links = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            links.extend(matches)
        
        return links
    
    def _filter_nodes(self, nodes: List[str], keywords: List[str]) -> List[str]:
        """过滤节点"""
        filtered = []
        keyword_pattern = '|'.join(keywords)
        
        for node in nodes:
            # 简单的关键词过滤
            if not any(keyword in node for keyword in keywords):
                filtered.append(node)
        
        return filtered
    
    def _generate_v2ray_config(self, nodes: List[Dict[str, Any]], output_file: str):
        """生成v2ray配置"""
        try:
            self._add_log(f"📋 开始生成V2Ray配置，节点数量: {len(nodes)}", "info")
            
            # 分离第一个源的节点和其他源的节点
            first_source_nodes = [node for node in nodes if node.get('is_first_source', False)]
            other_source_nodes = [node for node in nodes if not node.get('is_first_source', False)]
            
            # 确保第一个源的节点在最前面
            ordered_nodes = first_source_nodes + other_source_nodes
            
            # 将节点链接合并并base64编码
            node_urls = [node['url'] for node in ordered_nodes]
            content = '\n'.join(node_urls)
            content_size = len(content)
            self._add_log(f"📊 节点内容大小: {content_size} 字符", "info")
            
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            encoded_size = len(encoded_content)
            self._add_log(f"🔐 Base64编码完成，编码后大小: {encoded_size} 字符", "info")
            
            # 保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(encoded_content)
            
            file_size = os.path.getsize(output_file)
            self._add_log(f"💾 V2Ray配置文件已保存: {output_file} (大小: {file_size} 字节)", "info")
            
            # 保存到数据库
            self._save_v2ray_config_to_db(encoded_content)
            
            self._add_log(f"✅ V2Ray配置生成完成！文件: {output_file}", "success")
        except Exception as e:
            self._add_log(f"❌ 生成V2Ray配置失败: {str(e)}", "error")
            raise
    
    def _generate_clash_config(self, nodes: List[Dict[str, Any]], output_file: str, filter_keywords: List[str] = None):
        """生成clash配置 - 按照老代码逻辑"""
        try:
            self._add_log(f"📋 开始生成Clash配置，节点数量: {len(nodes)}", "info")
            
            # 按照老代码逻辑解析所有节点
            proxies = []
            proxy_names = []
            name_count = {}
            
            
            self._add_log(f"🔍 开始解析 {len(nodes)} 个节点为Clash格式", "info")
            
            # 统计节点类型
            node_type_count = {}
            failed_count = 0
            
            # 分离第一个源的节点和其他源的节点
            first_source_nodes = [node for node in nodes if node.get('is_first_source', False)]
            other_source_nodes = [node for node in nodes if not node.get('is_first_source', False)]
            
            if first_source_nodes:
                self._add_log(f"🔍 检测到第一个源的节点 {len(first_source_nodes)} 个，将完全保持原始名称和顺序", "info")
            if other_source_nodes:
                self._add_log(f"🔍 检测到其他源的节点 {len(other_source_nodes)} 个，将在其他源之间进行去重和重命名", "info")
            
            # 先处理第一个源的节点（完全保持原始状态，不进行任何解析验证）
            # 这些节点必须放在最前面，不参与去重和重命名
            first_source_proxies = []
            first_source_proxy_names = []
            first_source_name_count = {}  # 用于跟踪第一个源的节点名称计数
            
            for i, node_info in enumerate(first_source_nodes, 1):
                try:
                    node_url = node_info['url']
                    # 记录节点类型
                    if node_url.startswith('ss://'):
                        node_type = 'SS'
                    elif node_url.startswith('ssr://'):
                        node_type = 'SSR'
                    elif node_url.startswith('vmess://'):
                        node_type = 'VMess'
                    elif node_url.startswith('trojan://'):
                        node_type = 'Trojan'
                    elif node_url.startswith('vless://'):
                        node_type = 'VLESS'
                    elif node_url.startswith('hysteria2://') or node_url.startswith('hy2://'):
                        node_type = 'Hysteria2'
                    elif node_url.startswith('tuic://'):
                        node_type = 'TUIC'
                    else:
                        node_type = 'Unknown'
                    
                    # 第一个源的节点不进行重命名，但需要解析以生成正确的Clash配置
                    # 使用不重命名的解析方法，保持原始名称
                    proxy = self._parse_node_without_rename(node_url)
                    if proxy:
                        # 确保第一个源的节点名称唯一
                        original_name = proxy['name']
                        if original_name in first_source_name_count:
                            first_source_name_count[original_name] += 1
                            unique_name = f"{original_name} #{first_source_name_count[original_name]}"
                        else:
                            first_source_name_count[original_name] = 1
                            unique_name = original_name
                        
                        # 更新节点名称
                        proxy['name'] = unique_name
                        
                        # 第一个源的节点添加到临时列表
                        first_source_proxies.append(proxy)
                        first_source_proxy_names.append(unique_name)
                        node_type_count[node_type] = node_type_count.get(node_type, 0) + 1
                    else:
                        # 如果解析失败，跳过这个节点，不添加到配置中
                        failed_count += 1
                        if failed_count <= 5:  # 只记录前5个失败案例
                            self._add_log(f"⚠️ 第一个源第 {i} 个节点解析失败: {node_type} 节点格式错误", "warning")
                    
                    # 每100个节点记录一次进度
                    if i % 100 == 0:
                        self._add_log(f"📊 已处理第一个源 {i}/{len(first_source_nodes)} 个节点", "info")
                        
                except Exception as e:
                    failed_count += 1
                    if failed_count <= 5:  # 只记录前5个失败案例
                        self._add_log(f"⚠️ 处理第一个源第 {i} 个节点异常: {str(e)}", "warning")
                    continue
            
            # 将第一个源的节点添加到最前面
            proxies = first_source_proxies + proxies
            proxy_names = first_source_proxy_names + proxy_names
            
            # 再处理其他源的节点（只在这些源之间进行去重和重命名，不与第一个源对比）
            if other_source_nodes:
                # 在其他源节点之间进行去重（根据节点类型使用不同的去重策略）
                other_source_urls = set()
                unique_other_nodes = []
                for node_info in other_source_nodes:
                    node_url = node_info['url']
                    
                    # 根据节点类型决定去重策略
                    if node_url.startswith('ssr://') or node_url.startswith('vmess://'):
                        # SSR和VMESS节点：使用完整URL进行去重
                        dedup_key = node_url
                    else:
                        # 其他节点（SS、VLESS、Trojan等）：使用#之前的内容进行去重
                        if '#' in node_url:
                            dedup_key = node_url.split('#')[0]
                        else:
                            dedup_key = node_url
                    
                    if dedup_key not in other_source_urls:
                        other_source_urls.add(dedup_key)
                        unique_other_nodes.append(node_info)
                
                if len(unique_other_nodes) != len(other_source_nodes):
                    duplicate_count = len(other_source_nodes) - len(unique_other_nodes)
                    self._add_log(f"🔄 其他源节点去重: 原始 {len(other_source_nodes)} 个，去重后 {len(unique_other_nodes)} 个，移除 {duplicate_count} 个重复节点", "info")
                
                # 解析其他源的节点
                for i, node_info in enumerate(unique_other_nodes, 1):
                    try:
                        node_url = node_info['url']
                        # 记录节点类型
                        if node_url.startswith('ss://'):
                            node_type = 'SS'
                        elif node_url.startswith('ssr://'):
                            node_type = 'SSR'
                        elif node_url.startswith('vmess://'):
                            node_type = 'VMess'
                        elif node_url.startswith('trojan://'):
                            node_type = 'Trojan'
                        elif node_url.startswith('vless://'):
                            node_type = 'VLESS'
                        elif node_url.startswith('hysteria2://') or node_url.startswith('hy2://'):
                            node_type = 'Hysteria2'
                        elif node_url.startswith('tuic://'):
                            node_type = 'TUIC'
                        else:
                            node_type = 'Unknown'
                        
                        # 其他源的节点进行重命名和去重
                        proxy = self._parse_node_legacy(node_url, name_count, filter_keywords)
                        if proxy:
                            proxies.append(proxy)
                            proxy_names.append(proxy['name'])
                            node_type_count[node_type] = node_type_count.get(node_type, 0) + 1
                            
                            # 每100个节点记录一次进度
                            if i % 100 == 0:
                                self._add_log(f"📊 已解析其他源 {i}/{len(unique_other_nodes)} 个节点", "info")
                        else:
                            failed_count += 1
                            if failed_count <= 5:  # 只记录前5个失败案例
                                self._add_log(f"⚠️ 解析其他源第 {i} 个节点失败: {node_type} 节点格式错误", "warning")
                            
                    except Exception as e:
                        failed_count += 1
                        if failed_count <= 5:  # 只记录前5个失败案例
                            self._add_log(f"⚠️ 解析其他源第 {i} 个节点异常: {str(e)}", "warning")
                        continue
            
            # 显示解析结果统计
            if node_type_count:
                type_info = ', '.join([f"{k}: {v}" for k, v in node_type_count.items()])
                self._add_log(f"📈 成功解析节点类型统计: {type_info}", "info")
            
            self._add_log(f"📊 解析完成: 成功 {len(proxies)} 个节点，失败 {failed_count} 个", "info")
            
            if not proxies:
                self._add_log("❌ 没有有效的节点可以生成Clash配置", "error")
                return
            
            self._add_log(f"🔧 开始生成Clash配置文件，使用 {len(proxies)} 个有效节点", "info")
            
            # 使用老代码的模板生成完整的Clash配置
            clash_config_content = self._generate_clash_with_legacy_template(proxies, proxy_names)
            
            config_size = len(clash_config_content)
            self._add_log(f"📊 Clash配置内容大小: {config_size} 字符", "info")
            
            # 保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(clash_config_content)
            
            file_size = os.path.getsize(output_file)
            self._add_log(f"💾 Clash配置文件已保存: {output_file} (大小: {file_size} 字节)", "info")
            
            # 保存到数据库
            self._save_clash_config_to_db(clash_config_content)
            
            # 清除节点服务缓存，确保下次获取节点时使用最新配置
            try:
                from app.services.node_service import NodeService
                node_service = NodeService(self.db)
                node_service.clear_cache()
                node_service.close()
                self._add_log(f"🔄 节点服务缓存已清除", "info")
            except Exception as e:
                self._add_log(f"⚠️ 清除节点缓存失败: {str(e)}", "warning")
            
            self._add_log(f"✅ Clash配置生成完成！文件: {output_file}，共 {len(proxies)} 个节点", "success")
        except Exception as e:
            self._add_log(f"❌ 生成Clash配置失败: {str(e)}", "error")
            raise
    
    def _parse_node_to_clash(self, node_url: str, default_name: str, name_count: dict) -> Optional[Dict[str, Any]]:
        """解析节点URL为Clash格式"""
        try:
            if node_url.startswith('vmess://'):
                return self._parse_vmess_to_clash(node_url, default_name, name_count)
            elif node_url.startswith('vless://'):
                return self._parse_vless_to_clash(node_url, default_name, name_count)
            elif node_url.startswith('ss://'):
                return self._parse_ss_to_clash(node_url, default_name, name_count)
            elif node_url.startswith('ssr://'):
                return self._parse_ssr_to_clash(node_url, default_name, name_count)
            elif node_url.startswith('trojan://'):
                return self._parse_trojan_to_clash(node_url, default_name, name_count)
            elif node_url.startswith('hysteria2://') or node_url.startswith('hy2://'):
                return self._parse_hysteria2_to_clash(node_url, default_name, name_count)
            elif node_url.startswith('tuic://'):
                return self._parse_tuic_to_clash(node_url, default_name, name_count)
            else:
                return None
        except Exception as e:
            self._add_log(f"解析节点失败: {str(e)}", "warning")
            return None
    
    def _get_unique_name(self, name: str, name_count: dict) -> str:
        """获取唯一名称"""
        # 清理名称
        import re
        name = re.sub(r'[\s]+', '', name).strip()
        if not name:
            name = "节点"
        
        # 检查名称是否已存在
        original_name = name
        counter = 1
        while name in name_count:
            counter += 1
            name = f"{original_name}{counter:02d}"
        
        name_count[name] = True
        return name
    
    def _parse_vmess_to_clash(self, vmess_url: str, default_name: str, name_count: dict, use_filter: bool = True) -> Optional[Dict[str, Any]]:
        """解析VMess节点"""
        try:
            import urllib.parse
            b64 = vmess_url[8:]  # 去掉 'vmess://'
            b64 += '=' * (-len(b64) % 4)  # 补齐padding
            raw = base64.b64decode(b64).decode('utf-8')
            data = json.loads(raw)
            
            name = data.get('ps', '')
            if name:
                name = urllib.parse.unquote(name)
                try:
                    name = json.loads(f'"{name}"')
                except:
                    pass
            
            if not name or name.strip() == '' or name == 'vmess':
                name = default_name
            
            # 如果不重命名（name_count为空），直接使用原始名称
            if not name_count:
                final_name = name
            else:
                if use_filter:
                    final_name = self._get_unique_name(name, name_count)
                else:
                    # 不使用过滤关键词，直接使用原始名称
                    final_name = name
            
            proxy = {
                'name': final_name,
                'type': 'vmess',
                'server': data.get('add'),
                'port': int(data.get('port', 443)),
                'uuid': data.get('id'),
                'alterId': int(data.get('aid', 0)),
                'cipher': data.get('scy', 'auto'),
                'udp': True,
                'tls': data.get('tls') == 'tls'
            }
            
            # 处理网络类型
            network = data.get('net', 'tcp')
            if network == 'ws':
                proxy['network'] = 'ws'
                proxy['ws-opts'] = {
                    'path': data.get('path', '/'),
                    'headers': {'Host': data.get('host', '')}
                }
            elif network == 'grpc':
                proxy['network'] = 'grpc'
                proxy['grpc-opts'] = {
                    'grpc-service-name': data.get('path', '')
                }
            elif network == 'h2':
                proxy['network'] = 'h2'
                proxy['h2-opts'] = {
                    'host': [data.get('host', '')],
                    'path': data.get('path', '/')
                }
            
            # 处理TLS
            if data.get('tls') == 'tls':
                proxy['tls'] = True
                if data.get('sni'):
                    proxy['servername'] = data.get('sni')
                elif data.get('host'):
                    proxy['servername'] = data.get('host')
                
                if data.get('alpn'):
                    proxy['alpn'] = data.get('alpn').split(',')
            
            return proxy
        except Exception as e:
            self._add_log(f"解析VMess节点失败: {str(e)}", "warning")
            return None
    
    def _parse_vless_to_clash(self, vless_url: str, default_name: str, name_count: dict) -> Optional[Dict[str, Any]]:
        """解析VLess节点"""
        try:
            import urllib.parse
            url_parts = urllib.parse.urlparse(vless_url)
            server = url_parts.hostname
            port = url_parts.port
            uuid = url_parts.username
            
            query_params = urllib.parse.parse_qs(url_parts.query)
            
            name = default_name
            if url_parts.fragment:
                name = urllib.parse.unquote(url_parts.fragment)
            
            # 如果不重命名（name_count为空），直接使用原始名称
            if not name_count:
                final_name = name
            else:
                final_name = self._get_unique_name(name, name_count)
            
            proxy = {
                'name': final_name,
                'type': 'vless',
                'server': server,
                'port': port,
                'uuid': uuid,
                'udp': True
            }
            
            # 处理加密
            encryption = query_params.get('encryption', ['none'])[0]
            if encryption != 'none':
                proxy['encryption'] = encryption
            
            # 处理安全传输
            security = query_params.get('security', ['none'])[0]
            if security == 'tls':
                proxy['tls'] = True
                sni = query_params.get('sni', [''])[0]
                if sni:
                    proxy['servername'] = sni
                alpn = query_params.get('alpn', [''])[0]
                if alpn:
                    proxy['alpn'] = alpn.split(',')
            elif security == 'reality':
                proxy['tls'] = True
                sni = query_params.get('sni', [''])[0]
                if sni:
                    proxy['servername'] = sni
                reality_opts = {}
                pbk = query_params.get('pbk', [''])[0]
                if pbk:
                    reality_opts['public-key'] = pbk
                sid = query_params.get('sid', [''])[0]
                if sid:
                    reality_opts['short-id'] = sid
                if reality_opts:
                    proxy['reality-opts'] = reality_opts
                proxy['client-fingerprint'] = 'chrome'
            
            # 处理传输协议
            network_type = query_params.get('type', ['tcp'])[0]
            proxy['network'] = network_type
            
            if network_type == 'ws':
                ws_opts = {}
                path = query_params.get('path', ['/'])[0]
                ws_opts['path'] = path
                host = query_params.get('host', [''])[0]
                if host:
                    ws_opts['headers'] = {'Host': host}
                proxy['ws-opts'] = ws_opts
            elif network_type == 'grpc':
                grpc_opts = {}
                service_name = query_params.get('serviceName', [''])[0]
                if service_name:
                    grpc_opts['grpc-service-name'] = service_name
                proxy['grpc-opts'] = grpc_opts
            
            # 处理flow
            flow = query_params.get('flow', [''])[0]
            if flow:
                proxy['flow'] = flow
            
            return proxy
        except Exception as e:
            self._add_log(f"解析VLess节点失败: {str(e)}", "warning")
            return None
    
    def _parse_ss_to_clash(self, ss_url: str, default_name: str, name_count: dict, use_filter: bool = True) -> Optional[Dict[str, Any]]:
        """解析SS节点"""
        try:
            import urllib.parse
            import re
            
            url_parts = urllib.parse.urlparse(ss_url)
            name = default_name
            if url_parts.fragment:
                name = urllib.parse.unquote(url_parts.fragment)
            
            # 如果不重命名（name_count为空），直接使用原始名称
            if not name_count:
                final_name = name
            else:
                final_name = self._get_unique_name(name, name_count)
            
            # 方法1: 尝试解析标准SS格式 ss://base64@server:port
            m = re.match(r'ss://([A-Za-z0-9+/=%]+)@([^:]+):(\d+)', ss_url)
            if m:
                userinfo, server, port = m.groups()
                try:
                    userinfo = urllib.parse.unquote(userinfo)
                    userinfo += '=' * (-len(userinfo) % 4)
                    method_pass = base64.b64decode(userinfo).decode('utf-8')
                    method, password = method_pass.split(':', 1)
                    
                    return {
                        'name': final_name,
                        'type': 'ss',
                        'server': server,
                        'port': int(port),
                        'cipher': method,
                        'password': password,
                        'udp': True
                    }
                except Exception as e:
                    # 如果标准格式失败，尝试其他方法
                    pass
            
            # 方法2: 尝试解析完整Base64格式 ss://base64#name
            if ss_url.startswith('ss://') and '@' not in ss_url:
                try:
                    b64_part = ss_url[5:]  # 去掉 'ss://'
                    if '#' in b64_part:
                        b64_part = b64_part.split('#')[0]
                    
                    b64_part += '=' * (-len(b64_part) % 4)
                    decoded = base64.b64decode(b64_part).decode('utf-8')
                    
                    # 解析格式: method:password@server:port
                    if '@' in decoded and ':' in decoded:
                        userinfo, serverinfo = decoded.split('@', 1)
                        if ':' in userinfo and ':' in serverinfo:
                            method, password = userinfo.split(':', 1)
                            server, port = serverinfo.split(':', 1)
                            
                            return {
                                'name': final_name,
                                'type': 'ss',
                                'server': server,
                                'port': int(port),
                                'cipher': method,
                                'password': password,
                                'udp': True
                            }
                except Exception as e:
                    pass
            
            # 方法3: 尝试从URL参数解析
            if url_parts.hostname and url_parts.port:
                query_params = urllib.parse.parse_qs(url_parts.query)
                if 'password' in query_params and 'method' in query_params:
                    return {
                        'name': final_name,
                        'type': 'ss',
                        'server': url_parts.hostname,
                        'port': url_parts.port,
                        'cipher': query_params['method'][0],
                        'password': query_params['password'][0],
                        'udp': True
                    }
            
            return None
        except Exception as e:
            self._add_log(f"解析SS节点失败: {str(e)}", "warning")
            return None
    
    def _parse_ssr_to_clash(self, ssr_url: str, default_name: str, name_count: dict) -> Optional[Dict[str, Any]]:
        """解析SSR节点"""
        try:
            import urllib.parse
            
            # 移除 ssr:// 前缀
            b64 = ssr_url[6:]
            # 补齐base64填充
            b64 += '=' * (-len(b64) % 4)
            
            # 解码base64
            raw = base64.b64decode(b64).decode('utf-8')
            
            # 分割URL部分和参数部分
            if '?' in raw:
                url_part, params_str = raw.split('?', 1)
            else:
                url_part = raw
                params_str = ''
            
            # 解析URL部分
            parts = url_part.split(':')
            if len(parts) < 6:
                return None
            
            server = parts[0]
            port = int(parts[1])
            protocol = parts[2]
            method = parts[3]
            obfs = parts[4]
            password_b64 = parts[5]
            
            # 解码密码
            try:
                # 处理URL安全的base64编码，移除末尾的斜杠
                password_b64 = password_b64.rstrip('/')
                password_b64 = password_b64.replace('-', '+').replace('_', '/')
                # 补齐填充
                password_b64 += '=' * (-len(password_b64) % 4)
                password = base64.b64decode(password_b64).decode('utf-8')
            except Exception as e:
                # 如果base64解码失败，尝试直接使用原始值
                password = password_b64
            
            # 解析参数
            params = urllib.parse.parse_qs(params_str) if params_str else {}
            
            # 获取节点名称
            name = default_name
            if 'remarks' in params:
                try:
                    remarks_b64 = params['remarks'][0].replace('-', '+').replace('_', '/')
                    remarks_b64 += '=' * (-len(remarks_b64) % 4)
                    name = base64.b64decode(remarks_b64).decode('utf-8')
                    name = urllib.parse.unquote(name)
                except:
                    pass
            
            # 获取协议参数和混淆参数
            protocol_param = ''
            obfs_param = ''
            
            if 'protoparam' in params:
                try:
                    protoparam_b64 = params['protoparam'][0].replace('-', '+').replace('_', '/')
                    protoparam_b64 += '=' * (-len(protoparam_b64) % 4)
                    protocol_param = base64.b64decode(protoparam_b64).decode('utf-8')
                except:
                    protocol_param = params['protoparam'][0]
            
            if 'obfsparam' in params:
                try:
                    obfsparam_b64 = params['obfsparam'][0].replace('-', '+').replace('_', '/')
                    obfsparam_b64 += '=' * (-len(obfsparam_b64) % 4)
                    obfs_param = base64.b64decode(obfsparam_b64).decode('utf-8')
                except:
                    obfs_param = params['obfsparam'][0]
            
            # 如果不重命名（name_count为空），直接使用原始名称
            if not name_count:
                final_name = name
            else:
                final_name = self._get_unique_name(name, name_count)
            
            return {
                'name': final_name,
                'type': 'ssr',
                'server': server,
                'port': port,
                'cipher': method,
                'password': password,
                'protocol': protocol,
                'protocol-param': protocol_param,
                'obfs': obfs,
                'obfs-param': obfs_param,
                'udp': True
            }
        except Exception as e:
            self._add_log(f"解析SSR节点失败: {str(e)}", "warning")
            return None
    
    def _parse_trojan_to_clash(self, trojan_url: str, default_name: str, name_count: dict) -> Optional[Dict[str, Any]]:
        """解析Trojan节点"""
        try:
            import urllib.parse
            
            # 方法1: 尝试标准URL解析
            try:
                url_parts = urllib.parse.urlparse(trojan_url)
                server = url_parts.hostname
                port = url_parts.port
                password = url_parts.username
                
                if not server or not port or not password:
                    raise ValueError("缺少必要参数")
                
                query_params = urllib.parse.parse_qs(url_parts.query)
                
                name = default_name
                if url_parts.fragment:
                    name = urllib.parse.unquote(url_parts.fragment)
                
                # 如果不重命名（name_count为空），直接使用原始名称
                if not name_count:
                    final_name = name
                else:
                    final_name = self._get_unique_name(name, name_count)
                
                proxy = {
                    'name': final_name,
                    'type': 'trojan',
                    'server': server,
                    'port': port,
                    'password': password,
                    'udp': True,
                    'tls': True
                }
                
                # 处理SNI
                sni = query_params.get('sni', [''])[0]
                if sni:
                    proxy['sni'] = sni
                
                # 处理跳过证书验证
                allow_insecure = query_params.get('allowInsecure', [''])[0]
                if allow_insecure == '1' or allow_insecure.lower() == 'true':
                    proxy['skip-cert-verify'] = True
                
                # 处理传输协议
                network_type = query_params.get('type', ['tcp'])[0]
                if network_type == 'ws':
                    proxy['network'] = 'ws'
                    ws_opts = {}
                    path = query_params.get('path', ['/'])[0]
                    ws_opts['path'] = path
                    host = query_params.get('host', [''])[0]
                    if host:
                        ws_opts['headers'] = {'Host': host}
                    proxy['ws-opts'] = ws_opts
                
                return proxy
                
            except Exception as e:
                # 方法2: 尝试Base64解码格式
                if trojan_url.startswith('trojan://'):
                    try:
                        b64_part = trojan_url[9:]  # 去掉 'trojan://'
                        if '#' in b64_part:
                            b64_part = b64_part.split('#')[0]
                        
                        b64_part += '=' * (-len(b64_part) % 4)
                        decoded = base64.b64decode(b64_part).decode('utf-8')
                        
                        # 解析格式: password@server:port?params
                        if '@' in decoded:
                            password, server_part = decoded.split('@', 1)
                            if ':' in server_part:
                                server, port_part = server_part.split(':', 1)
                                if '?' in port_part:
                                    port, params = port_part.split('?', 1)
                                else:
                                    port = port_part
                                    params = ''
                                
                                name = default_name
                                if '#' in trojan_url:
                                    name = urllib.parse.unquote(trojan_url.split('#')[1])
                                
                                if not name_count:
                                    final_name = name
                                else:
                                    final_name = self._get_unique_name(name, name_count)
                                
                                proxy = {
                                    'name': final_name,
                                    'type': 'trojan',
                                    'server': server,
                                    'port': int(port),
                                    'password': password,
                                    'udp': True,
                                    'tls': True
                                }
                                
                                # 解析查询参数
                                if params:
                                    query_params = urllib.parse.parse_qs(params)
                                    sni = query_params.get('sni', [''])[0]
                                    if sni:
                                        proxy['sni'] = sni
                                    
                                    allow_insecure = query_params.get('allowInsecure', [''])[0]
                                    if allow_insecure == '1' or allow_insecure.lower() == 'true':
                                        proxy['skip-cert-verify'] = True
                                
                                return proxy
                    except Exception as e2:
                        pass
            
            return None
        except Exception as e:
            self._add_log(f"解析Trojan节点失败: {str(e)}", "warning")
            return None
    
    def _parse_hysteria2_to_clash(self, hy2_url: str, default_name: str, name_count: dict) -> Optional[Dict[str, Any]]:
        """解析Hysteria2节点"""
        try:
            import urllib.parse
            url_parts = urllib.parse.urlparse(hy2_url)
            server = url_parts.hostname
            port = url_parts.port
            password = url_parts.username
            
            query_params = urllib.parse.parse_qs(url_parts.query)
            
            name = default_name
            if url_parts.fragment:
                name = urllib.parse.unquote(url_parts.fragment)
            
            # 如果不重命名（name_count为空），直接使用原始名称
            if not name_count:
                final_name = name
            else:
                final_name = self._get_unique_name(name, name_count)
            
            proxy = {
                'name': final_name,
                'type': 'hysteria2',
                'server': server,
                'port': port,
                'password': password,
                'udp': True
            }
            
            # 处理SNI
            sni = query_params.get('sni', [''])[0]
            if sni:
                proxy['sni'] = sni
            
            # 处理insecure
            insecure = query_params.get('insecure', [''])[0]
            if insecure == '1' or insecure.lower() == 'true':
                proxy['skip-cert-verify'] = True
            
            # 处理带宽
            up_mbps = query_params.get('upmbps', [''])[0]
            if up_mbps:
                try:
                    proxy['up-mbps'] = int(up_mbps)
                except ValueError:
                    pass
            
            down_mbps = query_params.get('downmbps', [''])[0]
            if down_mbps:
                try:
                    proxy['down-mbps'] = int(down_mbps)
                except ValueError:
                    pass
            
            return proxy
        except Exception as e:
            self._add_log(f"解析Hysteria2节点失败: {str(e)}", "warning")
            return None
    
    def _parse_tuic_to_clash(self, tuic_url: str, default_name: str, name_count: dict) -> Optional[Dict[str, Any]]:
        """解析TUIC节点"""
        try:
            import urllib.parse
            url_parts = urllib.parse.urlparse(tuic_url)
            server = url_parts.hostname
            port = url_parts.port
            uuid = url_parts.username
            password = url_parts.password
            
            name = default_name
            if url_parts.fragment:
                name = urllib.parse.unquote(url_parts.fragment)
            
            # 如果不重命名（name_count为空），直接使用原始名称
            if not name_count:
                final_name = name
            else:
                final_name = self._get_unique_name(name, name_count)
            
            return {
                'name': final_name,
                'type': 'tuic',
                'server': server,
                'port': port,
                'uuid': uuid,
                'password': password,
                'udp': True
            }
        except Exception as e:
            self._add_log(f"解析TUIC节点失败: {str(e)}", "warning")
            return None
    
    def _generate_clash_from_template(self, proxies: List[Dict[str, Any]], proxy_names: List[str]) -> str:
        """使用模板生成Clash配置"""
        try:
            # 读取模板文件
            template_file = "/Users/apple/Downloads/xboard 2/app/services/cash.yaml"
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # 生成proxies部分的YAML
            proxies_yaml = yaml.dump({'proxies': proxies}, allow_unicode=True, sort_keys=False, indent=2)
            
            # 替换模板中的proxies部分
            import re
            
            # 找到proxies部分并替换
            proxies_pattern = r'proxies:\s*\n(?:  - .*\n)*'
            new_proxies_section = 'proxies:\n' + proxies_yaml[9:]  # 去掉开头的'proxies:\n'
            
            # 替换proxies部分
            updated_content = re.sub(proxies_pattern, new_proxies_section, template_content)
            
            # 更新代理组中的节点列表
            # 找到所有代理组并更新其中的节点列表
            proxy_groups_pattern = r'(\s+- name: [^\n]+\n\s+type: [^\n]+\n(?:\s+[^\n]+\n)*\s+proxies:\n)((?:\s+- [^\n]+\n)*)'
            
            def replace_proxy_group(match):
                group_header = match.group(1)
                old_proxies = match.group(2)
                
                # 检查是否是自动选择组
                if '自动选择' in group_header:
                    # 自动选择组包含所有节点
                    new_proxies = '\n'.join([f'      - {name}' for name in proxy_names])
                    return group_header + new_proxies + '\n'
                elif '节点选择' in group_header:
                    # 节点选择组包含自动选择和所有节点
                    new_proxies = '      - ♻️ 自动选择\n      - DIRECT\n' + '\n'.join([f'      - {name}' for name in proxy_names])
                    return group_header + new_proxies + '\n'
                elif '漏网之鱼' in group_header:
                    # 漏网之鱼组包含节点选择和自动选择
                    new_proxies = '      - 🚀 节点选择\n      - 🎯 全球直连\n      - ♻️ 自动选择\n' + '\n'.join([f'      - {name}' for name in proxy_names])
                    return group_header + new_proxies + '\n'
                else:
                    # 其他组保持原样
                    return match.group(0)
            
            updated_content = re.sub(proxy_groups_pattern, replace_proxy_group, updated_content, flags=re.MULTILINE)
            
            return updated_content
            
        except Exception as e:
            self._add_log(f"使用模板生成Clash配置失败: {str(e)}", "error")
            # 如果模板生成失败，使用基本配置
            return self._create_basic_clash_config_fallback(proxies, proxy_names)
    
    def _create_basic_clash_config_fallback(self, proxies: List[Dict[str, Any]], proxy_names: List[str]) -> str:
        """创建基本的Clash配置（备用方案）"""
        config = {
            "port": 7890,
            "socks-port": 7891,
            "allow-lan": True,
            "mode": "Rule",
            "log-level": "info",
            "external-controller": ":9090",
            "dns": {
                "enable": True,
                "nameserver": ["119.29.29.29", "223.5.5.5"],
                "fallback": ["8.8.8.8", "8.8.4.4"]
            },
            "proxies": proxies,
            "proxy-groups": [
                {
                    "name": "🚀 节点选择",
                    "type": "select",
                    "proxies": ["♻️ 自动选择", "DIRECT"] + proxy_names
                },
                {
                    "name": "♻️ 自动选择",
                    "type": "url-test",
                    "url": "http://www.gstatic.com/generate_204",
                    "interval": 300,
                    "tolerance": 50,
                    "proxies": proxy_names
                },
                {
                    "name": "🎯 全球直连",
                    "type": "select",
                    "proxies": ["DIRECT", "🚀 节点选择", "♻️ 自动选择"]
                },
                {
                    "name": "🛑 全球拦截",
                    "type": "select",
                    "proxies": ["REJECT", "DIRECT"]
                },
                {
                    "name": "🐟 漏网之鱼",
                    "type": "select",
                    "proxies": ["🚀 节点选择", "🎯 全球直连", "♻️ 自动选择"] + proxy_names
                }
            ],
            "rules": [
                "DOMAIN-SUFFIX,{domain},🎯 全球直连",
                "IP-CIDR,127.0.0.0/8,🎯 全球直连,no-resolve",
                "IP-CIDR,172.16.0.0/12,🎯 全球直连,no-resolve",
                "IP-CIDR,192.168.0.0/16,🎯 全球直连,no-resolve",
                "GEOIP,CN,🎯 全球直连",
                "MATCH,🐟 漏网之鱼"
            ]
        }
        
        return yaml.dump(config, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    
    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取日志"""
        try:
            # 优先从内存中获取日志（实时性更好）
            if self.logs:
                return self.logs[-limit:] if len(self.logs) > limit else self.logs
            
            # 如果内存中没有日志，从数据库获取
            if self.db is not None:
                logs_record = self.db.query(SystemConfig).filter(SystemConfig.key == "config_update_logs").first()
                if logs_record:
                    logs_data = json.loads(logs_record.value)
                    return logs_data[-limit:] if logs_data else []
            
            return []
        except Exception as e:
            logger.error(f"获取日志失败: {str(e)}")
            # 如果出错，至少返回内存中的日志
            return self.logs[-limit:] if self.logs else []
    
    def _add_log(self, message: str, level: str = "info"):
        """添加日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        
        # 先保存到内存中（用于实时显示）
        self.logs.append(log_entry)
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        try:
            # 检查数据库连接是否有效
            if self.db is None:
                logger.warning("数据库连接无效，仅保存到内存")
                return
                
            # 从数据库获取现有日志
            logs_record = self.db.query(SystemConfig).filter(SystemConfig.key == "config_update_logs").first()
            if logs_record:
                logs_data = json.loads(logs_record.value)
            else:
                logs_data = []
            
            # 添加新日志
            logs_data.append(log_entry)
            
            # 限制日志数量
            if len(logs_data) > self.max_logs:
                logs_data = logs_data[-self.max_logs:]
            
            # 保存到数据库
            if logs_record:
                logs_record.value = json.dumps(logs_data)
            else:
                logs_record = SystemConfig(
                    key="config_update_logs",
                    value=json.dumps(logs_data),
                    type="json",
                    category="general",
                    display_name="配置更新日志",
                    description="配置更新操作日志"
                )
                self.db.add(logs_record)
            
            self.db.commit()
            logger.info(f"日志已保存到数据库: {message}")
                
        except Exception as e:
            logger.error(f"保存日志到数据库失败: {str(e)}")
            # 如果数据库保存失败，至少已经保存到内存中了
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        try:
            # 从数据库获取配置
            config_record = self.db.query(SystemConfig).filter(SystemConfig.key == "config_update").first()
            if config_record:
                return json.loads(config_record.value)
            else:
                # 返回默认配置
                return self.default_config.copy()
        except Exception as e:
            logger.error(f"获取配置失败: {str(e)}")
            return self.default_config.copy()
    
    def get_node_sources(self) -> List[str]:
        """获取节点源URL列表"""
        try:
            config = self.get_config()
            return config.get("urls", [])
        except Exception as e:
            self._add_log(f"获取节点源配置失败: {str(e)}", "error")
            return []
    
    def update_node_sources(self, sources_data: dict) -> None:
        """更新节点源URL列表"""
        try:
            urls = sources_data.get("urls", [])
            if not isinstance(urls, list):
                raise ValueError("节点源URL必须是列表格式")
            
            # 验证URL格式
            for url in urls:
                if not url.startswith(('http://', 'https://')):
                    raise ValueError(f"无效的URL格式: {url}")
            
            # 更新配置
            config = self.get_config()
            config["urls"] = urls
            self.update_config(config)
            
            self._add_log(f"节点源配置已更新，共 {len(urls)} 个源", "info")
        except Exception as e:
            self._add_log(f"更新节点源配置失败: {str(e)}", "error")
            raise
    
    def get_filter_keywords(self) -> List[str]:
        """获取过滤关键词列表"""
        try:
            config = self.get_config()
            return config.get("filter_keywords", [])
        except Exception as e:
            self._add_log(f"获取过滤关键词配置失败: {str(e)}", "error")
            return []
    
    def update_filter_keywords(self, keywords_data: dict) -> None:
        """更新过滤关键词列表"""
        try:
            keywords = keywords_data.get("keywords", [])
            if not isinstance(keywords, list):
                raise ValueError("过滤关键词必须是列表格式")
            
            # 更新配置
            config = self.get_config()
            config["filter_keywords"] = keywords
            self.update_config(config)
            
            self._add_log(f"过滤关键词配置已更新，共 {len(keywords)} 个关键词", "info")
        except Exception as e:
            self._add_log(f"更新过滤关键词配置失败: {str(e)}", "error")
            raise
    
    def update_config(self, config_data: Dict[str, Any]):
        """更新配置"""
        try:
            # 验证配置
            validated_config = self._validate_config(config_data)
            
            # 保存到数据库
            config_record = self.db.query(SystemConfig).filter(SystemConfig.key == "config_update").first()
            if config_record:
                config_record.value = json.dumps(validated_config)
            else:
                config_record = SystemConfig(
                    key="config_update",
                    value=json.dumps(validated_config),
                    type="json",
                    category="general",
                    display_name="配置更新设置",
                    description="配置更新设置"
                )
                self.db.add(config_record)
            
            self.db.commit()
            self._add_log("配置已更新", "success")
        except Exception as e:
            self.db.rollback()
            self._add_log(f"更新配置失败: {str(e)}", "error")
            raise
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置"""
        validated = self.default_config.copy()
        
        if "urls" in config and isinstance(config["urls"], list):
            validated["urls"] = config["urls"]
        
        if "target_dir" in config and isinstance(config["target_dir"], str):
            validated["target_dir"] = config["target_dir"]
        
        if "v2ray_file" in config and isinstance(config["v2ray_file"], str):
            validated["v2ray_file"] = config["v2ray_file"]
        
        if "clash_file" in config and isinstance(config["clash_file"], str):
            validated["clash_file"] = config["clash_file"]
        
        if "update_interval" in config and isinstance(config["update_interval"], int):
            validated["update_interval"] = max(300, config["update_interval"])  # 最少5分钟
        
        if "enable_schedule" in config and isinstance(config["enable_schedule"], bool):
            validated["enable_schedule"] = config["enable_schedule"]
        
        if "filter_keywords" in config and isinstance(config["filter_keywords"], list):
            validated["filter_keywords"] = config["filter_keywords"]
        
        return validated
    
    def get_generated_files(self) -> Dict[str, Any]:
        """获取生成的文件信息"""
        try:
            config = self.get_config()
            target_dir = config.get("target_dir", "./uploads/config")
            v2ray_file = os.path.join(target_dir, config.get("v2ray_file", "xr"))
            clash_file = os.path.join(target_dir, config.get("clash_file", "clash.yaml"))
            
            files_info = {}
            
            if os.path.exists(v2ray_file):
                stat = os.stat(v2ray_file)
                files_info["v2ray"] = {
                    "path": v2ray_file,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "exists": True
                }
            else:
                files_info["v2ray"] = {"exists": False}
            
            if os.path.exists(clash_file):
                stat = os.stat(clash_file)
                files_info["clash"] = {
                    "path": clash_file,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "exists": True
                }
            else:
                files_info["clash"] = {"exists": False}
            
            return files_info
        except Exception as e:
            logger.error(f"获取文件信息失败: {str(e)}")
            return {}
    
    def _check_config_files_exist(self) -> bool:
        """检查配置文件是否存在"""
        try:
            config = self.get_config()
            target_dir = config.get("target_dir", "./uploads/config")
            v2ray_file = os.path.join(target_dir, config.get("v2ray_file", "xr"))
            clash_file = os.path.join(target_dir, config.get("clash_file", "clash.yaml"))
            
            return os.path.exists(v2ray_file) and os.path.exists(clash_file)
        except:
            return False
    
    def _get_last_update_time(self) -> Optional[str]:
        """获取最后更新时间"""
        try:
            config_record = self.db.query(SystemConfig).filter(SystemConfig.key == "config_update_last_time").first()
            if config_record:
                return config_record.value
            return None
        except:
            return None
    
    def _update_last_update_time(self):
        """更新最后更新时间"""
        try:
            current_time = datetime.now().isoformat()
            config_record = self.db.query(SystemConfig).filter(SystemConfig.key == "config_update_last_time").first()
            if config_record:
                config_record.value = current_time
            else:
                config_record = SystemConfig(
                    key="config_update_last_time",
                    value=current_time,
                    type="string",
                    category="general",
                    display_name="配置更新最后时间",
                    description="配置更新最后时间"
                )
                self.db.add(config_record)
            self.db.commit()
        except Exception as e:
            logger.error(f"更新最后更新时间失败: {str(e)}")
    
    def _get_next_update_time(self) -> Optional[str]:
        """获取下次更新时间"""
        try:
            config = self.get_config()
            if not config.get("enable_schedule", False):
                return None
            
            last_update = self._get_last_update_time()
            if not last_update:
                return None
            
            last_time = datetime.fromisoformat(last_update)
            interval = config.get("update_interval", 3600)
            next_time = last_time + timedelta(seconds=interval)
            
            return next_time.isoformat()
        except:
            return None
    
    def get_schedule_config(self) -> Dict[str, Any]:
        """获取定时任务配置"""
        return self.get_config()
    
    def update_schedule_config(self, schedule_data: Dict[str, Any]):
        """更新定时任务配置"""
        self.update_config(schedule_data)
    
    def start_scheduled_task(self):
        """启动定时任务"""
        try:
            config = self.get_config()
            if not config.get("enable_schedule", False):
                self._add_log("定时任务未启用", "warning")
                return
            
            if self.scheduled_task is not None:
                self._add_log("定时任务已在运行", "warning")
                return
            
            interval = config.get("update_interval", 3600)
            self.scheduled_task = threading.Timer(interval, self._scheduled_update)
            self.scheduled_task.start()
            
            self._add_log(f"定时任务已启动，间隔 {interval} 秒", "success")
        except Exception as e:
            self._add_log(f"启动定时任务失败: {str(e)}", "error")
            raise
    
    def stop_scheduled_task(self):
        """停止定时任务"""
        try:
            if self.scheduled_task is not None:
                self.scheduled_task.cancel()
                self.scheduled_task = None
                self._add_log("定时任务已停止", "success")
            else:
                self._add_log("定时任务未在运行", "warning")
        except Exception as e:
            self._add_log(f"停止定时任务失败: {str(e)}", "error")
            raise
    
    def _scheduled_update(self):
        """定时更新任务"""
        try:
            if not self.is_running_flag:
                self.run_update_task()
            
            # 重新启动定时器
            config = self.get_config()
            if config.get("enable_schedule", False):
                interval = config.get("update_interval", 3600)
                self.scheduled_task = threading.Timer(interval, self._scheduled_update)
                self.scheduled_task.start()
        except Exception as e:
            self._add_log(f"定时更新失败: {str(e)}", "error")
            logger.error(f"定时更新失败: {str(e)}", exc_info=True)
    
    def _save_clash_config_to_db(self, config_content: str):
        """保存clash配置到数据库（只覆盖有效配置）"""
        try:
            from sqlalchemy import text
            from datetime import datetime
            
            current_time = datetime.now()
            
            # 检查是否存在有效配置（不是失效配置）
            check_query = text('SELECT id FROM system_configs WHERE key = \'clash_config\' AND type = \'clash\'')
            existing = self.db.execute(check_query).first()
            
            if existing:
                # 更新现有有效配置
                update_query = text("""
                    UPDATE system_configs 
                    SET value = :value, updated_at = :updated_at
                    WHERE key = 'clash_config' AND type = 'clash'
                """)
                self.db.execute(update_query, {
                    "value": config_content,
                    "updated_at": current_time
                })
                self._add_log("Clash有效配置已更新", "success")
            else:
                # 插入新的有效配置
                insert_query = text("""
                    INSERT INTO system_configs ("key", value, type, category, display_name, description, is_public, sort_order, created_at, updated_at)
                    VALUES ('clash_config', :value, 'clash', 'proxy', 'Clash有效配置', 'Clash代理有效配置文件', 0, 1, :created_at, :updated_at)
                """)
                self.db.execute(insert_query, {
                    "value": config_content,
                    "created_at": current_time,
                    "updated_at": current_time
                })
                self._add_log("Clash有效配置已创建", "success")
            
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self._add_log(f"保存Clash有效配置到数据库失败: {str(e)}", "error")
            raise
    
    def _save_v2ray_config_to_db(self, config_content: str):
        """保存v2ray配置到数据库（只覆盖有效配置）"""
        try:
            from sqlalchemy import text
            from datetime import datetime
            
            current_time = datetime.now()
            
            # 检查是否存在有效配置（不是失效配置）
            check_query = text('SELECT id FROM system_configs WHERE key = \'v2ray_config\' AND type = \'v2ray\'')
            existing = self.db.execute(check_query).first()
            
            if existing:
                # 更新现有有效配置
                update_query = text("""
                    UPDATE system_configs 
                    SET value = :value, updated_at = :updated_at
                    WHERE key = 'v2ray_config' AND type = 'v2ray'
                """)
                self.db.execute(update_query, {
                    "value": config_content,
                    "updated_at": current_time
                })
                self._add_log("V2Ray有效配置已更新", "success")
            else:
                # 插入新的有效配置
                insert_query = text("""
                    INSERT INTO system_configs ("key", value, type, category, display_name, description, is_public, sort_order, created_at, updated_at)
                    VALUES ('v2ray_config', :value, 'v2ray', 'proxy', 'V2Ray有效配置', 'V2Ray代理有效配置文件', 0, 2, :created_at, :updated_at)
                """)
                self.db.execute(insert_query, {
                    "value": config_content,
                    "created_at": current_time,
                    "updated_at": current_time
                })
                self._add_log("V2Ray有效配置已创建", "success")
            
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self._add_log(f"保存V2Ray有效配置到数据库失败: {str(e)}", "error")
            raise
    
    def _parse_node_legacy(self, node_url: str, name_count: dict, filter_keywords: List[str] = None) -> Optional[Dict[str, Any]]:
        """按照老代码逻辑解析节点"""
        try:
            if node_url.startswith('vmess://'):
                return self._decode_vmess_legacy(node_url, name_count, filter_keywords)
            elif node_url.startswith('ss://'):
                return self._decode_ss_legacy(node_url, name_count, filter_keywords)
            elif node_url.startswith('trojan://'):
                return self._decode_trojan_legacy(node_url, name_count, filter_keywords)
            elif node_url.startswith('vless://'):
                if 'reality' in node_url.lower() or 'pbk=' in node_url:
                    return self._decode_vless_reality_legacy(node_url, name_count, filter_keywords)
                else:
                    return self._decode_vless_legacy(node_url, name_count, filter_keywords)
            elif node_url.startswith('ssr://'):
                return self._decode_ssr_legacy(node_url, name_count, filter_keywords)
            elif node_url.startswith('hysteria2://') or node_url.startswith('hy2://'):
                return self._decode_hysteria2_legacy(node_url, name_count, filter_keywords)
            elif node_url.startswith('tuic://'):
                return self._decode_tuic_legacy(node_url, name_count, filter_keywords)
            else:
                return None
        except Exception as e:
            self._add_log(f"解析节点失败: {str(e)}", "warning")
            return None
    
    def _parse_node_without_rename(self, node_url: str) -> Optional[Dict[str, Any]]:
        """解析节点但不进行重命名（用于第一个源的节点，完全保持原始状态）"""
        try:
            if node_url.startswith('vmess://'):
                return self._parse_vmess_raw(node_url)
            elif node_url.startswith('ss://'):
                return self._parse_ss_raw(node_url)
            elif node_url.startswith('trojan://'):
                return self._parse_trojan_raw(node_url)
            elif node_url.startswith('vless://'):
                return self._parse_vless_raw(node_url)
            elif node_url.startswith('ssr://'):
                return self._parse_ssr_raw(node_url)
            elif node_url.startswith('hysteria2://') or node_url.startswith('hy2://'):
                return self._parse_hysteria2_raw(node_url)
            elif node_url.startswith('tuic://'):
                return self._parse_tuic_raw(node_url)
            else:
                # 尝试智能检测节点类型
                return self._smart_parse_node(node_url)
        except Exception as e:
            # 不记录错误日志，因为第一个源的节点解析失败是正常的
            return None
    
    def _smart_parse_node(self, node_url: str) -> Optional[Dict[str, Any]]:
        """智能解析节点，自动检测类型"""
        try:
            # 如果URL包含Base64编码，尝试解码检测
            if '://' in node_url:
                protocol, content = node_url.split('://', 1)
                
                # 尝试Base64解码
                try:
                    if '#' in content:
                        b64_part = content.split('#')[0]
                    else:
                        b64_part = content
                    
                    b64_part += '=' * (-len(b64_part) % 4)
                    decoded = base64.b64decode(b64_part).decode('utf-8')
                    
                    # 检测VMess格式
                    if decoded.startswith('{') and '"add"' in decoded:
                        try:
                            data = json.loads(decoded)
                            if 'add' in data and 'port' in data and 'id' in data:
                                return self._parse_vmess_raw(node_url)
                        except:
                            pass
                    
                    # 检测SS格式
                    if ':' in decoded and '@' in decoded and not decoded.startswith('{'):
                        try:
                            parts = decoded.split('@')
                            if len(parts) == 2 and ':' in parts[0] and ':' in parts[1]:
                                return self._parse_ss_raw(node_url)
                        except:
                            pass
                    
                    # 检测Trojan格式
                    if '@' in decoded and ':' in decoded and not decoded.startswith('{'):
                        try:
                            password, server_part = decoded.split('@', 1)
                            if ':' in server_part:
                                return self._parse_trojan_raw(node_url)
                        except:
                            pass
                            
                except:
                    pass
            
            return None
        except Exception as e:
            return None
    
    def _parse_vmess_raw(self, vmess_url: str) -> Optional[Dict[str, Any]]:
        """解析VMess节点，完全保持原始状态（用于第一个源）"""
        try:
            import urllib.parse
            
            # 方法1: 尝试标准VMess解析
            try:
                b64 = vmess_url[8:]  # 去掉 'vmess://'
                b64 += '=' * (-len(b64) % 4)  # 补齐padding
                raw = base64.b64decode(b64).decode('utf-8')
                
                # 检查是否是SS格式的Base64编码（被错误标记为VMess）
                if ':' in raw and '@' in raw and not raw.startswith('{'):
                    # 这可能是SS格式的Base64编码
                    parts = raw.split('@')
                    if len(parts) == 2:
                        userinfo_part = parts[0]
                        server_part = parts[1]
                        
                        if ':' in userinfo_part and ':' in server_part:
                            method, password = userinfo_part.split(':', 1)
                            server, port = server_part.split(':', 1)
                            
                            # 构造SS节点
                            return {
                                'name': "SS节点",
                                'type': 'ss',
                                'server': server,
                                'port': int(port),
                                'cipher': method,
                                'password': password,
                            }
                
                # 尝试作为标准VMess解析
                data = json.loads(raw)
                
                name = data.get('ps', '')
                if name:
                    name = urllib.parse.unquote(name)
                    try:
                        name = json.loads(f'"{name}"')
                    except:
                        pass
                
                # 完全保持原始名称，不进行任何处理
                if not name or name.strip() == '' or name == 'vmess':
                    name = "VMess节点"
                
                proxy = {
                    'name': name,
                    'type': 'vmess',
                    'server': data.get('add'),
                    'port': int(data.get('port', 443)),
                    'uuid': data.get('id'),
                    'alterId': int(data.get('aid', 0)),
                    'cipher': data.get('scy', 'auto'),
                    'udp': True,
                    'tls': data.get('tls', '') == 'tls',
                }
                
                # 处理不同的网络类型
                network = data.get('net', 'tcp')
                if network == 'ws':
                    proxy['network'] = 'ws'
                    proxy['ws-opts'] = {
                        'path': data.get('path', '/'),
                        'headers': {
                            'Host': data.get('host', '')
                        } if data.get('host') else {}
                    }
                elif network == 'h2':
                    proxy['network'] = 'h2'
                    proxy['h2-opts'] = {
                        'path': data.get('path', '/'),
                        'host': [data.get('host', '')] if data.get('host') else []
                    }
                elif network == 'grpc':
                    proxy['network'] = 'grpc'
                    proxy['grpc-opts'] = {
                        'grpc-service-name': data.get('path', '')
                    }
                
                return proxy
                
            except Exception as e:
                # 方法2: 尝试其他VMess格式
                try:
                    # 检查是否是URL编码的VMess
                    if vmess_url.startswith('vmess://'):
                        # 尝试直接解析URL格式的VMess
                        url_parts = urllib.parse.urlparse(vmess_url)
                        if url_parts.hostname and url_parts.port:
                            query_params = urllib.parse.parse_qs(url_parts.query)
                            
                            name = "VMess节点"
                            if url_parts.fragment:
                                name = urllib.parse.unquote(url_parts.fragment)
                            
                            proxy = {
                                'name': name,
                                'type': 'vmess',
                                'server': url_parts.hostname,
                                'port': url_parts.port,
                                'uuid': url_parts.username or query_params.get('uuid', [''])[0],
                                'alterId': int(query_params.get('aid', ['0'])[0]),
                                'cipher': query_params.get('scy', ['auto'])[0],
                                'udp': True,
                                'tls': query_params.get('tls', [''])[0] == 'tls',
                            }
                            
                            # 处理网络类型
                            network = query_params.get('net', ['tcp'])[0]
                            if network == 'ws':
                                proxy['network'] = 'ws'
                                proxy['ws-opts'] = {
                                    'path': query_params.get('path', ['/'])[0],
                                    'headers': {
                                        'Host': query_params.get('host', [''])[0]
                                    } if query_params.get('host', [''])[0] else {}
                                }
                            
                            return proxy
                except Exception as e2:
                    pass
            
            return None
        except Exception as e:
            return None
    
    def _parse_ss_raw(self, ss_url: str) -> Optional[Dict[str, Any]]:
        """解析SS节点，完全保持原始状态（用于第一个源）"""
        try:
            import urllib.parse
            import re
            
            # 首先检查是否是VMess格式的Base64编码（被错误标记为SS）
            if ss_url.startswith('ss://') and len(ss_url) > 100:
                # 可能是VMess格式的Base64编码
                b64_part = ss_url[5:]  # 去掉 'ss://'
                try:
                    b64_part += '=' * (-len(b64_part) % 4)
                    raw = base64.b64decode(b64_part).decode('utf-8')
                    
                    # 检查是否是JSON格式（VMess）
                    if raw.startswith('{') and raw.endswith('}'):
                        data = json.loads(raw)
                        
                        # 构造VMess节点
                        name = data.get('ps', '')
                        if name:
                            name = urllib.parse.unquote(name)
                            try:
                                name = json.loads(f'"{name}"')
                            except:
                                pass
                        
                        if not name or name.strip() == '' or name == 'vmess':
                            name = "VMess节点"
                        
                        proxy = {
                            'name': name,
                            'type': 'vmess',
                            'server': data.get('add'),
                            'port': int(data.get('port', 443)),
                            'uuid': data.get('id'),
                            'alterId': int(data.get('aid', 0)),
                            'cipher': data.get('scy', 'auto'),
                            'udp': True,
                            'tls': data.get('tls', '') == 'tls',
                        }
                        
                        # 处理不同的网络类型
                        network = data.get('net', 'tcp')
                        if network == 'ws':
                            proxy['network'] = 'ws'
                            proxy['ws-opts'] = {
                                'path': data.get('path', '/'),
                                'headers': {
                                    'Host': data.get('host', '')
                                } if data.get('host') else {}
                            }
                        elif network == 'h2':
                            proxy['network'] = 'h2'
                            proxy['h2-opts'] = {
                                'path': data.get('path', '/'),
                                'host': [data.get('host', '')] if data.get('host') else []
                            }
                        elif network == 'grpc':
                            proxy['network'] = 'grpc'
                            proxy['grpc-opts'] = {
                                'grpc-service-name': data.get('path', '')
                            }
                        
                        return proxy
                except:
                    pass  # 不是VMess格式，继续SS解析
            
            # 方法1: 尝试标准SS格式 ss://base64@server:port
            m = re.match(r'ss://([A-Za-z0-9+/=%]+)@([^:]+):(\d+)', ss_url)
            if m:
                userinfo, server, port = m.groups()
                try:
                    userinfo = urllib.parse.unquote(userinfo)
                    userinfo += '=' * (-len(userinfo) % 4)
                    method_pass = base64.b64decode(userinfo).decode('utf-8')
                    method, password = method_pass.split(':', 1)
                    
                    # 获取节点名称
                    name = "SS节点"
                    if '#' in ss_url:
                        name = urllib.parse.unquote(ss_url.split('#')[1])
                    
                    return {
                        'name': name,
                        'type': 'ss',
                        'server': server,
                        'port': int(port),
                        'cipher': method,
                        'password': password,
                    }
                except Exception as e:
                    # 如果标准格式失败，尝试其他方法
                    pass
            
            # 方法2: 尝试完整Base64格式 ss://base64#name
            if ss_url.startswith('ss://') and '@' not in ss_url:
                try:
                    b64_part = ss_url[5:]  # 去掉 'ss://'
                    if '#' in b64_part:
                        b64_part = b64_part.split('#')[0]
                    
                    b64_part += '=' * (-len(b64_part) % 4)
                    decoded = base64.b64decode(b64_part).decode('utf-8')
                    
                    # 解析格式: method:password@server:port
                    if '@' in decoded and ':' in decoded:
                        userinfo, serverinfo = decoded.split('@', 1)
                        if ':' in userinfo and ':' in serverinfo:
                            method, password = userinfo.split(':', 1)
                            server, port = serverinfo.split(':', 1)
                            
                            # 获取节点名称
                            name = "SS节点"
                            if '#' in ss_url:
                                name = urllib.parse.unquote(ss_url.split('#')[1])
                            
                            return {
                                'name': name,
                                'type': 'ss',
                                'server': server,
                                'port': int(port),
                                'cipher': method,
                                'password': password,
                            }
                except Exception as e:
                    pass
            
            # 方法3: 尝试从URL参数解析
            try:
                url_parts = urllib.parse.urlparse(ss_url)
                if url_parts.hostname and url_parts.port:
                    query_params = urllib.parse.parse_qs(url_parts.query)
                    if 'password' in query_params and 'method' in query_params:
                        name = "SS节点"
                        if url_parts.fragment:
                            name = urllib.parse.unquote(url_parts.fragment)
                        
                        return {
                            'name': name,
                            'type': 'ss',
                            'server': url_parts.hostname,
                            'port': url_parts.port,
                            'cipher': query_params['method'][0],
                            'password': query_params['password'][0],
                        }
            except Exception as e:
                pass
            
            # 方法4: 尝试更宽松的正则表达式
            m = re.match(r'^ss://([^@]+)@([^:]+):(\d+)(?:[?][^#]*)?(?:#(.+))?$', ss_url)
            if m:
                userinfo, server, port, name = m.groups()
                try:
                    userinfo = urllib.parse.unquote(userinfo)
                    
                    # 检查是否是UUID格式（特殊的SS格式）
                    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                    if re.match(uuid_pattern, userinfo):
                        # 这是UUID格式，作为特殊的SS格式处理
                        cipher = 'none'  # 默认加密方法
                        
                        # 解析URL参数获取加密方法
                        if '?' in ss_url:
                            params_part = ss_url.split('?')[1].split('#')[0]
                            params = urllib.parse.parse_qs(params_part)
                            if 'encryption' in params:
                                cipher = params['encryption'][0]
                        
                        # 完全保持原始名称
                        if not name:
                            name = "SS节点"
                        else:
                            name = urllib.parse.unquote(name)
                        
                        return {
                            'name': name,
                            'type': 'ss',
                            'server': server,
                            'port': int(port),
                            'cipher': cipher,
                            'password': userinfo,  # UUID作为密码
                        }
                    
                    # 尝试Base64解码
                    userinfo += '=' * (-len(userinfo) % 4)
                    method_pass = base64.b64decode(userinfo).decode('utf-8')
                    method, password = method_pass.split(':', 1)
                    
                    # 完全保持原始名称
                    if not name:
                        name = "SS节点"
                    else:
                        name = urllib.parse.unquote(name)
                    
                    return {
                        'name': name,
                        'type': 'ss',
                        'server': server,
                        'port': int(port),
                        'cipher': method,
                        'password': password,
                    }
                except:
                    pass
            
            return None
        except Exception as e:
            return None
    
    def _parse_trojan_raw(self, trojan_url: str) -> Optional[Dict[str, Any]]:
        """解析Trojan节点，完全保持原始状态（用于第一个源）"""
        try:
            import urllib.parse
            
            # 方法1: 尝试标准URL解析
            try:
                url_parts = urllib.parse.urlparse(trojan_url)
                server = url_parts.hostname
                port = url_parts.port
                password = url_parts.username
                
                if not server or not port or not password:
                    raise ValueError("缺少必要参数")
                
                query_params = urllib.parse.parse_qs(url_parts.query)
                
                name = "Trojan节点"
                if url_parts.fragment:
                    name = urllib.parse.unquote(url_parts.fragment)
                
                proxy = {
                    'name': name,
                    'type': 'trojan',
                    'server': server,
                    'port': port,
                    'password': password,
                    'udp': True,
                    'tls': True
                }
                
                # 处理SNI
                sni = query_params.get('sni', [''])[0]
                if sni:
                    proxy['sni'] = sni
                
                # 处理跳过证书验证
                allow_insecure = query_params.get('allowInsecure', [''])[0]
                if allow_insecure == '1' or allow_insecure.lower() == 'true':
                    proxy['skip-cert-verify'] = True
                
                # 处理传输协议
                network_type = query_params.get('type', ['tcp'])[0]
                if network_type == 'ws':
                    proxy['network'] = 'ws'
                    ws_opts = {}
                    path = query_params.get('path', ['/'])[0]
                    ws_opts['path'] = path
                    host = query_params.get('host', [''])[0]
                    if host:
                        ws_opts['headers'] = {'Host': host}
                    proxy['ws-opts'] = ws_opts
                
                return proxy
                
            except Exception as e:
                # 方法2: 尝试Base64解码格式
                if trojan_url.startswith('trojan://'):
                    try:
                        b64_part = trojan_url[9:]  # 去掉 'trojan://'
                        if '#' in b64_part:
                            b64_part = b64_part.split('#')[0]
                        
                        b64_part += '=' * (-len(b64_part) % 4)
                        decoded = base64.b64decode(b64_part).decode('utf-8')
                        
                        # 解析格式: password@server:port?params
                        if '@' in decoded:
                            password, server_part = decoded.split('@', 1)
                            if ':' in server_part:
                                server, port_part = server_part.split(':', 1)
                                if '?' in port_part:
                                    port, params = port_part.split('?', 1)
                                else:
                                    port = port_part
                                    params = ''
                                
                                name = "Trojan节点"
                                if '#' in trojan_url:
                                    name = urllib.parse.unquote(trojan_url.split('#')[1])
                                
                                proxy = {
                                    'name': name,
                                    'type': 'trojan',
                                    'server': server,
                                    'port': int(port),
                                    'password': password,
                                    'udp': True,
                                    'tls': True
                                }
                                
                                # 解析查询参数
                                if params:
                                    query_params = urllib.parse.parse_qs(params)
                                    sni = query_params.get('sni', [''])[0]
                                    if sni:
                                        proxy['sni'] = sni
                                    
                                    allow_insecure = query_params.get('allowInsecure', [''])[0]
                                    if allow_insecure == '1' or allow_insecure.lower() == 'true':
                                        proxy['skip-cert-verify'] = True
                                
                                return proxy
                    except Exception as e2:
                        pass
            
            return None
        except Exception as e:
            return None
    
    def _parse_vless_raw(self, vless_url: str) -> Optional[Dict[str, Any]]:
        """解析VLESS节点，完全保持原始状态（用于第一个源）"""
        try:
            import urllib.parse
            import re
            
            # 解析VLESS URL
            m = re.match(r'^vless://([^@]+)@([^:]+):(\d+)(?:[?]([^#]+))?(?:#(.+))?$', vless_url)
            if m:
                uuid, server, port, params, name = m.groups()
                
                # 完全保持原始名称
                if not name:
                    name = "VLESS节点"
                else:
                    name = urllib.parse.unquote(name)
                
                proxy = {
                    'name': name,
                    'type': 'vless',
                    'server': server,
                    'port': int(port),
                    'uuid': uuid,
                    'udp': True,
                }
                
                # 解析参数
                if params:
                    for param in params.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            if key == 'encryption':
                                proxy['cipher'] = value
                            elif key == 'type':
                                if value == 'ws':
                                    proxy['network'] = 'ws'
                            elif key == 'path':
                                proxy['ws-opts'] = {'path': value}
                            elif key == 'host':
                                proxy['ws-opts'] = proxy.get('ws-opts', {})
                                proxy['ws-opts']['headers'] = {'Host': value}
                            elif key == 'security':
                                if value == 'tls':
                                    proxy['tls'] = True
                            elif key == 'sni':
                                proxy['sni'] = value
                
                return proxy
            return None
        except Exception as e:
            return None
    
    def _parse_ssr_raw(self, ssr_url: str) -> Optional[Dict[str, Any]]:
        """解析SSR节点，完全保持原始状态（用于第一个源）"""
        try:
            import urllib.parse
            import base64
            
            # 解析SSR URL
            b64 = ssr_url[6:]  # 去掉 'ssr://'
            b64 += '=' * (-len(b64) % 4)
            raw = base64.b64decode(b64).decode('utf-8')
            
            # 解析格式：server:port:protocol:method:obfs:password_base64/?params
            parts = raw.split('/')
            main_part = parts[0]
            params_part = parts[1] if len(parts) > 1 else ''
            
            # 解析主要部分
            main_parts = main_part.split(':')
            
            # 处理不完整的SSR格式
            if len(main_parts) < 6:
                # 如果只有服务器和端口，使用默认值
                if len(main_parts) >= 2:
                    server, port = main_parts[0], main_parts[1]
                    protocol = 'origin'
                    method = 'none'
                    obfs = 'plain'
                    password = ''
                else:
                    return None
            else:
                server, port, protocol, method, obfs, password_b64 = main_parts[:6]
                
                # 解码密码
                if password_b64:
                    password_b64 += '=' * (-len(password_b64) % 4)
                    try:
                        password = base64.b64decode(password_b64).decode('utf-8')
                    except:
                        password = ''
                else:
                    password = ''
            
            # 解析参数
            name = "SSR节点"
            if params_part:
                params = urllib.parse.parse_qs(params_part)
                if 'remarks' in params:
                    name_b64 = params['remarks'][0]
                    name_b64 += '=' * (-len(name_b64) % 4)
                    try:
                        name = base64.b64decode(name_b64).decode('utf-8')
                    except:
                        name = "SSR节点"
            
            return {
                'name': name,
                'type': 'ssr',
                'server': server,
                'port': int(port),
                'cipher': method,
                'password': password,
                'protocol': protocol,
                'obfs': obfs,
            }
        except Exception as e:
            return None
    
    def _parse_hysteria2_raw(self, hysteria2_url: str) -> Optional[Dict[str, Any]]:
        """解析Hysteria2节点，完全保持原始状态（用于第一个源）"""
        try:
            import urllib.parse
            import re
            
            # 解析Hysteria2 URL
            m = re.match(r'^(?:hysteria2|hy2)://([^@]+)@([^:]+):(\d+)(?:[?]([^#]+))?(?:#(.+))?$', hysteria2_url)
            if m:
                password, server, port, params, name = m.groups()
                
                # 完全保持原始名称
                if not name:
                    name = "Hysteria2节点"
                else:
                    name = urllib.parse.unquote(name)
                
                proxy = {
                    'name': name,
                    'type': 'hysteria2',
                    'server': server,
                    'port': int(port),
                    'password': password,
                    'udp': True,
                }
                
                # 解析参数
                if params:
                    for param in params.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            if key == 'sni':
                                proxy['sni'] = value
                            elif key == 'insecure':
                                proxy['skip-cert-verify'] = value == '1'
                
                return proxy
            return None
        except Exception as e:
            return None
    
    def _parse_tuic_raw(self, tuic_url: str) -> Optional[Dict[str, Any]]:
        """解析TUIC节点，完全保持原始状态（用于第一个源）"""
        try:
            import urllib.parse
            import re
            
            # 解析TUIC URL
            m = re.match(r'^tuic://([^@]+)@([^:]+):(\d+)(?:[?]([^#]+))?(?:#(.+))?$', tuic_url)
            if m:
                uuid, server, port, params, name = m.groups()
                
                # 完全保持原始名称
                if not name:
                    name = "TUIC节点"
                else:
                    name = urllib.parse.unquote(name)
                
                proxy = {
                    'name': name,
                    'type': 'tuic',
                    'server': server,
                    'port': int(port),
                    'uuid': uuid,
                    'udp': True,
                }
                
                # 解析参数
                if params:
                    for param in params.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            if key == 'sni':
                                proxy['sni'] = value
                            elif key == 'insecure':
                                proxy['skip-cert-verify'] = value == '1'
                
                return proxy
            return None
        except Exception as e:
            return None

    def _decode_vmess_legacy(self, vmess_url: str, name_count: dict, filter_keywords: List[str] = None) -> Optional[Dict[str, Any]]:
        """按照老代码逻辑解析VMess节点"""
        try:
            b64 = vmess_url[8:]
            b64 += '=' * (-len(b64) % 4)
            raw = base64.b64decode(b64).decode('utf-8')
            
            # 检查是否是SS格式的Base64编码（被错误标记为VMess）
            if ':' in raw and '@' in raw and not raw.startswith('{'):
                # 这可能是SS格式的Base64编码
                parts = raw.split('@')
                if len(parts) == 2:
                    userinfo_part = parts[0]
                    server_part = parts[1]
                    
                    if ':' in userinfo_part and ':' in server_part:
                        method, password = userinfo_part.split(':', 1)
                        server, port = server_part.split(':', 1)
                        
                        # 构造SS节点
                        return {
                            'name': get_unique_name("SS节点", name_count, "SS", server, filter_keywords),
                            'type': 'ss',
                            'server': server,
                            'port': int(port),
                            'cipher': method,
                            'password': password,
                        }
            
            # 尝试作为标准VMess解析
            data = json.loads(raw)
            name = data.get('ps', '')
            server = data.get('add')
            
            # 解码节点名称
            if name:
                name = urllib.parse.unquote(name)
                name = unicode_decode(name)
            
            # 如果没有节点名称或名称为默认值，使用美国作为默认名称
            if not name or name.strip() == '' or name == 'vmess':
                name = "美国"
            
            port = int(data.get('port'))
            uuid = data.get('id')
            alterId = int(data.get('aid', 0))
            cipher = data.get('scy', 'auto')
            # 修复不支持的加密方法
            if cipher == 'auto':
                cipher = 'auto'  # VMess的auto在Clash中是支持的，但为了保险起见，我们保持原样
            network = data.get('net', 'tcp')
            tls = data.get('tls', '') == 'tls'
            
            proxy = {
                'name': get_unique_name(name, name_count, "VMess", server, filter_keywords),
                'type': 'vmess',
                'server': server,
                'port': port,
                'uuid': uuid,
                'alterId': alterId,
                'cipher': cipher,
                'udp': True,
                'tls': tls,
            }
            
            # 处理不同的网络类型
            if network == 'ws':
                proxy['network'] = 'ws'
                proxy['ws-opts'] = {
                    'path': data.get('path', '/'),
                    'headers': {
                        'Host': data.get('host', '')
                    }
                }
            elif network == 'h2':
                proxy['network'] = 'h2'
                proxy['h2-opts'] = {
                    'path': data.get('path', '/'),
                    'host': [data.get('host', '')]
                }
            elif network == 'grpc':
                proxy['network'] = 'grpc'
                proxy['grpc-opts'] = {
                    'grpc-service-name': data.get('path', '')
                }
            
            return proxy
        except Exception as e:
            self._add_log(f"解析VMess节点失败: {str(e)}", "warning")
            return None
    
    def _decode_ss_legacy(self, ss_url: str, name_count: dict, filter_keywords: List[str] = None) -> Optional[Dict[str, Any]]:
        """按照老代码逻辑解析SS节点"""
        try:
            # 处理SS URL格式
            if '#' in ss_url:
                url_part, name_part = ss_url.split('#', 1)
                name = urllib.parse.unquote(name_part)
                name = unicode_decode(name)
            else:
                url_part = ss_url
                name = "SS节点"
            
            # 解析URL部分
            url_part = url_part[5:]  # 去掉 'ss://'
            
            # 处理URL参数
            if '?' in url_part:
                base_part, params_part = url_part.split('?', 1)
                # 忽略参数部分，只处理基础部分
                url_part = base_part
            
            if '@' in url_part:
                method_password, server_port = url_part.split('@', 1)
                if ':' in server_port:
                    server, port = server_port.split(':', 1)
                    port = int(port)
                else:
                    server = server_port
                    port = 443
                
                # 解码method和password
                try:
                    decoded = base64.b64decode(method_password + '==').decode('utf-8')
                    if ':' in decoded:
                        method, password = decoded.split(':', 1)
                    else:
                        method = 'aes-256-gcm'
                        password = decoded
                except:
                    method = 'aes-256-gcm'
                    password = ''
            else:
                # 处理base64编码的完整URL
                try:
                    decoded = base64.b64decode(url_part + '==').decode('utf-8')
                    if '@' in decoded:
                        method_password, server_port = decoded.split('@', 1)
                        if ':' in method_password:
                            method, password = method_password.split(':', 1)
                        else:
                            method = 'aes-256-gcm'
                            password = method_password
                        
                        if ':' in server_port:
                            server, port = server_port.split(':', 1)
                            port = int(port)
                        else:
                            server = server_port
                            port = 443
                    else:
                        return None
                except:
                    return None
            
            # 修复不支持的加密方法
            if method == 'auto':
                method = 'aes-256-gcm'  # 将auto替换为Clash支持的加密方法
            
            return {
                'name': get_unique_name(name, name_count, "SS", server, filter_keywords),
                'type': 'ss',
                'server': server,
                'port': port,
                'cipher': method,
                'password': password,
                'udp': True
            }
        except Exception as e:
            self._add_log(f"解析SS节点失败: {str(e)}", "warning")
            return None
    
    def _decode_trojan_legacy(self, trojan_url: str, name_count: dict, filter_keywords: List[str] = None) -> Optional[Dict[str, Any]]:
        """按照老代码逻辑解析Trojan节点"""
        try:
            # 解析Trojan URL
            if '#' in trojan_url:
                url_part, name_part = trojan_url.split('#', 1)
                name = urllib.parse.unquote(name_part)
            else:
                url_part = trojan_url
                name = "Trojan节点"
            
            # 解析URL部分
            url_part = url_part[9:]  # 去掉 'trojan://'
            if '@' in url_part:
                password, server_port = url_part.split('@', 1)
                if '?' in server_port:
                    server_port, params = server_port.split('?', 1)
                
                if ':' in server_port:
                    server, port = server_port.split(':', 1)
                    port = int(port)
                else:
                    server = server_port
                    port = 443
            else:
                return None
            
            proxy = {
                'name': get_unique_name(name, name_count, "Trojan", server, filter_keywords),
                'type': 'trojan',
                'server': server,
                'port': port,
                'password': password,
                'udp': True,
                'sni': server
            }
            
            return proxy
        except Exception as e:
            self._add_log(f"解析Trojan节点失败: {str(e)}", "warning")
            return None
    
    def _decode_vless_legacy(self, vless_url: str, name_count: dict, filter_keywords: List[str] = None) -> Optional[Dict[str, Any]]:
        """按照老代码逻辑解析VLESS节点"""
        try:
            # 解析VLESS URL
            if '#' in vless_url:
                url_part, name_part = vless_url.split('#', 1)
                name = urllib.parse.unquote(name_part)
            else:
                url_part = vless_url
                name = "VLESS节点"
            
            # 解析URL部分
            url_part = url_part[8:]  # 去掉 'vless://'
            if '@' in url_part:
                uuid, server_port = url_part.split('@', 1)
                if '?' in server_port:
                    server_port, params = server_port.split('?', 1)
                
                if ':' in server_port:
                    server, port = server_port.split(':', 1)
                    port = int(port)
                else:
                    server = server_port
                    port = 443
            else:
                return None
            
            proxy = {
                'name': get_unique_name(name, name_count, "VLESS", server, filter_keywords),
                'type': 'vless',
                'server': server,
                'port': port,
                'uuid': uuid,
                'udp': True
            }
            
            return proxy
        except Exception as e:
            self._add_log(f"解析VLESS节点失败: {str(e)}", "warning")
            return None
    
    def _decode_vless_reality_legacy(self, vless_url: str, name_count: dict, filter_keywords: List[str] = None) -> Optional[Dict[str, Any]]:
        """按照老代码逻辑解析VLESS Reality节点"""
        try:
            # 解析VLESS Reality URL
            if '#' in vless_url:
                url_part, name_part = vless_url.split('#', 1)
                name = urllib.parse.unquote(name_part)
            else:
                url_part = vless_url
                name = "VLESS Reality节点"
            
            # 解析URL部分
            url_part = url_part[8:]  # 去掉 'vless://'
            if '@' in url_part:
                uuid, server_port = url_part.split('@', 1)
                if '?' in server_port:
                    server_port, params = server_port.split('?', 1)
                
                if ':' in server_port:
                    server, port = server_port.split(':', 1)
                    port = int(port)
                else:
                    server = server_port
                    port = 443
            else:
                return None
            
            proxy = {
                'name': get_unique_name(name, name_count, "VLESS", server, filter_keywords),
                'type': 'vless',
                'server': server,
                'port': port,
                'uuid': uuid,
                'udp': True,
                'network': 'tcp',
                'tls': True,
                'reality-opts': {
                    'public-key': '',
                    'short-id': ''
                }
            }
            
            return proxy
        except Exception as e:
            self._add_log(f"解析VLESS Reality节点失败: {str(e)}", "warning")
            return None
    
    def _decode_ssr_legacy(self, ssr_url: str, name_count: dict, filter_keywords: List[str] = None) -> Optional[Dict[str, Any]]:
        """按照老代码逻辑解析SSR节点"""
        try:
            b64 = ssr_url[6:]  # 去掉 'ssr://'
            b64 += '=' * (-len(b64) % 4)
            raw = base64.b64decode(b64).decode('utf-8')
            parts = raw.split(':')
            if len(parts) < 5:
                return None
                
            if len(parts) == 6:
                # 6部分格式: server:port:protocol:method:obfs:password_base64/?params
                server = parts[0]
                port = int(parts[1])
                protocol = parts[2]
                method = parts[3]
                actual_obfs = parts[4]
                password_and_params = parts[5]
                
                # 检查第6部分是否包含参数
                if '?' in password_and_params:
                    password_b64 = password_and_params.split('?')[0].rstrip('/')
                    actual_params_str = '?' + password_and_params.split('?', 1)[1]
                else:
                    password_b64 = password_and_params
                    actual_params_str = ''
            else:
                # 5部分格式: server:port:protocol:method:obfs/?params
                server = parts[0]
                port = int(parts[1])
                protocol = parts[2]
                method = parts[3]
                obfs_and_params = parts[4]
                
                if '?' in obfs_and_params:
                    actual_obfs = obfs_and_params.split('?')[0].rstrip('/')
                    actual_params_str = '?' + obfs_and_params.split('?', 1)[1]
                else:
                    actual_obfs = obfs_and_params.rstrip('/')
                    actual_params_str = ''
                password_b64 = ''
            
            # 解析参数
            params = {}
            if actual_params_str:
                param_str = actual_params_str[1:]  # 移除开头的?
                
                # 解析URL参数
                for param in param_str.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        try:
                            # 处理URL安全的base64编码
                            url_safe_value = value.replace('-', '+').replace('_', '/')
                            # 修复base64填充
                            padding_needed = (4 - len(url_safe_value) % 4) % 4
                            padded_value = url_safe_value + '=' * padding_needed
                            decoded_value = base64.b64decode(padded_value).decode('utf-8')
                            params[key] = decoded_value
                        except Exception as e:
                            # 如果base64解码失败，尝试直接使用原始值
                            params[key] = value
            
            # 解码密码
            if password_b64:
                try:
                    # 处理URL安全的base64编码
                    url_safe_password = password_b64.replace('-', '+').replace('_', '/')
                    # 修复base64填充
                    padding_needed = (4 - len(url_safe_password) % 4) % 4
                    padded_password = url_safe_password + '=' * padding_needed
                    password = base64.b64decode(padded_password).decode('utf-8')
                except Exception as e:
                    password = password_b64  # 如果解码失败，使用原始值
            else:
                # 如果没有password_b64，尝试从参数中获取，或使用服务器信息作为密码
                password = params.get('password', f'{server}_password')
            
            # 获取节点名称 - remarks参数也需要base64解码
            name = params.get('remarks', '')
            if name:
                # remarks参数已经在上面解析时进行了base64解码
                name = urllib.parse.unquote(name)
                name = unicode_decode(name)
            else:
                name = "SSR节点"
            
            return {
                'name': get_unique_name(name, name_count, "SSR", server, filter_keywords),
                'type': 'ssr',
                'server': server,
                'port': port,
                'cipher': method,
                'password': password,
                'obfs': actual_obfs,
                'protocol': protocol,
                'udp': True
            }
        except Exception as e:
            self._add_log(f"解析SSR节点失败: {str(e)}", "warning")
            return None
    
    def _decode_hysteria2_legacy(self, hysteria2_url: str, name_count: dict, filter_keywords: List[str] = None) -> Optional[Dict[str, Any]]:
        """按照老代码逻辑解析Hysteria2节点"""
        try:
            # 解析Hysteria2 URL
            if '#' in hysteria2_url:
                url_part, name_part = hysteria2_url.split('#', 1)
                name = urllib.parse.unquote(name_part)
            else:
                url_part = hysteria2_url
                name = "Hysteria2节点"
            
            # 解析URL部分
            url_part = url_part[12:]  # 去掉 'hysteria2://'
            if '@' in url_part:
                password, server_port = url_part.split('@', 1)
                if '?' in server_port:
                    server_port, params = server_port.split('?', 1)
                
                if ':' in server_port:
                    server, port = server_port.split(':', 1)
                    port = int(port)
                else:
                    server = server_port
                    port = 443
            else:
                return None
            
            return {
                'name': get_unique_name(name, name_count, "Hysteria2", server, filter_keywords),
                'type': 'hysteria2',
                'server': server,
                'port': port,
                'password': password,
                'udp': True
            }
        except Exception as e:
            self._add_log(f"解析Hysteria2节点失败: {str(e)}", "warning")
            return None
    
    def _decode_tuic_legacy(self, tuic_url: str, name_count: dict, filter_keywords: List[str] = None) -> Optional[Dict[str, Any]]:
        """按照老代码逻辑解析TUIC节点"""
        try:
            # 解析TUIC URL
            if '#' in tuic_url:
                url_part, name_part = tuic_url.split('#', 1)
                name = urllib.parse.unquote(name_part)
            else:
                url_part = tuic_url
                name = "TUIC节点"
            
            # 解析URL部分
            url_part = url_part[6:]  # 去掉 'tuic://'
            if '@' in url_part:
                password, server_port = url_part.split('@', 1)
                if '?' in server_port:
                    server_port, params = server_port.split('?', 1)
                
                if ':' in server_port:
                    server, port = server_port.split(':', 1)
                    port = int(port)
                else:
                    server = server_port
                    port = 443
            else:
                return None
            
            return {
                'name': get_unique_name(name, name_count, "TUIC", server, filter_keywords),
                'type': 'tuic',
                'server': server,
                'port': port,
                'password': password,
                'udp': True
            }
        except Exception as e:
            self._add_log(f"解析TUIC节点失败: {str(e)}", "warning")
            return None
    
    def _generate_clash_with_legacy_template(self, proxies: List[Dict[str, Any]], proxy_names: List[str]) -> str:
        """使用老代码的模板生成Clash配置"""
        try:
            # 读取模板文件
            script_dir = os.path.dirname(os.path.abspath(__file__))
            head_file = os.path.join(script_dir, '..', '..', 'templates', 'clash_template_head.yaml')
            tail_file = os.path.join(script_dir, '..', '..', 'templates', 'clash_template_tail.yaml')
            
            # 检查模板文件是否存在
            if not os.path.exists(head_file):
                self._add_log(f"⚠️ 模板文件不存在: {head_file}", "warning")
                return self._create_basic_clash_config_fallback(proxies, proxy_names)
            if not os.path.exists(tail_file):
                self._add_log(f"⚠️ 模板文件不存在: {tail_file}", "warning")
                return self._create_basic_clash_config_fallback(proxies, proxy_names)
            
            with open(head_file, encoding='utf-8') as f:
                head = f.read().rstrip() + '\n'
            with open(tail_file, encoding='utf-8') as f:
                tail = f.read().lstrip()
            
            # 生成proxies部分的YAML
            proxies_yaml = yaml.dump({'proxies': proxies}, allow_unicode=True, sort_keys=False, indent=2)
            
            # 处理tail部分，替换代理名称列表
            tail_lines = tail.split('\n')
            formatted_tail_lines = []
            i = 0
            while i < len(tail_lines):
                line = tail_lines[i]
                if line.strip():
                    if line.startswith('  - name:') or line.startswith('- name:'):
                        # 处理代理组
                        if line.startswith('- name:'):
                            formatted_tail_lines.append('  ' + line)
                        else:
                            formatted_tail_lines.append(line)
                        
                        # 查找proxies字段并替换
                        j = i + 1
                        while j < len(tail_lines):
                            next_line = tail_lines[j]
                            if 'proxies:' in next_line:
                                formatted_tail_lines.append(next_line)
                                
                                # 跳过原有的代理列表
                                k = j + 1
                                while k < len(tail_lines) and (tail_lines[k].startswith('      -') or not tail_lines[k].strip()):
                                    k += 1
                                
                                # 添加新的代理名称列表
                                for proxy_name in proxy_names:
                                    formatted_tail_lines.append(f'      - {proxy_name}')
                                
                                i = k - 1
                                break
                            else:
                                formatted_tail_lines.append(next_line)
                                j += 1
                        if j >= len(tail_lines):
                            i = len(tail_lines)
                    else:
                        formatted_tail_lines.append(line)
                else:
                    formatted_tail_lines.append(line)
                i += 1
            
            formatted_tail = '\n'.join(formatted_tail_lines)
            final_content = head + '\nproxies:\n' + proxies_yaml[9:] + '\nproxy-groups:\n' + formatted_tail
            
            return final_content
        except Exception as e:
            self._add_log(f"使用模板生成Clash配置失败: {str(e)}", "error")
            # 如果模板生成失败，使用基本配置
            return self._create_basic_clash_config_fallback(proxies, proxy_names)
