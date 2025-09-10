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

def clean_name(name):
    """清理节点名称 - 按照老代码逻辑"""
    import re
    if not name:
        return name

    # 检查是否是重命名后的格式（如：英国-Trojan-001, 香港-SS-001等）
    # 如果是这种格式，直接返回，不进行清理
    if re.match(r'^[^\s]+-[A-Za-z]+-\d+$', name):
        return name

    # 更强的机场后缀清理，支持多种常见无用后缀
    patterns = [
        r'[\s]*[-_][\s]*(官网|网址|连接|试用|导入|免费|Hoshino|Network|续|费|qq|超时|请更新|订阅|通知|域名|套餐|剩余|到期|流量|GB|TB|过期|expire|traffic|remain|迅云加速|快云加速|脉冲云|闪连一元公益机场|一元公益机场|公益机场|机场|加速|云)[\s]*$',
        r'[\s]*[-_][\s]*[0-9]+[\s]*$',
        r'[\s]*[-_][\s]*[A-Za-z]+[\s]*$',
        # 直接以这些词结尾也去除
        r'(官网|网址|连接|试用|导入|免费|Hoshino|Network|续|费|qq|超时|请更新|订阅|通知|域名|套餐|剩余|到期|流量|GB|TB|过期|expire|traffic|remain|迅云加速|快云加速|脉冲云|闪连一元公益机场|一元公益机场|公益机场|机场|加速|云)$',
        # 处理没有空格的情况，如"-迅云加速"
        r'[-_](官网|网址|连接|试用|导入|免费|Hoshino|Network|续|费|qq|超时|请更新|订阅|通知|域名|套餐|剩余|到期|流量|GB|TB|过期|expire|traffic|remain|迅云加速|快云加速|脉冲云|闪连一元公益机场|一元公益机场|公益机场|机场|加速|云)$'
    ]
    for pattern in patterns:
        name = re.sub(pattern, '', name)

    # 去掉所有空格
    name = re.sub(r'[\s]+', '', name)
    name = name.strip()
    return name

def get_unique_name(name, name_count):
    """获取唯一名称 - 按照老代码逻辑"""
    # 先清理名称
    name = clean_name(name)
    name = name.strip()
    if not name:
        name = "节点"
    
    # 检查名称是否已存在，如果存在则添加编号
    original_name = name
    counter = 1
    while name in name_count:
        counter += 1
        name = f"{original_name}{counter:02d}"
    
    # 记录使用的名称
    name_count[name] = True
    return name

class ConfigUpdateService:
    def __init__(self, db: Session):
        self.db = db
        self.is_running_flag = False
        self.scheduled_task = None
        self.scheduled_thread = None
        self.logs = []
        self.max_logs = 1000
        self.log_cleanup_timer = None
        self.cleanup_interval = 600  # 默认10分钟，可配置
        # 不在初始化时自动启动日志清理定时器
        
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
            
            # 节点采集功能已暂时关闭，等待后期开发
            self._add_log("节点采集功能已暂时关闭，等待后期开发", "info")
            self._add_log("如需使用此功能，请联系开发人员", "warning")
            
            # 暂时跳过节点下载和处理
            # nodes = self._download_and_process_nodes(config)
            
            # 暂时跳过配置文件生成
            # if nodes:
            #     # 生成v2ray配置
            #     v2ray_file = os.path.join(target_dir, config.get("v2ray_file", "xr"))
            #     self._generate_v2ray_config(nodes, v2ray_file)
            #     
            #     # 生成clash配置
            #     clash_file = os.path.join(target_dir, config.get("clash_file", "clash.yaml"))
            #     self._generate_clash_config(nodes, clash_file)
            #     
            #     self._add_log(f"配置更新完成，处理了 {len(nodes)} 个节点", "success")
            #     self._update_last_update_time()
            # else:
            #     self._add_log("未获取到有效节点", "error")
            
            self._add_log("配置更新任务完成（节点采集功能已关闭）", "success")
                
        except Exception as e:
            self._add_log(f"配置更新失败: {str(e)}", "error")
            logger.error(f"配置更新失败: {str(e)}", exc_info=True)
        finally:
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
            
            # 节点采集功能已暂时关闭，等待后期开发
            self._add_log("节点采集功能已暂时关闭，等待后期开发", "info")
            self._add_log("如需使用此功能，请联系开发人员", "warning")
            
            # 暂时跳过节点下载和处理
            # nodes = self._download_and_process_nodes(config)
            
            # if nodes:
            #     self._add_log(f"测试完成，处理了 {len(nodes)} 个节点", "success")
            # else:
            #     self._add_log("测试失败，未获取到有效节点", "error")
            
            self._add_log("测试任务完成（节点采集功能已关闭）", "success")
                
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
    
    def _download_and_process_nodes(self, config: Dict[str, Any]) -> List[str]:
        """下载和处理节点"""
        urls = config.get("urls", [])
        filter_keywords = config.get("filter_keywords", [])
        nodes = []
        
        # 检查是否配置了节点源URL
        if not urls:
            self._add_log("错误：未配置节点源URL，请在后台设置中添加节点源", "error")
            raise ValueError("未配置节点源URL，请在后台设置中添加节点源")
        
        # 检查是否配置了过滤关键词
        if not filter_keywords:
            self._add_log("警告：未配置过滤关键词，将不过滤任何节点", "warning")
        
        for i, url in enumerate(urls):
            try:
                self._add_log(f"正在下载: {url}", "info")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                content = response.text
                
                # 检查是否是base64编码
                if self._is_base64(content):
                    try:
                        content = base64.b64decode(content).decode('utf-8')
                        self._add_log(f"解码base64内容成功", "info")
                    except:
                        self._add_log(f"base64解码失败，使用原始内容", "warning")
                
                # 提取节点链接
                node_links = self._extract_node_links(content)
                self._add_log(f"从 {url} 提取到 {len(node_links)} 个节点链接", "info")
                
                # 显示节点类型统计
                if node_links:
                    type_count = {}
                    for link in node_links[:10]:  # 只统计前10个
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
                        self._add_log(f"节点类型统计: {type_info}", "info")
                
                # 过滤节点
                filtered_links = self._filter_nodes(node_links, filter_keywords)
                
                nodes.extend(filtered_links)
                self._add_log(f"从 {url} 获取到 {len(filtered_links)} 个有效节点", "info")
                
            except Exception as e:
                self._add_log(f"下载 {url} 失败: {str(e)}", "error")
        
        # 去重
        unique_nodes = list(set(nodes))
        self._add_log(f"去重后剩余 {len(unique_nodes)} 个节点", "info")
        
        return unique_nodes
    
    def _is_base64(self, text: str) -> bool:
        """检查文本是否是base64编码"""
        try:
            # 移除空白字符
            clean_text = ''.join(text.split())
            # 检查是否只包含base64字符
            if len(clean_text) % 4 != 0:
                return False
            # 尝试解码
            base64.b64decode(clean_text)
            return True
        except:
            return False
    
    def _extract_node_links(self, content: str) -> List[str]:
        """提取节点链接"""
        import re
        patterns = [
            r'vmess://[A-Za-z0-9+/=]+',
            r'vless://[A-Za-z0-9+/=]+',
            r'ss://[A-Za-z0-9+/=]+',
            r'ssr://[A-Za-z0-9+/=]+',
            r'trojan://[A-Za-z0-9+/=]+',
            r'hysteria2://[A-Za-z0-9+/=]+',
            r'hy2://[A-Za-z0-9+/=]+',
            r'tuic://[A-Za-z0-9+/=]+'
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
    
    def _generate_v2ray_config(self, nodes: List[str], output_file: str):
        """生成v2ray配置"""
        try:
            # 将节点链接合并并base64编码
            content = '\n'.join(nodes)
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            # 保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(encoded_content)
            
            # 保存到数据库
            self._save_v2ray_config_to_db(encoded_content)
            
            self._add_log(f"v2ray配置已生成并保存到数据库: {output_file}", "success")
        except Exception as e:
            self._add_log(f"生成v2ray配置失败: {str(e)}", "error")
            raise
    
    def _generate_clash_config(self, nodes: List[str], output_file: str):
        """生成clash配置 - 按照老代码逻辑"""
        try:
            # 按照老代码逻辑解析所有节点
            proxies = []
            proxy_names = []
            name_count = {}
            
            self._add_log(f"开始解析 {len(nodes)} 个节点", "info")
            
            # 统计节点类型
            node_type_count = {}
            failed_count = 0
            
            for i, node in enumerate(nodes, 1):
                try:
                    # 记录节点类型
                    if node.startswith('ss://'):
                        node_type = 'SS'
                    elif node.startswith('ssr://'):
                        node_type = 'SSR'
                    elif node.startswith('vmess://'):
                        node_type = 'VMess'
                    elif node.startswith('trojan://'):
                        node_type = 'Trojan'
                    elif node.startswith('vless://'):
                        node_type = 'VLESS'
                    elif node.startswith('hysteria2://') or node.startswith('hy2://'):
                        node_type = 'Hysteria2'
                    elif node.startswith('tuic://'):
                        node_type = 'TUIC'
                    else:
                        node_type = 'Unknown'
                    
                    proxy = self._parse_node_legacy(node, name_count)
                    if proxy:
                        proxies.append(proxy)
                        proxy_names.append(proxy['name'])
                        node_type_count[node_type] = node_type_count.get(node_type, 0) + 1
                        
                        # 每100个节点记录一次进度
                        if i % 100 == 0:
                            self._add_log(f"已解析 {i}/{len(nodes)} 个节点", "info")
                    else:
                        failed_count += 1
                        if failed_count <= 5:  # 只记录前5个失败案例
                            self._add_log(f"解析第 {i} 个节点失败: {node_type} 节点格式错误", "warning")
                        
                except Exception as e:
                    failed_count += 1
                    if failed_count <= 5:  # 只记录前5个失败案例
                        self._add_log(f"解析第 {i} 个节点异常: {str(e)}", "warning")
                    continue
            
            # 显示解析结果统计
            if node_type_count:
                type_info = ', '.join([f"{k}: {v}" for k, v in node_type_count.items()])
                self._add_log(f"成功解析节点类型统计: {type_info}", "info")
            
            self._add_log(f"成功解析 {len(proxies)} 个节点，失败 {failed_count} 个", "info")
            
            if not proxies:
                self._add_log("没有有效的节点可以生成Clash配置", "error")
                return
            
            # 使用老代码的模板生成完整的Clash配置
            clash_config_content = self._generate_clash_with_legacy_template(proxies, proxy_names)
            
            # 保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(clash_config_content)
            
            # 保存到数据库
            self._save_clash_config_to_db(clash_config_content)
            
            # 清除节点服务缓存，确保下次获取节点时使用最新配置
            try:
                from app.services.node_service import NodeService
                node_service = NodeService(self.db)
                node_service.clear_cache()
                node_service.close()
            except Exception as e:
                self._add_log(f"清除节点缓存失败: {str(e)}", "warning")
            
            self._add_log(f"clash配置已生成并保存到数据库: {output_file}，共 {len(proxies)} 个节点", "success")
        except Exception as e:
            self._add_log(f"生成clash配置失败: {str(e)}", "error")
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
    
    def _parse_vmess_to_clash(self, vmess_url: str, default_name: str, name_count: dict) -> Optional[Dict[str, Any]]:
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
            
            name = self._get_unique_name(name, name_count)
            
            proxy = {
                'name': name,
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
            
            name = self._get_unique_name(name, name_count)
            
            proxy = {
                'name': name,
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
            if network_type == 'ws':
                proxy['network'] = 'ws'
                ws_opts = {}
                path = query_params.get('path', ['/'])[0]
                ws_opts['path'] = path
                host = query_params.get('host', [''])[0]
                if host:
                    ws_opts['headers'] = {'Host': host}
                proxy['ws-opts'] = ws_opts
            elif network_type == 'grpc':
                proxy['network'] = 'grpc'
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
    
    def _parse_ss_to_clash(self, ss_url: str, default_name: str, name_count: dict) -> Optional[Dict[str, Any]]:
        """解析SS节点"""
        try:
            import urllib.parse
            import re
            
            url_parts = urllib.parse.urlparse(ss_url)
            name = default_name
            if url_parts.fragment:
                name = urllib.parse.unquote(url_parts.fragment)
            
            name = self._get_unique_name(name, name_count)
            
            # 尝试解析SS格式
            m = re.match(r'ss://([A-Za-z0-9+/=%]+)@([^:]+):(\d+)', ss_url)
            if m:
                userinfo, server, port = m.groups()
                try:
                    userinfo = urllib.parse.unquote(userinfo)
                    userinfo += '=' * (-len(userinfo) % 4)
                    method_pass = base64.b64decode(userinfo).decode('utf-8')
                    method, password = method_pass.split(':', 1)
                    
                    return {
                        'name': name,
                        'type': 'ss',
                        'server': server,
                        'port': int(port),
                        'cipher': method,
                        'password': password,
                        'udp': True
                    }
                except:
                    pass
            
            return None
        except Exception as e:
            self._add_log(f"解析SS节点失败: {str(e)}", "warning")
            return None
    
    def _parse_ssr_to_clash(self, ssr_url: str, default_name: str, name_count: dict) -> Optional[Dict[str, Any]]:
        """解析SSR节点"""
        try:
            import urllib.parse
            b64 = ssr_url[6:]
            b64 += '=' * (-len(b64) % 4)
            raw = base64.b64decode(b64).decode('utf-8')
            parts = raw.split(':')
            
            if len(parts) < 5:
                return None
            
            server = parts[0]
            port = int(parts[1])
            protocol = parts[2]
            method = parts[3]
            obfs = parts[4]
            
            # 解析密码和参数
            if len(parts) >= 6:
                password_and_params = parts[5]
                if '?' in password_and_params:
                    password_b64 = password_and_params.split('?')[0]
                    params_str = password_and_params.split('?', 1)[1]
                else:
                    password_b64 = password_and_params
                    params_str = ''
                
                try:
                    password_b64 = password_b64.replace('-', '+').replace('_', '/')
                    password_b64 += '=' * (-len(password_b64) % 4)
                    password = base64.b64decode(password_b64).decode('utf-8')
                except:
                    password = password_b64
            else:
                password = f'{server}_password'
                params_str = ''
            
            # 解析参数获取节点名称
            name = default_name
            if params_str:
                params = urllib.parse.parse_qs(params_str)
                if 'remarks' in params:
                    try:
                        remarks_b64 = params['remarks'][0].replace('-', '+').replace('_', '/')
                        remarks_b64 += '=' * (-len(remarks_b64) % 4)
                        name = base64.b64decode(remarks_b64).decode('utf-8')
                        name = urllib.parse.unquote(name)
                    except:
                        pass
            
            name = self._get_unique_name(name, name_count)
            
            return {
                'name': name,
                'type': 'ssr',
                'server': server,
                'port': port,
                'cipher': method,
                'password': password,
                'protocol': protocol,
                'obfs': obfs,
                'udp': True
            }
        except Exception as e:
            self._add_log(f"解析SSR节点失败: {str(e)}", "warning")
            return None
    
    def _parse_trojan_to_clash(self, trojan_url: str, default_name: str, name_count: dict) -> Optional[Dict[str, Any]]:
        """解析Trojan节点"""
        try:
            import urllib.parse
            url_parts = urllib.parse.urlparse(trojan_url)
            server = url_parts.hostname
            port = url_parts.port
            password = url_parts.username
            
            query_params = urllib.parse.parse_qs(url_parts.query)
            
            name = default_name
            if url_parts.fragment:
                name = urllib.parse.unquote(url_parts.fragment)
            
            name = self._get_unique_name(name, name_count)
            
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
            
            name = self._get_unique_name(name, name_count)
            
            proxy = {
                'name': name,
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
            
            name = self._get_unique_name(name, name_count)
            
            return {
                'name': name,
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
                "DOMAIN-SUFFIX,localhost,🎯 全球直连",
                "IP-CIDR,127.0.0.0/8,🎯 全球直连,no-resolve",
                "IP-CIDR,172.16.0.0/12,🎯 全球直连,no-resolve",
                "IP-CIDR,192.168.0.0/16,🎯 全球直连,no-resolve",
                "GEOIP,CN,🎯 全球直连",
                "MATCH,🐟 漏网之鱼"
            ]
        }
        
        return yaml.dump(config, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    def _start_log_cleanup_timer(self, interval: int = None):
        """启动日志清理定时器"""
        try:
            if self.log_cleanup_timer is not None:
                self.log_cleanup_timer.cancel()
            
            # 使用配置的间隔时间，如果没有指定则使用默认值
            cleanup_interval = interval or self.cleanup_interval
            self.log_cleanup_timer = threading.Timer(cleanup_interval, self._cleanup_logs)
            self.log_cleanup_timer.start()
            self._add_log(f"日志清理定时器已启动，每{cleanup_interval//60}分钟清理一次", "info")
        except Exception as e:
            logger.error(f"启动日志清理定时器失败: {str(e)}")
    
    def _cleanup_logs(self):
        """清理日志"""
        try:
            # 清空内存中的日志
            self.logs = []
            
            # 清空数据库中的日志
            logs_record = self.db.query(SystemConfig).filter(SystemConfig.key == "config_update_logs").first()
            if logs_record:
                logs_record.value = json.dumps([])
                self.db.commit()
            
            self._add_log("日志已清理", "info")
            
            # 重新启动定时器
            self._start_log_cleanup_timer()
        except Exception as e:
            logger.error(f"清理日志失败: {str(e)}")
            # 即使清理失败，也要重新启动定时器
            self._start_log_cleanup_timer()
    
    def stop_log_cleanup_timer(self):
        """停止日志清理定时器"""
        try:
            if self.log_cleanup_timer is not None:
                self.log_cleanup_timer.cancel()
                self.log_cleanup_timer = None
                self._add_log("日志清理定时器已停止", "info")
        except Exception as e:
            logger.error(f"停止日志清理定时器失败: {str(e)}")
    
    def set_cleanup_interval(self, interval_minutes: int):
        """设置日志清理间隔（分钟）"""
        if interval_minutes < 1:
            raise ValueError("清理间隔不能小于1分钟")
        
        self.cleanup_interval = interval_minutes * 60  # 转换为秒
        self._add_log(f"日志清理间隔已设置为{interval_minutes}分钟", "info")
        
        # 如果定时器正在运行，重新启动以应用新间隔
        if self.log_cleanup_timer is not None:
            self._start_log_cleanup_timer()
    
    def get_cleanup_interval(self) -> int:
        """获取日志清理间隔（分钟）"""
        return self.cleanup_interval // 60
    
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
    
    def _parse_node_legacy(self, node_url: str, name_count: dict) -> Optional[Dict[str, Any]]:
        """按照老代码逻辑解析节点"""
        try:
            if node_url.startswith('vmess://'):
                return self._decode_vmess_legacy(node_url, name_count)
            elif node_url.startswith('ss://'):
                return self._decode_ss_legacy(node_url, name_count)
            elif node_url.startswith('trojan://'):
                return self._decode_trojan_legacy(node_url, name_count)
            elif node_url.startswith('vless://'):
                if 'reality' in node_url.lower() or 'pbk=' in node_url:
                    return self._decode_vless_reality_legacy(node_url, name_count)
                else:
                    return self._decode_vless_legacy(node_url, name_count)
            elif node_url.startswith('ssr://'):
                return self._decode_ssr_legacy(node_url, name_count)
            elif node_url.startswith('hysteria2://') or node_url.startswith('hy2://'):
                return self._decode_hysteria2_legacy(node_url, name_count)
            elif node_url.startswith('tuic://'):
                return self._decode_tuic_legacy(node_url, name_count)
            else:
                return None
        except Exception as e:
            self._add_log(f"解析节点失败: {str(e)}", "warning")
            return None
    
    def _decode_vmess_legacy(self, vmess_url: str, name_count: dict) -> Optional[Dict[str, Any]]:
        """按照老代码逻辑解析VMess节点"""
        try:
            b64 = vmess_url[8:]
            b64 += '=' * (-len(b64) % 4)
            raw = base64.b64decode(b64).decode('utf-8')
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
                'name': get_unique_name(name, name_count),
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
    
    def _decode_ss_legacy(self, ss_url: str, name_count: dict) -> Optional[Dict[str, Any]]:
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
                'name': get_unique_name(name, name_count),
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
    
    def _decode_trojan_legacy(self, trojan_url: str, name_count: dict) -> Optional[Dict[str, Any]]:
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
                'name': get_unique_name(name, name_count),
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
    
    def _decode_vless_legacy(self, vless_url: str, name_count: dict) -> Optional[Dict[str, Any]]:
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
                'name': get_unique_name(name, name_count),
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
    
    def _decode_vless_reality_legacy(self, vless_url: str, name_count: dict) -> Optional[Dict[str, Any]]:
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
                'name': get_unique_name(name, name_count),
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
    
    def _decode_ssr_legacy(self, ssr_url: str, name_count: dict) -> Optional[Dict[str, Any]]:
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
                'name': get_unique_name(name, name_count),
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
    
    def _decode_hysteria2_legacy(self, hysteria2_url: str, name_count: dict) -> Optional[Dict[str, Any]]:
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
                'name': get_unique_name(name, name_count),
                'type': 'hysteria2',
                'server': server,
                'port': port,
                'password': password,
                'udp': True
            }
        except Exception as e:
            self._add_log(f"解析Hysteria2节点失败: {str(e)}", "warning")
            return None
    
    def _decode_tuic_legacy(self, tuic_url: str, name_count: dict) -> Optional[Dict[str, Any]]:
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
                'name': get_unique_name(name, name_count),
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
                                    if tail_lines[k].strip():
                                        formatted_tail_lines.append(tail_lines[k])
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
