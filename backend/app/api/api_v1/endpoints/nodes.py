from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ResponseBase
from app.services.node import NodeService
from app.utils.security import get_current_user

router = APIRouter()

@router.get("/", response_model=ResponseBase)
def get_nodes(
    db: Session = Depends(get_db)
) -> Any:
    """获取节点列表"""
    node_service = NodeService(db)
    nodes = node_service.get_all_nodes()
    
    return ResponseBase(
        data={
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "region": node.region,
                    "type": node.type,
                    "status": node.status,
                    "load": node.load,
                    "speed": node.speed,
                    "uptime": node.uptime,
                    "latency": node.latency,
                    "description": node.description,
                    "is_recommended": node.is_recommended
                }
                for node in nodes
            ]
        }
    )

@router.get("/{node_id}", response_model=ResponseBase)
def get_node(
    node_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """获取节点详情"""
    node_service = NodeService(db)
    node = node_service.get(node_id)
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    return ResponseBase(
        data={
            "node": {
                "id": node.id,
                "name": node.name,
                "region": node.region,
                "type": node.type,
                "status": node.status,
                "load": node.load,
                "speed": node.speed,
                "uptime": node.uptime,
                "latency": node.latency,
                "description": node.description,
                "is_recommended": node.is_recommended,
                "config": node.config
            }
        }
    )

@router.post("/{node_id}/test", response_model=ResponseBase)
def test_node(
    node_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """测试节点连接"""
    node_service = NodeService(db)
    
    # 检查节点是否存在
    node = node_service.get(node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    # 测试节点连接
    test_result = node_service.test_node_connection(node_id)
    
    return ResponseBase(
        data={
            "node_id": node_id,
            "latency": test_result.get("latency", 0),
            "status": test_result.get("status", "failed"),
            "message": test_result.get("message", "测试失败")
        }
    )

@router.get("/stats/overview", response_model=ResponseBase)
def get_nodes_stats(
    db: Session = Depends(get_db)
) -> Any:
    """获取节点统计信息"""
    node_service = NodeService(db)
    stats = node_service.get_nodes_stats()
    
    return ResponseBase(
        data={
            "total_nodes": stats.get("total", 0),
            "online_nodes": stats.get("online", 0),
            "regions": stats.get("regions", []),
            "types": stats.get("types", []),
            "avg_latency": stats.get("avg_latency", 0),
            "avg_load": stats.get("avg_load", 0)
        }
    ) 