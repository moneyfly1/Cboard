from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func

from app.core.database import Base

class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="节点名称")
    region = Column(String(50), nullable=False, comment="地区")
    type = Column(String(20), nullable=False, comment="节点类型")
    status = Column(String(20), default="offline", comment="节点状态")
    load = Column(Float, default=0.0, comment="负载百分比")
    speed = Column(Float, default=0.0, comment="速度(MB/s)")
    uptime = Column(Integer, default=0, comment="在线时间(秒)")
    latency = Column(Integer, default=0, comment="延迟(毫秒)")
    description = Column(Text, comment="节点描述")
    config = Column(Text, comment="节点配置")
    is_recommended = Column(Boolean, default=False, comment="是否推荐")
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_test = Column(DateTime, comment="最后测试时间")
    last_update = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="最后更新时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间") 