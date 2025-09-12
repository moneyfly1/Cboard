from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.schemas.notification import (
    EmailTemplateCreate, EmailTemplateUpdate, EmailTemplate, 
    EmailTemplateList, EmailTemplatePreview, EmailTemplateDuplicate
)
from app.services.email_template import EmailTemplateService
from app.services.email import EmailService
from app.utils.security import get_current_admin_user
from app.schemas.common import ResponseBase

router = APIRouter()

@router.get("/", response_model=EmailTemplateList)
def get_email_templates(
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取所有邮件模板（分页）"""
    service = EmailTemplateService(db)
    templates = service.get_all_templates()
    
    # 简单的分页处理
    start = (page - 1) * size
    end = start + size
    paginated_templates = templates[start:end]
    
    return EmailTemplateList(
        templates=paginated_templates,
        total=len(templates),
        page=page,
        size=size
    )

@router.get("/active", response_model=List[EmailTemplate])
def get_active_email_templates(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取所有激活的邮件模板"""
    service = EmailTemplateService(db)
    return service.get_active_templates()

@router.get("/{template_id}", response_model=EmailTemplate)
def get_email_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取指定邮件模板"""
    service = EmailTemplateService(db)
    template = service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="邮件模板不存在")
    return template

@router.post("/", response_model=EmailTemplate)
def create_email_template(
    template: EmailTemplateCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """创建邮件模板"""
    service = EmailTemplateService(db)
    try:
        return service.create_template(template)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")

@router.put("/{template_id}", response_model=EmailTemplate)
def update_email_template(
    template_id: int,
    template: EmailTemplateUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """更新邮件模板"""
    service = EmailTemplateService(db)
    try:
        updated_template = service.update_template(template_id, template)
        if not updated_template:
            raise HTTPException(status_code=404, detail="邮件模板不存在")
        return updated_template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新模板失败: {str(e)}")

@router.delete("/{template_id}")
def delete_email_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """删除邮件模板"""
    service = EmailTemplateService(db)
    success = service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="邮件模板不存在")
    
    return ResponseBase(message="邮件模板删除成功")

@router.post("/{template_id}/toggle-status", response_model=EmailTemplate)
def toggle_template_status(
    template_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """切换模板状态（激活/停用）"""
    service = EmailTemplateService(db)
    template = service.toggle_template_status(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="邮件模板不存在")
    
    status_text = "激活" if template.is_active else "停用"
    return template

@router.post("/{template_id}/duplicate", response_model=EmailTemplate)
def duplicate_email_template(
    template_id: int,
    duplicate_data: EmailTemplateDuplicate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """复制邮件模板"""
    service = EmailTemplateService(db)
    try:
        new_template = service.duplicate_template(template_id, duplicate_data.new_name)
        if not new_template:
            raise HTTPException(status_code=404, detail="邮件模板不存在")
        return new_template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"复制模板失败: {str(e)}")

@router.post("/preview", response_model=EmailTemplatePreview)
def preview_email_template(
    preview_data: EmailTemplatePreview,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """预览邮件模板"""
    service = EmailTemplateService(db)
    try:
        subject, content = service.render_template(preview_data.template_name, preview_data.variables)
        return EmailTemplatePreview(
            template_name=preview_data.template_name,
            variables=preview_data.variables,
            preview_subject=subject,
            preview_content=content
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览模板失败: {str(e)}")


@router.get("/{template_name}/variables")
def get_template_variables(
    template_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取模板变量列表"""
    service = EmailTemplateService(db)
    try:
        variables = service.get_template_variables(template_name)
        return ResponseBase(data={"variables": variables})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板变量失败: {str(e)}")

@router.post("/{template_name}/validate")
def validate_template_variables(
    template_name: str,
    variables: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """验证模板变量"""
    service = EmailTemplateService(db)
    try:
        validation = service.validate_template(template_name, variables)
        return ResponseBase(data=validation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证模板变量失败: {str(e)}")

@router.get("/stats/usage")
def get_template_usage_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取模板使用统计"""
    service = EmailTemplateService(db)
    try:
        stats = service.get_template_usage_stats()
        return ResponseBase(data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板统计失败: {str(e)}")

@router.post("/{template_name}/send")
def send_template_email(
    template_name: str,
    to_email: str,
    variables: Dict[str, Any],
    email_type: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """使用指定模板发送邮件"""
    email_service = EmailService(db)
    
    try:
        # 验证模板变量
        service = EmailTemplateService(db)
        validation = service.validate_template(template_name, variables)
        if not validation["valid"]:
            missing_vars = validation["missing_variables"]
            raise HTTPException(
                status_code=400, 
                detail=f"模板变量不完整，缺少: {', '.join(missing_vars)}"
            )
        
        # 发送邮件
        success = email_service.send_template_email(
            template_name,
            to_email,
            variables,
            email_type
        )
        
        if success:
            return ResponseBase(message="邮件发送成功")
        else:
            raise HTTPException(status_code=500, detail="邮件发送失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送邮件失败: {str(e)}")
