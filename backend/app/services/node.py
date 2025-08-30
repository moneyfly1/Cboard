from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

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
        node = Node(**node_data)
        
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node

    def update(self, node_id: int, node_data: dict) -> Optional[Node]:
        """更新节点"""
        node = self.get(node_id)
        if not node:
            return None
        
        for field, value in node_data.items():
            setattr(node, field, value)
        
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
        # 总节点数
        total = self.db.query(Node).count()
        
        # 在线节点数
        online = self.db.query(Node).filter(Node.status == "online").count()
        
        # 地区统计
        regions = self.db.query(Node.region).distinct().all()
        regions = [r[0] for r in regions if r[0]]
        
        # 类型统计
        types = self.db.query(Node.type).distinct().all()
        types = [t[0] for t in types if t[0]]
        
        # 平均延迟
        avg_latency = self.db.query(func.avg(Node.latency)).scalar() or 0
        
        # 平均负载
        avg_load = self.db.query(func.avg(Node.load)).scalar() or 0
        
        return {
            "total": total,
            "online": online,
            "regions": regions,
            "types": types,
            "avg_latency": float(avg_latency),
            "avg_load": float(avg_load)
        }

    def update_node_status(self, node_id: int, status: str, load: float = None, latency: int = None):
        """更新节点状态"""
        node = self.get(node_id)
        if not node:
            return False
        
        node.status = status
        if load is not None:
            node.load = load
        if latency is not None:
            node.latency = latency
        node.last_update = datetime.utcnow()
        
        self.db.commit()
        return True

    def get_recommended_nodes(self) -> List[Node]:
        """获取推荐节点"""
        return self.db.query(Node).filter(
            Node.status == "online",
            Node.is_recommended == True
        ).order_by(Node.load.asc()).limit(5).all()

    def get_fastest_nodes(self, limit: int = 10) -> List[Node]:
        """获取最快的节点"""
        return self.db.query(Node).filter(
            Node.status == "online"
        ).order_by(Node.latency.asc()).limit(limit).all()

    def get_nodes_by_load(self, max_load: float = 50.0) -> List[Node]:
        """获取负载较低的节点"""
        return self.db.query(Node).filter(
            Node.status == "online",
            Node.load <= max_load
        ).order_by(Node.load.asc()).all() 