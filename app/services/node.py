from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
import base64

from app.models.node import Node

class NodeService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, node_id: int) -> Optional[Node]:
        """根据ID获取节点"""
        return self.db.query(Node).filter(Node.id == node_id).first()

    def get_all_nodes(self) -> List[Node]:
        """获取所有节点"""
        return self.db.query(Node).order_by(Node.id.desc()).all()

    def get_active_nodes(self) -> List[Node]:
        """获取活跃节点"""
        return self.db.query(Node).filter(Node.status == "online").all()

    def get_nodes_by_region(self, region: str) -> List[Node]:
        """根据地区获取节点"""
        return self.db.query(Node).filter(Node.region == region).all()

    def get_nodes_by_type(self, node_type: str) -> List[Node]:
        """根据类型获取节点"""
        return self.db.query(Node).filter(Node.type == node_type).all()

    def create(self, node_data: dict) -> Node:
        """创建节点"""
        # 处理配置信息
        config = self._build_node_config(node_data)
        
        # 创建节点对象，只使用模型中存在的字段
        node_fields = {
            "name": node_data.get("name"),
            "region": node_data.get("region"),
            "type": node_data.get("type"),
            "status": node_data.get("status", "offline"),
            "load": node_data.get("load", 0.0),
            "speed": node_data.get("speed", 0.0),
            "uptime": node_data.get("uptime", 0),
            "latency": node_data.get("latency", 0),
            "description": node_data.get("description", ""),
            "config": config,
            "is_recommended": node_data.get("is_recommended", False),
            "is_active": node_data.get("is_active", True)
        }
        
        node = Node(**node_fields)
        
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node

    def update(self, node_id: int, node_data: dict) -> Optional[Node]:
        """更新节点"""
        node = self.get(node_id)
        if not node:
            return None
        
        # 处理配置信息更新
        if "config" in node_data:
            node_data["config"] = self._build_node_config(node_data)
        
        # 只更新模型中存在的字段
        valid_fields = [
            "name", "region", "type", "status", "load", "speed", 
            "uptime", "latency", "description", "config", 
            "is_recommended", "is_active"
        ]
        
        for field in valid_fields:
            if field in node_data:
                setattr(node, field, node_data[field])
        
        self.db.commit()
        self.db.refresh(node)
        return node

    def delete(self, node_id: int) -> bool:
        """删除节点"""
        node = self.get(node_id)
        if not node:
            return False
        
        self.db.delete(node)
        self.db.commit()
        return True

    def _build_node_config(self, node_data: dict) -> str:
        """根据节点数据构建配置字符串"""
        node_type = node_data.get("type", "ssr")
        
        if node_type == "vmess":
            return self._build_vmess_config(node_data)
        elif node_type == "trojan":
            return self._build_trojan_config(node_data)
        elif node_type == "ssr":
            return self._build_ssr_config(node_data)
        elif node_type == "ss":
            return self._build_ss_config(node_data)
        else:
            # 默认返回SSR配置
            return self._build_ssr_config(node_data)

    def _build_vmess_config(self, node_data: dict) -> str:
        """构建vmess配置"""
        config = {
            "v": "2",
            "ps": node_data.get("name", "vmess节点"),
            "add": node_data.get("server", ""),
            "port": node_data.get("port", ""),
            "id": node_data.get("uuid", ""),
            "aid": node_data.get("alterId", "0"),
            "net": node_data.get("network", "tcp"),
            "type": "none",
            "host": "",
            "path": "",
            "tls": node_data.get("tls", "none")
        }
        
        config_str = json.dumps(config, ensure_ascii=False)
        return f"vmess://{base64.b64encode(config_str.encode()).decode()}"

    def _build_trojan_config(self, node_data: dict) -> str:
        """构建trojan配置"""
        server = node_data.get("server", "")
        port = node_data.get("port", "")
        password = node_data.get("password", "")
        name = node_data.get("name", "trojan节点")
        
        return f"trojan://{password}@{server}:{port}#{name}"

    def _build_ssr_config(self, node_data: dict) -> str:
        """构建SSR配置"""
        server = node_data.get("server", "")
        port = node_data.get("port", "")
        protocol = node_data.get("protocol", "origin")
        method = node_data.get("method", "chacha20")
        obfs = node_data.get("obfs", "plain")
        password = node_data.get("password", "")
        obfs_param = node_data.get("obfs_param", "")
        protocol_param = node_data.get("protocol_param", "")
        remarks = node_data.get("name", "ssr节点")
        group = "XBoard"
        
        # 构建SSR字符串
        ssr_str = f"{server}:{port}:{protocol}:{method}:{obfs}:{password}/?obfsparam={obfs_param}&protoparam={protocol_param}&remarks={remarks}&group={group}"
        
        return f"ssr://{base64.b64encode(ssr_str.encode()).decode()}"

    def _build_ss_config(self, node_data: dict) -> str:
        """构建SS配置"""
        method = node_data.get("method", "chacha20")
        password = node_data.get("password", "")
        server = node_data.get("server", "")
        port = node_data.get("port", "")
        name = node_data.get("name", "ss节点")
        
        # 构建SS字符串
        ss_str = f"{method}:{password}@{server}:{port}#{name}"
        
        return f"ss://{base64.b64encode(ss_str.encode()).decode()}"

    def test_node_connection(self, node_id: int) -> Dict:
        """测试节点连接"""
        node = self.get(node_id)
        if not node:
            return {"status": "failed", "message": "节点不存在"}
        
        # 这里应该实现实际的节点连接测试
        # 示例实现
        import random
        import time
        
        # 模拟测试延迟
        time.sleep(0.1)
        latency = random.randint(50, 300)
        
        # 更新节点状态
        node.latency = latency
        node.last_test = datetime.utcnow()
        
        if latency < 200:
            node.status = "online"
            status = "success"
            message = "连接正常"
        else:
            node.status = "offline"
            status = "failed"
            message = "连接超时"
        
        self.db.commit()
        
        return {
            "status": status,
            "latency": latency,
            "message": message
        }

    def get_nodes_stats(self) -> Dict:
        """获取节点统计信息"""
        total_nodes = self.db.query(Node).count()
        online_nodes = self.db.query(Node).filter(Node.status == "online").count()
        offline_nodes = self.db.query(Node).filter(Node.status == "offline").count()
        
        # 计算平均延迟
        avg_latency = self.db.query(func.avg(Node.latency)).scalar() or 0
        
        return {
            "total": total_nodes,
            "online": online_nodes,
            "offline": offline_nodes,
            "avg_latency": round(avg_latency, 2)
        }

    def get_nodes_by_status(self, status: str) -> List[Node]:
        """根据状态获取节点"""
        return self.db.query(Node).filter(Node.status == status).all()

    def update_node_status(self, node_id: int, status: str) -> bool:
        """更新节点状态"""
        node = self.get(node_id)
        if not node:
            return False
        
        node.status = status
        node.last_update = datetime.utcnow()
        self.db.commit()
        return True

    def update_node_load(self, node_id: int, load: float) -> bool:
        """更新节点负载"""
        node = self.get(node_id)
        if not node:
            return False
        
        node.load = load
        node.last_update = datetime.utcnow()
        self.db.commit()
        return True

    def update_node_speed(self, node_id: int, speed: float) -> bool:
        """更新节点速度"""
        node = self.get(node_id)
        if not node:
            return False
        
        node.speed = speed
        node.last_update = datetime.utcnow()
        self.db.commit()
        return True

    def update_node_uptime(self, node_id: int, uptime: int) -> bool:
        """更新节点在线时间"""
        node = self.get(node_id)
        if not node:
            return False
        
        node.uptime = uptime
        node.last_update = datetime.utcnow()
        self.db.commit()
        return True

    def update_node_latency(self, node_id: int, latency: int) -> bool:
        """更新节点延迟"""
        node = self.get(node_id)
        if not node:
            return False
        
        node.latency = latency
        node.last_update = datetime.utcnow()
        self.db.commit()
        return True 