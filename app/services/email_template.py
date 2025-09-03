from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
from jinja2 import Template, Environment, BaseLoader
from app.models.notification import EmailTemplate
from app.schemas.notification import EmailTemplateCreate, EmailTemplateUpdate

class EmailTemplateService:
    def __init__(self, db: Session):
        self.db = db
        # 创建Jinja2环境，支持安全的模板渲染
        self.env = Environment(loader=BaseLoader())
    
    def get_template(self, template_name: str) -> Optional[EmailTemplate]:
        """获取邮件模板"""
        return self.db.query(EmailTemplate).filter(
            EmailTemplate.name == template_name,
            EmailTemplate.is_active == True
        ).first()
    
    def get_template_by_id(self, template_id: int) -> Optional[EmailTemplate]:
        """根据ID获取邮件模板"""
        return self.db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    
    def get_all_templates(self) -> List[EmailTemplate]:
        """获取所有邮件模板"""
        return self.db.query(EmailTemplate).order_by(EmailTemplate.name).all()
    
    def get_active_templates(self) -> List[EmailTemplate]:
        """获取所有激活的邮件模板"""
        return self.db.query(EmailTemplate).filter(
            EmailTemplate.is_active == True
        ).order_by(EmailTemplate.name).all()
    
    def create_template(self, template_data: EmailTemplateCreate) -> EmailTemplate:
        """创建邮件模板"""
        # 检查模板名称是否已存在
        existing = self.db.query(EmailTemplate).filter(
            EmailTemplate.name == template_data.name
        ).first()
        
        if existing:
            raise ValueError(f"模板名称 '{template_data.name}' 已存在")
        
        template = EmailTemplate(**template_data.dict())
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def update_template(self, template_id: int, template_data: EmailTemplateUpdate) -> Optional[EmailTemplate]:
        """更新邮件模板"""
        template = self.db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
        if not template:
            return None
        
        # 如果更新名称，检查是否与其他模板冲突
        if template_data.name and template_data.name != template.name:
            existing = self.db.query(EmailTemplate).filter(
                EmailTemplate.name == template_data.name,
                EmailTemplate.id != template_id
            ).first()
            if existing:
                raise ValueError(f"模板名称 '{template_data.name}' 已存在")
        
        update_data = template_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def delete_template(self, template_id: int) -> bool:
        """删除邮件模板"""
        template = self.db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
        if not template:
            return False
        
        self.db.delete(template)
        self.db.commit()
        return True
    
    def toggle_template_status(self, template_id: int) -> Optional[EmailTemplate]:
        """切换模板状态"""
        template = self.db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
        if not template:
            return None
        
        template.is_active = not template.is_active
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def render_template(self, template_name: str, variables: Dict[str, Any]) -> tuple[str, str]:
        """渲染邮件模板"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"邮件模板 '{template_name}' 不存在或未激活")
        
        try:
            # 使用Jinja2渲染模板
            jinja_template = self.env.from_string(template.content)
            rendered_content = jinja_template.render(**variables)
            
            # 渲染主题（如果主题包含变量）
            subject_template = self.env.from_string(template.subject)
            rendered_subject = subject_template.render(**variables)
            
            return rendered_subject, rendered_content
        except Exception as e:
            raise ValueError(f"模板渲染失败: {str(e)}")
    
    def get_template_variables(self, template_name: str) -> List[str]:
        """获取模板变量列表"""
        template = self.get_template(template_name)
        if template and template.variables:
            try:
                return json.loads(template.variables)
            except json.JSONDecodeError:
                return []
        return []
    
    def validate_template(self, template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """验证模板变量"""
        required_vars = self.get_template_variables(template_name)
        missing_vars = []
        
        for var in required_vars:
            if var not in variables:
                missing_vars.append(var)
        
        return {
            "valid": len(missing_vars) == 0,
            "missing_variables": missing_vars,
            "provided_variables": list(variables.keys()),
            "required_variables": required_vars
        }
    
    def duplicate_template(self, template_id: int, new_name: str) -> Optional[EmailTemplate]:
        """复制邮件模板"""
        original = self.db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
        if not original:
            return None
        
        # 检查新名称是否已存在
        existing = self.db.query(EmailTemplate).filter(EmailTemplate.name == new_name).first()
        if existing:
            raise ValueError(f"模板名称 '{new_name}' 已存在")
        
        # 创建新模板
        new_template = EmailTemplate(
            name=new_name,
            subject=f"{original.subject} (副本)",
            content=original.content,
            variables=original.variables,
            is_active=False  # 新复制的模板默认不激活
        )
        
        self.db.add(new_template)
        self.db.commit()
        self.db.refresh(new_template)
        return new_template
    
    def get_template_usage_stats(self) -> Dict[str, Any]:
        """获取模板使用统计"""
        # 这里可以扩展为统计每个模板的使用次数
        total_templates = self.db.query(EmailTemplate).count()
        active_templates = self.db.query(EmailTemplate).filter(EmailTemplate.is_active == True).count()
        
        return {
            "total_templates": total_templates,
            "active_templates": active_templates,
            "inactive_templates": total_templates - active_templates
        }
