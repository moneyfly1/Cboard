from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ResponseBase
from app.services.node_service import NodeService
from app.utils.security import get_current_user

router = APIRouter()

@router.get("/", response_model=ResponseBase)
def get_nodes(
    db: Session = Depends(get_db)
) -> Any:
    """获取节点列表"""
    node_service = NodeService(db)
    try:
        nodes = node_service.get_nodes_from_clash_config()
        
        return ResponseBase(
            data={
                "nodes": nodes
            },
            message="获取节点列表成功"
        )
    except Exception as e:
        return ResponseBase(
            success=False,
            message=f"获取节点列表失败: {str(e)}"
        )
    finally:
        node_service.close()

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

@router.post("/batch-test", response_model=ResponseBase)
def batch_test_nodes(
    node_ids: List[int],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """批量测试节点"""
    node_service = NodeService(db)
    
    if not node_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请选择要测试的节点"
        )
    
    # 执行批量测速
    results = node_service.batch_test_nodes(node_ids)
    
    return ResponseBase(
        data={
            "results": results,
            "total_tested": len(results),
            "success_count": len([r for r in results if r["status"] == "success"]),
            "failed_count": len([r for r in results if r["status"] == "failed"])
        }
    )

@router.post("/import-from-clash", response_model=ResponseBase)
def import_nodes_from_clash(
    clash_config: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """从Clash配置导入节点"""
    node_service = NodeService(db)
    
    try:
        # 从Clash配置中提取节点信息
        nodes_data = node_service.get_nodes_from_clash_config(clash_config)
        
        if not nodes_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法从Clash配置中提取节点信息"
            )
        
        # 创建节点
        created_nodes = []
        for node_data in nodes_data:
            node = node_service.create(node_data)
            created_nodes.append({
                "id": node.id,
                "name": node.name,
                "type": node.type,
                "region": node.region
            })
        
        return ResponseBase(
            data={
                "imported_nodes": created_nodes,
                "total_imported": len(created_nodes)
            },
            message=f"成功导入 {len(created_nodes)} 个节点"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入节点失败: {str(e)}"
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