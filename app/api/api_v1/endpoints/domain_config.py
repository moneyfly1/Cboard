"""
域名配置管理API
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_admin_user
from app.core.domain_config import get_domain_config
from app.schemas.common import ResponseBase

router = APIRouter()


class DomainConfigRequest(BaseModel):
    """域名配置请求"""
    domain_name: str
    ssl_enabled: bool = True
    frontend_domain: str = None


class DomainConfigResponse(BaseModel):
    """域名配置响应"""
    domain_name: str
    ssl_enabled: bool
    frontend_domain: str = None
    base_url: str
    frontend_url: str
    payment_urls: Dict[str, str]
    email_base_url: str


@router.get("/domain-config", response_model=ResponseBase)
def get_domain_config_info(
    request: Request,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取当前域名配置信息"""
    try:
        domain_config = get_domain_config()
        domain_info = domain_config.get_domain_info(request, db)
        
        return ResponseBase(data=domain_info)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取域名配置失败: {str(e)}")


@router.post("/domain-config", response_model=ResponseBase)
def update_domain_config(
    config_data: DomainConfigRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新域名配置"""
    try:
        domain_config = get_domain_config()
        
        # 验证域名格式
        if not config_data.domain_name or '.' not in config_data.domain_name:
            raise HTTPException(status_code=400, detail="域名格式不正确")
        
        # 更新配置
        domain_config.update_domain_config(
            domain_name=config_data.domain_name,
            ssl_enabled=config_data.ssl_enabled,
            db=db
        )
        
        # 如果配置了前端域名，也保存到数据库
        if config_data.frontend_domain:
            from sqlalchemy import text
            from datetime import datetime
            
            db.execute(text("""
                INSERT OR REPLACE INTO system_configs (key, value, type, created_at, updated_at)
                VALUES ('frontend_domain', :frontend_domain, 'system', :now, :now)
            """), {
                'frontend_domain': config_data.frontend_domain,
                'now': datetime.now()
            })
            db.commit()
        
        # 获取更新后的配置信息
        updated_info = domain_config.get_domain_info(request, db)
        
        return ResponseBase(
            data=updated_info,
            message="域名配置更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ResponseBase(success=False, message=f"更新域名配置失败: {str(e)}")


@router.post("/domain-config/test", response_model=ResponseBase)
def test_domain_config(
    request: Request,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """测试域名配置"""
    try:
        domain_config = get_domain_config()
        domain_info = domain_config.get_domain_info(request, db)
        
        # 测试各个URL的可访问性
        import requests
        
        test_results = {
            'base_url': domain_info['base_url'],
            'ssl_enabled': domain_info['ssl_enabled'],
            'tests': {}
        }
        
        # 测试基础URL
        try:
            response = requests.get(domain_info['base_url'], timeout=5)
            test_results['tests']['base_url'] = {
                'status': 'success',
                'status_code': response.status_code,
                'message': '基础URL可访问'
            }
        except Exception as e:
            test_results['tests']['base_url'] = {
                'status': 'error',
                'message': f'基础URL不可访问: {str(e)}'
            }
        
        # 测试前端URL
        try:
            response = requests.get(domain_info['frontend_url'], timeout=5)
            test_results['tests']['frontend_url'] = {
                'status': 'success',
                'status_code': response.status_code,
                'message': '前端URL可访问'
            }
        except Exception as e:
            test_results['tests']['frontend_url'] = {
                'status': 'error',
                'message': f'前端URL不可访问: {str(e)}'
            }
        
        return ResponseBase(data=test_results)
        
    except Exception as e:
        return ResponseBase(success=False, message=f"测试域名配置失败: {str(e)}")


@router.get("/domain-config/auto-detect", response_model=ResponseBase)
def auto_detect_domain_config(
    request: Request,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """自动检测域名配置"""
    try:
        domain_config = get_domain_config()
        
        # 从请求头自动检测
        host = request.headers.get('host', '')
        ssl_enabled = domain_config.is_ssl_enabled(request, db)
        
        detected_config = {
            'domain_name': host,
            'ssl_enabled': ssl_enabled,
            'base_url': domain_config.get_base_url(request, db),
            'frontend_url': domain_config.get_frontend_url(request, db)
        }
        
        return ResponseBase(
            data=detected_config,
            message="域名配置自动检测完成"
        )
        
    except Exception as e:
        return ResponseBase(success=False, message=f"自动检测域名配置失败: {str(e)}")
