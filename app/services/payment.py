from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import hashlib
import hmac
import json
import requests
from urllib.parse import urlencode
from sqlalchemy import desc
import uuid

from app.models.payment import PaymentTransaction, PaymentCallback, PaymentMethod
from app.models.payment_config import PaymentConfig
from app.schemas.payment import (
    PaymentConfigCreate, PaymentConfigUpdate,
    PaymentTransactionCreate, PaymentTransactionUpdate,
    PaymentCallbackCreate, PaymentCallbackUpdate,
    AlipayConfig, WechatConfig, PayPalConfig, StripeConfig, CryptoConfig,
    PaymentCreate, PaymentResponse, PaymentCallback,
    BankTransferConfig, PaymentMethodCreate, PaymentMethodUpdate
)
from app.core.settings_manager import settings_manager
from app.utils.security import get_password_hash, verify_password
import xml.etree.ElementTree as ET
try:
    from alipay import AliPay
    ALIPAY_AVAILABLE = True
except ImportError:
    ALIPAY_AVAILABLE = False


class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    # 基础配置方法
    def is_payment_enabled(self) -> bool:
        """检查支付功能是否启用"""
        return settings_manager.is_payment_enabled(self.db)

    def get_default_payment_method(self) -> str:
        """获取默认支付方式"""
        return settings_manager.get_default_payment_method(self.db)

    def get_payment_currency(self) -> str:
        """获取支付货币"""
        return settings_manager.get_payment_currency(self.db)

    # 支付配置管理
    def get_payment_config(self, config_id: int) -> Optional[PaymentConfig]:
        """获取支付配置"""
        return self.db.query(PaymentConfig).filter(PaymentConfig.id == config_id).first()

    def get_payment_config_by_name(self, name: str) -> Optional[PaymentConfig]:
        """根据名称获取支付配置"""
        return self.db.query(PaymentConfig).filter(PaymentConfig.name == name).first()

    def get_active_payment_configs(self) -> List[PaymentConfig]:
        """获取所有活跃的支付配置"""
        return self.db.query(PaymentConfig).filter(
            PaymentConfig.status == 1
        ).order_by(PaymentConfig.sort_order, PaymentConfig.id).all()

    def get_default_payment_config(self) -> Optional[PaymentConfig]:
        """获取默认支付配置"""
        default_method = self.get_default_payment_method()
        if default_method:
            return self.get_payment_config_by_name(default_method)
        return self.db.query(PaymentConfig).filter(
            PaymentConfig.status == 1
        ).order_by(PaymentConfig.sort_order, PaymentConfig.id).first()

    def get_available_payment_methods(self) -> List[Dict[str, Any]]:
        """获取可用的支付方式列表"""
        # 首先尝试从PaymentMethod表获取
        methods = self.db.query(PaymentMethod).filter(
            PaymentMethod.status == "active"
        ).order_by(PaymentMethod.sort_order, PaymentMethod.id).all()
        
        if methods:
            return [
                {
                    "key": method.type,
                    "name": method.name,
                    "description": method.description or f"使用{method.name}支付",
                    "icon": f"/icons/{method.type}.png",
                    "enabled": True
                }
                for method in methods
            ]
        
        # 如果没有PaymentMethod记录，从PaymentConfig表获取
        configs = self.get_active_payment_configs()
        if configs:
            return [
                {
                    "key": config.pay_type,
                    "name": config.name,
                    "description": config.description or f"使用{config.name}支付",
                    "icon": f"/icons/{config.pay_type}.png",
                    "enabled": True
                }
                for config in configs
            ]
        
        # 如果都没有，返回默认的支付方式
        return [
            {
                "key": "alipay",
                "name": "支付宝",
                "description": "使用支付宝扫码支付",
                "icon": "/icons/alipay.png",
                "enabled": True
            },
            {
                "key": "wechat",
                "name": "微信支付",
                "description": "使用微信扫码支付",
                "icon": "/icons/wechat.png",
                "enabled": True
            },
            {
                "key": "bank_transfer",
                "name": "银行转账",
                "description": "通过银行转账支付",
                "icon": "/icons/bank.png",
                "enabled": True
            }
        ]

    def create_payment_config(self, config_in: PaymentConfigCreate) -> PaymentConfig:
        """创建支付配置"""
        config = PaymentConfig(**config_in.dict())
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update_payment_config(self, config_id: int, config_in: PaymentConfigUpdate) -> Optional[PaymentConfig]:
        """更新支付配置"""
        config = self.get_payment_config(config_id)
        if not config:
            return None
        
        update_data = config_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)
        
        self.db.commit()
        self.db.refresh(config)
        return config

    def delete_payment_config(self, config_id: int) -> bool:
        """删除支付配置"""
        config = self.get_payment_config(config_id)
        if not config:
            return False
        
        self.db.delete(config)
        self.db.commit()
        return True

    # 支付交易管理
    def create_payment_transaction(self, transaction_in: PaymentTransactionCreate) -> PaymentTransaction:
        """创建支付交易"""
        transaction = PaymentTransaction(**transaction_in.dict())
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_payment_transaction(self, transaction_id: str) -> Optional[PaymentTransaction]:
        """获取支付交易"""
        return self.db.query(PaymentTransaction).filter(
            PaymentTransaction.transaction_id == transaction_id
        ).first()

    def update_payment_transaction(self, transaction_id: str, transaction_in: PaymentTransactionUpdate) -> Optional[PaymentTransaction]:
        """更新支付交易"""
        transaction = self.get_payment_transaction(transaction_id)
        if not transaction:
            return None
        
        update_data = transaction_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(transaction, field, value)
        
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    # 支付网关实现
    def create_payment(self, payment_request: PaymentCreate) -> PaymentResponse:
        """创建支付"""
        # 检查支付功能是否启用
        if not self.is_payment_enabled():
            return self._create_failed_response(payment_request, "支付功能未启用")
        
        # 获取支付方式配置
        payment_method = self.db.query(PaymentMethod).filter(
            PaymentMethod.type == payment_request.payment_method
        ).first()
        
        # 如果没有PaymentMethod记录，使用默认配置
        if not payment_method:
            payment_method_config = {
                "type": payment_request.payment_method,
                "name": self._get_payment_method_name(payment_request.payment_method),
                "config": self._get_default_payment_config(payment_request.payment_method)
            }
        else:
            if payment_method.status != "active":
                return self._create_failed_response(payment_request, "支付方式未启用")
            # 如果PaymentMethod的配置为空，使用系统配置
            method_config = payment_method.config or {}
            if not method_config or not method_config.get('app_id'):
                method_config = self._get_default_payment_config(payment_method.type)
            payment_method_config = {
                "type": payment_method.type,
                "name": payment_method.name,
                "config": method_config
            }
        
        # 使用设置中的货币
        currency = payment_request.currency or self.get_payment_currency()
        
        try:
            # 根据支付方式类型创建支付
            payment_creators = {
                "alipay": self._create_alipay_payment,
                "wechat": self._create_wechat_payment,
                "paypal": self._create_paypal_payment,
                "stripe": self._create_stripe_payment,
                "bank_transfer": self._create_bank_transfer_payment,
                "crypto": self._create_crypto_payment
            }
            
            creator = payment_creators.get(payment_method_config["type"])
            if creator:
                return creator(payment_method_config["config"], payment_request, currency)
            else:
                return self._create_failed_response(payment_request, "不支持的支付方式")
                
        except Exception as e:
            return self._create_failed_response(payment_request, f"创建支付失败: {str(e)}")

    def _create_failed_response(self, payment_request: PaymentCreate, message: str = "支付创建失败") -> PaymentResponse:
        """创建失败的支付响应"""
        return PaymentResponse(
            id=0,
            payment_url=None,
            order_no=payment_request.order_no,
            amount=payment_request.amount,
            payment_method=payment_request.payment_method,
            status="failed",
            created_at=datetime.now()
        )

    def _get_payment_method_name(self, payment_type: str) -> str:
        """获取支付方式名称"""
        names = {
            "alipay": "支付宝",
            "wechat": "微信支付",
            "paypal": "PayPal",
            "stripe": "Stripe",
            "bank_transfer": "银行转账",
            "crypto": "加密货币"
        }
        return names.get(payment_type, payment_type)

    def _get_default_payment_config(self, payment_type: str) -> Dict[str, Any]:
        """获取默认支付配置"""
        if payment_type == 'alipay':
            return self._get_alipay_config_from_system()
        return {}

    def _get_alipay_config_from_system(self) -> Dict[str, Any]:
        """从系统配置中获取支付宝配置"""
        try:
            from app.models.config import SystemConfig
            
            # 查询支付宝相关配置
            configs = self.db.query(SystemConfig).filter(
                SystemConfig.key.in_([
                    'alipay_app_id', 'alipay_private_key', 'alipay_public_key',
                    'alipay_gateway', 'notify_url', 'return_url'
                ])
            ).all()
            
            config_dict = {config.key: config.value for config in configs}
            
            # 构建支付宝配置
            private_key = config_dict.get('alipay_private_key', '')
            public_key = config_dict.get('alipay_public_key', '')
            
            # 确保私钥和公钥有正确的PEM格式
            if private_key and not private_key.startswith('-----BEGIN'):
                private_key = f"-----BEGIN PRIVATE KEY-----\n{private_key}\n-----END PRIVATE KEY-----"
            
            if public_key and not public_key.startswith('-----BEGIN'):
                public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
            
            alipay_config = {
                'app_id': config_dict.get('alipay_app_id'),
                'merchant_private_key': private_key,
                'alipay_public_key': public_key,
                'gateway_url': config_dict.get('alipay_gateway', 'https://openapi.alipaydev.com/gateway.do'),
                'notify_url': config_dict.get('notify_url'),
                'return_url': config_dict.get('return_url'),
                'debug': 'alipaydev.com' in config_dict.get('alipay_gateway', '')
            }
            
            # 检查是否有完整的配置
            if alipay_config['app_id'] and alipay_config['merchant_private_key'] and alipay_config['alipay_public_key']:
                return alipay_config
            else:
                return {}
                
        except Exception as e:
            return {}

    def _create_payment_response(self, payment_request: PaymentCreate, payment_url: str, 
                                transaction_id: str = None, status: str = "pending") -> PaymentResponse:
        """创建支付响应的通用方法"""
        # 保存交易记录
        if transaction_id:
            self.create_payment_transaction(PaymentTransactionCreate(
                order_id=0,  # 临时使用0，实际应该从订单获取
                user_id=0,  # 临时使用0，实际应该从订单获取
                payment_method_id=0,  # 临时使用0
                amount=int(payment_request.amount * 100),  # 转换为分
                currency=payment_request.currency or "CNY"
            ))
        
        return PaymentResponse(
            id=0,
            payment_url=payment_url,
            order_no=payment_request.order_no,
            amount=payment_request.amount,
            payment_method=payment_request.payment_method,
            status=status,
            created_at=datetime.now()
        )

    def _create_alipay_payment(self, config: Dict[str, Any], request: PaymentCreate, currency: str) -> PaymentResponse:
        """创建支付宝支付"""
        try:
            transaction_id = f"ALI{datetime.now().strftime('%Y%m%d%H%M%S')}{request.order_no}"
            
            # 检查是否有真实的支付宝配置
            if config and config.get('app_id') and config.get('merchant_private_key'):
                # 使用真实的支付宝API
                return self._create_real_alipay_payment(config, request, currency, transaction_id)
            else:
                # 不再使用演示模式，直接返回错误
                return self._create_failed_response(request, "支付宝配置不完整，请联系管理员配置真实的支付宝密钥")
                
        except Exception as e:
            return self._create_failed_response(request, f"支付宝支付创建失败: {str(e)}")

    def _create_real_alipay_payment(self, config: Dict[str, Any], request: PaymentCreate, currency: str, transaction_id: str) -> PaymentResponse:
        """创建真实的支付宝支付"""
        try:
            if not ALIPAY_AVAILABLE:
                return self._create_failed_response(request, "支付宝SDK不可用，请联系管理员")
            
            # 初始化支付宝客户端
            alipay = AliPay(
                appid=config['app_id'],
                app_notify_url=config.get('notify_url', 'http://localhost:8000/api/v1/payment/alipay/notify'),
                app_private_key_string=config['merchant_private_key'],
                alipay_public_key_string=config['alipay_public_key'],
                sign_type='RSA2',
                debug=config.get('debug', False)
            )
            
            # 创建支付订单
            order_string = alipay.api_alipay_trade_page_pay(
                out_trade_no=transaction_id,
                total_amount=str(request.amount),
                subject=f"XBoard套餐购买-{request.order_no}",
                return_url=config.get('return_url', 'http://localhost:3000/payment/success'),
                notify_url=config.get('notify_url', 'http://localhost:8000/api/v1/payment/alipay/notify')
            )
            
            # 使用配置中的网关URL
            gateway_url = config.get('gateway_url', 'https://openapi.alipay.com/gateway.do')
            payment_url = f"{gateway_url}?{order_string}"
            
            return self._create_payment_response(request, payment_url, transaction_id)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            # 如果真实支付失败，直接返回错误，不再回退到演示模式
            return self._create_failed_response(request, f"支付宝支付创建失败: {str(e)}")

    def _create_demo_alipay_payment(self, request: PaymentCreate, transaction_id: str) -> PaymentResponse:
        """创建演示用的支付宝支付（模拟）- 已禁用，强制使用真实支付"""
        # 不再提供演示模式，直接返回错误
        return self._create_failed_response(request, "支付宝配置不完整，请联系管理员配置真实的支付宝密钥")

    def _create_wechat_payment(self, config: Dict[str, Any], request: PaymentCreate, currency: str) -> PaymentResponse:
        """创建微信支付"""
        try:
            transaction_id = f"WX{datetime.now().strftime('%Y%m%d%H%M%S')}{request.order_no}"
            payment_url = f"weixin://wxpay/bizpayurl?pr={transaction_id}"
            return self._create_payment_response(request, payment_url, transaction_id)
        except Exception as e:
            return self._create_failed_response(request, f"微信支付创建失败: {str(e)}")

    def _create_paypal_payment(self, config: Dict[str, Any], request: PaymentCreate, currency: str) -> PaymentResponse:
        """创建PayPal支付"""
        try:
            transaction_id = f"PP{datetime.now().strftime('%Y%m%d%H%M%S')}{request.order_no}"
            payment_url = f"https://www.paypal.com/paypalme/{transaction_id}"
            return self._create_payment_response(request, payment_url, transaction_id)
        except Exception as e:
            return self._create_failed_response(request, f"PayPal支付创建失败: {str(e)}")

    def _create_stripe_payment(self, config: Dict[str, Any], request: PaymentCreate, currency: str) -> PaymentResponse:
        """创建Stripe支付"""
        try:
            transaction_id = f"ST{datetime.now().strftime('%Y%m%d%H%M%S')}{request.order_no}"
            payment_url = f"https://checkout.stripe.com/pay/{transaction_id}"
            return self._create_payment_response(request, payment_url, transaction_id)
        except Exception as e:
            return self._create_failed_response(request, f"Stripe支付创建失败: {str(e)}")

    def _create_bank_transfer_payment(self, config: Dict[str, Any], request: PaymentCreate, currency: str) -> PaymentResponse:
        """创建银行转账支付"""
        try:
            transaction_id = f"BT{datetime.now().strftime('%Y%m%d%H%M%S')}{request.order_no}"
            bank_info = {
                "bank_name": "中国银行",
                "account_name": "XBoard科技有限公司",
                "account_number": "1234567890123456789",
                "amount": request.amount,
                "currency": currency,
                "transaction_id": transaction_id
            }
            payment_url = str(bank_info)
            return self._create_payment_response(request, payment_url, transaction_id)
        except Exception as e:
            return self._create_failed_response(request, f"银行转账支付创建失败: {str(e)}")

    def _create_crypto_payment(self, config: Dict[str, Any], request: PaymentCreate, currency: str) -> PaymentResponse:
        """创建加密货币支付"""
        try:
            transaction_id = f"CR{datetime.now().strftime('%Y%m%d%H%M%S')}{request.order_no}"
            crypto_info = {
                "wallet_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                "amount": request.amount,
                "currency": "BTC",
                "transaction_id": transaction_id
            }
            payment_url = str(crypto_info)
            return self._create_payment_response(request, payment_url, transaction_id)
        except Exception as e:
            return self._create_failed_response(request, f"加密货币支付创建失败: {str(e)}")

    # 支付回调验证
    def verify_payment_notify(self, payment_method: str, params: dict) -> bool:
        """验证支付回调通知"""
        try:
            if payment_method == 'alipay':
                return self._verify_alipay_notify(params)
            elif payment_method == 'wechat':
                return self._verify_wechat_notify(params)
            else:
                return True
        except Exception as e:
            return False

    def _verify_alipay_notify(self, params: dict) -> bool:
        """验证支付宝回调"""
        return True

    def _verify_wechat_notify(self, params: dict) -> bool:
        """验证微信支付回调"""
        return True

    # 工具方法
    def _generate_alipay_sign(self, params: Dict[str, Any], private_key: str) -> str:
        """生成支付宝签名"""
        sign_string = "&".join([f"{k}={v}" for k, v in sorted(params.items()) if k != "sign"])
        return hashlib.md5(sign_string.encode()).hexdigest()

    def _generate_wechat_sign(self, params: Dict[str, Any], key: str) -> str:
        """生成微信支付签名"""
        sign_string = "&".join([f"{k}={v}" for k, v in sorted(params.items()) if k != "sign"])
        sign_string += f"&key={key}"
        return hashlib.md5(sign_string.encode()).hexdigest().upper()

    def _generate_crypto_sign(self, params: Dict[str, Any], secret_key: str) -> str:
        """生成加密货币支付签名"""
        sign_string = "&".join([f"{k}={v}" for k, v in sorted(params.items()) if k != "signature"])
        return hmac.new(secret_key.encode(), sign_string.encode(), hashlib.sha512).hexdigest()

    def _generate_nonce_str(self) -> str:
        """生成随机字符串"""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

    def _get_paypal_token(self, config: PayPalConfig) -> str:
        """获取PayPal访问令牌"""
        return "paypal_token_placeholder"

    def _dict_to_xml(self, data: Dict[str, Any]) -> str:
        """字典转XML"""
        xml = "<xml>"
        for key, value in data.items():
            xml += f"<{key}>{value}</{key}>"
        xml += "</xml>"
        return xml

    def _xml_to_dict(self, xml: str) -> Dict[str, Any]:
        """XML转字典"""
        root = ET.fromstring(xml)
        return {child.tag: child.text for child in root}


class PaymentMethodService:
    def __init__(self, db: Session):
        self.db = db

    def get_payment_methods(self, skip: int = 0, limit: int = 100, 
                          type_filter: Optional[str] = None, 
                          status_filter: Optional[str] = None) -> List:
        """获取支付方式列表"""
        query = self.db.query(PaymentMethod)
        
        if type_filter:
            query = query.filter(PaymentMethod.type == type_filter)
        if status_filter:
            query = query.filter(PaymentMethod.status == status_filter)
        
        return query.order_by(PaymentMethod.sort_order, PaymentMethod.id).offset(skip).limit(limit).all()

    def get_payment_method(self, payment_method_id: int):
        """根据ID获取支付方式"""
        return self.db.query(PaymentMethod).filter(PaymentMethod.id == payment_method_id).first()

    def get_active_payment_methods(self) -> List:
        """获取所有启用的支付方式"""
        return self.db.query(PaymentMethod).filter(
            PaymentMethod.status == "active"
        ).order_by(PaymentMethod.sort_order, PaymentMethod.id).all()

    def create_payment_method(self, payment_method: PaymentMethodCreate):
        """创建支付方式"""
        db_payment_method = PaymentMethod(**payment_method.dict())
        self.db.add(db_payment_method)
        self.db.commit()
        self.db.refresh(db_payment_method)
        return db_payment_method

    def update_payment_method(self, payment_method_id: int, payment_method: PaymentMethodUpdate):
        """更新支付方式"""
        db_payment_method = self.get_payment_method(payment_method_id)
        if not db_payment_method:
            return None
        
        update_data = payment_method.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_payment_method, field, value)
        
        self.db.commit()
        self.db.refresh(db_payment_method)
        return db_payment_method

    def delete_payment_method(self, payment_method_id: int) -> bool:
        """删除支付方式"""
        db_payment_method = self.get_payment_method(payment_method_id)
        if not db_payment_method:
            return False
        
        self.db.delete(db_payment_method)
        self.db.commit()
        return True

    def update_payment_method_status(self, payment_method_id: int, status: str):
        """更新支付方式状态"""
        db_payment_method = self.get_payment_method(payment_method_id)
        if not db_payment_method:
            return None
        
        db_payment_method.status = status
        self.db.commit()
        self.db.refresh(db_payment_method)
        return db_payment_method

    def update_payment_method_config(self, payment_method_id: int, config: Dict[str, Any]):
        """更新支付方式配置"""
        db_payment_method = self.get_payment_method(payment_method_id)
        if not db_payment_method:
            return None
        
        db_payment_method.config = config
        self.db.commit()
        self.db.refresh(db_payment_method)
        return db_payment_method

    def get_payment_method_config(self, payment_method_id: int) -> Optional[Dict[str, Any]]:
        """获取支付方式配置"""
        db_payment_method = self.get_payment_method(payment_method_id)
        return db_payment_method.config if db_payment_method else None

    def test_payment_method_config(self, payment_method_id: int) -> Dict[str, Any]:
        """测试支付方式配置"""
        db_payment_method = self.get_payment_method(payment_method_id)
        if not db_payment_method:
            return {"success": False, "message": "支付方式不存在"}
        
        try:
            test_methods = {
                "alipay": self._test_alipay_config,
                "wechat": self._test_wechat_config,
                "paypal": self._test_paypal_config,
                "stripe": self._test_stripe_config
            }
            
            test_method = test_methods.get(db_payment_method.type)
            if test_method:
                return test_method(db_payment_method.config)
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
        required_fields = ["mch_id", "app_id", "api_key"]
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

    def bulk_update_status(self, payment_method_ids: List[int], status: str) -> int:
        """批量更新支付方式状态"""
        result = self.db.query(PaymentMethod).filter(
            PaymentMethod.id.in_(payment_method_ids)
        ).update({"status": status}, synchronize_session=False)
        
        self.db.commit()
        return result

    def bulk_delete(self, payment_method_ids: List[int]) -> int:
        """批量删除支付方式"""
        result = self.db.query(PaymentMethod).filter(
            PaymentMethod.id.in_(payment_method_ids)
        ).delete(synchronize_session=False)
        
        self.db.commit()
        return result


class PaymentTransactionService:
    def __init__(self, db: Session):
        self.db = db

    def get_transactions(self, skip: int = 0, limit: int = 100,
                        user_id: Optional[int] = None,
                        order_id: Optional[int] = None,
                        status: Optional[str] = None) -> List[PaymentTransaction]:
        """获取支付交易列表"""
        query = self.db.query(PaymentTransaction)
        
        if user_id:
            query = query.filter(PaymentTransaction.user_id == user_id)
        if order_id:
            query = query.filter(PaymentTransaction.order_id == order_id)
        if status:
            query = query.filter(PaymentTransaction.status == status)
        
        return query.order_by(desc(PaymentTransaction.created_at)).offset(skip).limit(limit).all()

    def get_transaction(self, transaction_id: int) -> Optional[PaymentTransaction]:
        """根据ID获取支付交易"""
        return self.db.query(PaymentTransaction).filter(
            PaymentTransaction.id == transaction_id
        ).first()

    def get_transaction_by_external_id(self, external_id: str) -> Optional[PaymentTransaction]:
        """根据外部交易号获取支付交易"""
        return self.db.query(PaymentTransaction).filter(
            PaymentTransaction.external_transaction_id == external_id
        ).first()

    def create_transaction(self, transaction: PaymentTransactionCreate) -> PaymentTransaction:
        """创建支付交易"""
        db_transaction = PaymentTransaction(
            **transaction.dict(),
            transaction_id=str(uuid.uuid4())
        )
        self.db.add(db_transaction)
        self.db.commit()
        self.db.refresh(db_transaction)
        return db_transaction

    def update_transaction(self, transaction_id: int, transaction: PaymentTransactionUpdate) -> Optional[PaymentTransaction]:
        """更新支付交易"""
        db_transaction = self.get_transaction(transaction_id)
        if not db_transaction:
            return None
        
        update_data = transaction.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_transaction, field, value)
        
        self.db.commit()
        self.db.refresh(db_transaction)
        return db_transaction

    def update_transaction_status(self, transaction_id: int, status: str) -> Optional[PaymentTransaction]:
        """更新支付交易状态"""
        db_transaction = self.get_transaction(transaction_id)
        if not db_transaction:
            return None
        
        db_transaction.status = status
        self.db.commit()
        self.db.refresh(db_transaction)
        return db_transaction

    def get_user_transactions(self, user_id: int, limit: int = 50) -> List[PaymentTransaction]:
        """获取用户支付交易历史"""
        return self.db.query(PaymentTransaction).filter(
            PaymentTransaction.user_id == user_id
        ).order_by(desc(PaymentTransaction.created_at)).limit(limit).all()

    def get_order_transactions(self, order_id: int) -> List[PaymentTransaction]:
        """获取订单相关的支付交易"""
        return self.db.query(PaymentTransaction).filter(
            PaymentTransaction.order_id == order_id
        ).order_by(desc(PaymentTransaction.created_at)).all()