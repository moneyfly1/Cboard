from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.payment_config import PaymentConfig
from app.schemas.payment_config import (
    PaymentConfigCreate, PaymentConfigUpdate,
    PaymentConfigList
)

class PaymentConfigService:
    def __init__(self, db: Session):
        self.db = db

    def get_payment_configs(
        self,
        skip: int = 0,
        limit: int = 100,
        pay_type_filter: Optional[str] = None,
        status_filter: Optional[int] = None
    ) -> List[PaymentConfig]:
        """获取支付配置列表"""
        query = self.db.query(PaymentConfig)

        if pay_type_filter:
            query = query.filter(PaymentConfig.pay_type == pay_type_filter)

        if status_filter is not None:
            query = query.filter(PaymentConfig.status == status_filter)

        return query.order_by(PaymentConfig.sort_order, PaymentConfig.id).offset(skip).limit(limit).all()

    def get_payment_config(self, payment_config_id: int) -> Optional[PaymentConfig]:
        """根据ID获取支付配置"""
        return self.db.query(PaymentConfig).filter(PaymentConfig.id == payment_config_id).first()

    def get_payment_config_by_type(self, pay_type: str) -> Optional[PaymentConfig]:
        """根据支付类型获取支付配置"""
        return self.db.query(PaymentConfig).filter(
            PaymentConfig.pay_type == pay_type,
            PaymentConfig.status == 1
        ).first()

    def get_active_payment_configs(self) -> List[PaymentConfig]:
        """获取所有启用的支付配置"""
        return self.db.query(PaymentConfig).filter(
            PaymentConfig.status == 1
        ).order_by(PaymentConfig.sort_order, PaymentConfig.id).all()

    def create_payment_config(self, payment_config: PaymentConfigCreate) -> PaymentConfig:
        """创建支付配置"""
        db_payment_config = PaymentConfig(**payment_config.dict())
        self.db.add(db_payment_config)
        self.db.commit()
        self.db.refresh(db_payment_config)
        return db_payment_config

    def update_payment_config(
        self,
        payment_config_id: int,
        payment_config: PaymentConfigUpdate
    ) -> Optional[PaymentConfig]:
        """更新支付配置"""
        db_payment_config = self.get_payment_config(payment_config_id)
        if not db_payment_config:
            return None

        update_data = payment_config.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_payment_config, field, value)

        self.db.commit()
        self.db.refresh(db_payment_config)
        return db_payment_config

    def delete_payment_config(self, payment_config_id: int) -> bool:
        """删除支付配置"""
        db_payment_config = self.get_payment_config(payment_config_id)
        if not db_payment_config:
            return False

        self.db.delete(db_payment_config)
        self.db.commit()
        return True

    def update_payment_config_status(self, payment_config_id: int, status: int) -> Optional[PaymentConfig]:
        """更新支付配置状态"""
        db_payment_config = self.get_payment_config(payment_config_id)
        if not db_payment_config:
            return None

        db_payment_config.status = status
        self.db.commit()
        self.db.refresh(db_payment_config)
        return db_payment_config

    def update_payment_config_config(
        self,
        payment_config_id: int,
        config: Dict[str, Any]
    ) -> Optional[PaymentConfig]:
        """更新支付配置的配置内容"""
        db_payment_config = self.get_payment_config(payment_config_id)
        if not db_payment_config:
            return None

        db_payment_config.set_config(config)
        self.db.commit()
        self.db.refresh(db_payment_config)
        return db_payment_config

    def get_payment_config_config(self, payment_config_id: int) -> Optional[Dict[str, Any]]:
        """获取支付配置的配置内容"""
        db_payment_config = self.get_payment_config(payment_config_id)
        return db_payment_config.get_config() if db_payment_config else None

    def test_payment_config(self, payment_config_id: int) -> Dict[str, Any]:
        """测试支付配置"""
        db_payment_config = self.get_payment_config(payment_config_id)
        if not db_payment_config:
            return {"success": False, "message": "支付配置不存在"}

        try:
            # 根据支付类型进行不同的测试
            if db_payment_config.pay_type == "alipay":
                return self._test_alipay_config(db_payment_config.get_config())
            elif db_payment_config.pay_type == "wechat":
                return self._test_wechat_config(db_payment_config.get_config())
            elif db_payment_config.pay_type == "paypal":
                return self._test_paypal_config(db_payment_config.get_config())
            elif db_payment_config.pay_type == "stripe":
                return self._test_stripe_config(db_payment_config.get_config())
            else:
                return {"success": True, "message": "配置验证通过"}
        except Exception as e:
            return {"success": False, "message": f"配置测试失败: {str(e)}"}

    def _test_alipay_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """测试支付宝配置"""
        required_fields = ["app_id", "merchant_private_key", "alipay_public_key"]
        for field in required_fields:
            if not config.get(field):
                return {"success": False, "message": f"缺少必要配置: {field}"}

        return {"success": True, "message": "支付宝配置验证通过"}

    def _test_wechat_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """测试微信支付配置"""
        required_fields = ["app_id", "mch_id", "api_key"]
        for field in required_fields:
            if not config.get(field):
                return {"success": False, "message": f"缺少必要配置: {field}"}

        return {"success": True, "message": "微信支付配置验证通过"}

    def _test_paypal_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """测试PayPal配置"""
        required_fields = ["client_id", "secret"]
        for field in required_fields:
            if not config.get(field):
                return {"success": False, "message": f"缺少必要配置: {field}"}

        return {"success": True, "message": "PayPal配置验证通过"}

    def _test_stripe_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """测试Stripe配置"""
        required_fields = ["publishable_key", "secret_key"]
        for field in required_fields:
            if not config.get(field):
                return {"success": False, "message": f"缺少必要配置: {field}"}

        return {"success": True, "message": "Stripe配置验证通过"}

    def bulk_update_status(self, payment_config_ids: List[int], status: int) -> int:
        """批量更新支付配置状态"""
        result = self.db.query(PaymentConfig).filter(
            PaymentConfig.id.in_(payment_config_ids)
        ).update({"status": status}, synchronize_session=False)

        self.db.commit()
        return result

    def bulk_delete(self, payment_config_ids: List[int]) -> int:
        """批量删除支付配置"""
        result = self.db.query(PaymentConfig).filter(
            PaymentConfig.id.in_(payment_config_ids)
        ).delete(synchronize_session=False)

        self.db.commit()
        return result

    def get_payment_config_stats(self) -> Dict[str, Any]:
        """获取支付配置统计信息"""
        total_configs = self.db.query(PaymentConfig).count()
        active_configs = self.db.query(PaymentConfig).filter(PaymentConfig.status == 1).count()
        inactive_configs = total_configs - active_configs

        # 按类型统计
        type_stats = {}
        types = self.db.query(PaymentConfig.pay_type).distinct().all()
        for (pay_type,) in types:
            count = self.db.query(PaymentConfig).filter(
                PaymentConfig.pay_type == pay_type,
                PaymentConfig.status == 1
            ).count()
            type_stats[pay_type] = count

        return {
            "total_configs": total_configs,
            "active_configs": active_configs,
            "inactive_configs": inactive_configs,
            "type_stats": type_stats
        }
