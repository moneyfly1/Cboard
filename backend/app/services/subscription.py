from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import secrets
import string
import yaml
import base64
from pathlib import Path

from app.models.subscription import Subscription, Device
from app.models.user import User
from app.models.node import Node
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from app.utils.security import generate_subscription_url

class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, subscription_id: int) -> Optional[Subscription]:
        """根据ID获取订阅"""
        return self.db.query(Subscription).filter(Subscription.id == subscription_id).first()

    def get_by_user_id(self, user_id: int) -> Optional[Subscription]:
        """根据用户ID获取订阅"""
        return self.db.query(Subscription).filter(Subscription.user_id == user_id).first()

    def create(self, subscription_in: SubscriptionCreate) -> Subscription:
        """创建订阅"""
        subscription = Subscription(
            user_id=subscription_in.user_id,
            subscription_url=subscription_in.subscription_url,
            device_limit=subscription_in.device_limit,
            expire_time=subscription_in.expire_time
        )
        
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def update(self, subscription_id: int, subscription_in: SubscriptionUpdate) -> Optional[Subscription]:
        """更新订阅"""
        subscription = self.get(subscription_id)
        if not subscription:
            return None
        
        update_data = subscription_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(subscription, field, value)
        
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def update_subscription_key(self, subscription_id: int, new_key: str = None) -> bool:
        """更新订阅密钥"""
        subscription = self.get(subscription_id)
        if not subscription:
            return False
        
        if new_key is None:
            new_key = generate_subscription_url()
        
        subscription.subscription_url = new_key
        self.db.commit()
        return True

    def delete(self, subscription_id: int) -> bool:
        """删除订阅"""
        subscription = self.get(subscription_id)
        if not subscription:
            return False
        
        self.db.delete(subscription)
        self.db.commit()
        return True

    def get_devices_by_subscription_id(self, subscription_id: int) -> List[Device]:
        """获取订阅的所有设备"""
        return self.db.query(Device).filter(Device.subscription_id == subscription_id).all()

    def get_device(self, device_id: int) -> Optional[Device]:
        """根据ID获取设备"""
        return self.db.query(Device).filter(Device.id == device_id).first()

    def record_device_access(self, subscription_id: int, device_info: dict) -> Device:
        """记录设备访问"""
        # 检查设备是否已存在
        existing_device = self.db.query(Device).filter(
            and_(
                Device.subscription_id == subscription_id,
                Device.fingerprint == device_info["fingerprint"]
            )
        ).first()
        
        if existing_device:
            # 更新现有设备信息
            existing_device.name = device_info.get("name", existing_device.name)
            existing_device.ip = device_info.get("ip", existing_device.ip)
            existing_device.user_agent = device_info.get("user_agent", existing_device.user_agent)
            existing_device.last_access = datetime.utcnow()
            self.db.commit()
            return existing_device
        else:
            # 创建新设备记录
            device = Device(
                subscription_id=subscription_id,
                name=device_info.get("name", "Unknown Device"),
                type=device_info.get("type", "unknown"),
                ip=device_info.get("ip", "unknown"),
                user_agent=device_info.get("user_agent", ""),
                fingerprint=device_info["fingerprint"],
                last_access=datetime.utcnow()
            )
            
            self.db.add(device)
            self.db.commit()
            self.db.refresh(device)
            return device

    def delete_device(self, device_id: int) -> bool:
        """删除设备"""
        device = self.get_device(device_id)
        if not device:
            return False
        
        self.db.delete(device)
        self.db.commit()
        return True

    def delete_devices_by_subscription_id(self, subscription_id: int) -> bool:
        """删除订阅的所有设备"""
        devices = self.get_devices_by_subscription_id(subscription_id)
        for device in devices:
            self.db.delete(device)
        self.db.commit()
        return True

    def check_device_limit(self, subscription_id: int) -> bool:
        """检查设备数量限制"""
        subscription = self.get(subscription_id)
        if not subscription:
            return False
        
        device_count = self.db.query(Device).filter(Device.subscription_id == subscription_id).count()
        return device_count < subscription.device_limit

    def get_active_subscriptions(self) -> List[Subscription]:
        """获取所有有效订阅"""
        now = datetime.utcnow()
        return self.db.query(Subscription).filter(
            or_(
                Subscription.expire_time.is_(None),
                Subscription.expire_time > now
            )
        ).all()

    def get_expired_subscriptions(self) -> List[Subscription]:
        """获取所有过期订阅"""
        now = datetime.utcnow()
        return self.db.query(Subscription).filter(
            and_(
                Subscription.expire_time.isnot(None),
                Subscription.expire_time <= now
            )
        ).all()

    def get_subscription_stats(self) -> dict:
        """获取订阅统计信息"""
        total = self.db.query(Subscription).count()
        active = len(self.get_active_subscriptions())
        expired = len(self.get_expired_subscriptions())
        
        return {
            "total": total,
            "active": active,
            "expired": expired,
            "active_rate": (active / total * 100) if total > 0 else 0
        }

    def generate_ssr_subscription(self, subscription: Subscription) -> str:
        """生成SSR订阅内容"""
        # 获取所有可用节点
        nodes = self.db.query(Node).filter(Node.is_active == True).all()
        
        if not nodes:
            return "# 暂无可用节点"
        
        ssr_lines = []
        for node in nodes:
            # 生成SSR链接格式
            ssr_url = self._generate_ssr_url(node, subscription)
            ssr_lines.append(ssr_url)
        
        return "\n".join(ssr_lines)

    def generate_clash_subscription(self, subscription: Subscription) -> dict:
        """生成Clash订阅内容"""
        # 获取所有可用节点
        nodes = self.db.query(Node).filter(Node.is_active == True).all()
        
        if not nodes:
            return {"error": "暂无可用节点"}
        
        # 读取Clash模板配置
        template_path = Path("uploads/config/clash.yaml")
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            # 使用默认配置
            config = self._get_default_clash_config()
        
        # 添加节点到配置
        proxies = []
        proxy_names = []
        
        for node in nodes:
            proxy_config = self._generate_clash_proxy_config(node, subscription)
            proxies.append(proxy_config)
            proxy_names.append(node.name)
        
        config["proxies"] = proxies
        
        # 更新代理组
        if "proxy-groups" in config:
            for group in config["proxy-groups"]:
                if group["type"] == "select":
                    group["proxies"] = proxy_names
        
        return config

    def _generate_ssr_url(self, node: Node, subscription: Subscription) -> str:
        """生成SSR URL"""
        # SSR URL格式: ssr://server:port:protocol:method:obfs:password/?obfsparam=&protoparam=&remarks=&group=
        
        # 基础参数
        server = node.server
        port = node.port
        protocol = node.protocol or "origin"
        method = node.method or "chacha20"
        obfs = node.obfs or "plain"
        password = node.password or ""
        
        # 特殊参数
        obfsparam = node.obfs_param or ""
        protoparam = node.protocol_param or ""
        remarks = node.name
        group = "XBoard"
        
        # 构建URL
        ssr_str = f"{server}:{port}:{protocol}:{method}:{obfs}:{password}/?obfsparam={obfsparam}&protoparam={protoparam}&remarks={remarks}&group={group}"
        
        # Base64编码
        return f"ssr://{base64.b64encode(ssr_str.encode()).decode()}"

    def _generate_clash_proxy_config(self, node: Node, subscription: Subscription) -> dict:
        """生成Clash代理配置"""
        return {
            "name": node.name,
            "type": "ssr",
            "server": node.server,
            "port": node.port,
            "cipher": node.method or "chacha20",
            "password": node.password or "",
            "protocol": node.protocol or "origin",
            "protocol-param": node.protocol_param or "",
            "obfs": node.obfs or "plain",
            "obfs-param": node.obfs_param or ""
        }

    def _get_default_clash_config(self) -> dict:
        """获取默认Clash配置"""
        return {
            "port": 7890,
            "socks-port": 7891,
            "allow-lan": True,
            "mode": "Rule",
            "log-level": "info",
            "external-controller": ":9090",
            "proxies": [],
            "proxy-groups": [
                {
                    "name": "Proxy",
                    "type": "select",
                    "proxies": []
                }
            ],
            "rules": [
                "MATCH,Proxy"
            ]
        } 