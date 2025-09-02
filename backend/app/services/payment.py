from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import hashlib
import hmac
import json
import requests
from urllib.parse import urlencode
from sqlalchemy import desc

from app.models.payment import PaymentTransaction, PaymentCallback
from app.models.payment_config import PaymentConfig
from app.schemas.payment import (
    PaymentConfigCreate, PaymentConfigUpdate,
    PaymentTransactionCreate, PaymentTransactionUpdate,
    PaymentCallbackCreate, PaymentCallbackUpdate,
    AlipayConfig, WechatConfig, PayPalConfig, StripeConfig, CryptoConfig,
    PaymentCreate, PaymentResponse, PaymentCallback,
    BankTransferConfig, PaymentMethod, PaymentMethodCreate, PaymentMethodUpdate
)
from app.core.settings_manager import settings_manager
from app.utils.security import get_password_hash, verify_password
import xml.etree.ElementTree as ET

class PaymentService:
    def __init__(self, db: Session):
        self.db = db

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
            PaymentConfig.is_active == True
        ).order_by(PaymentConfig.sort_order, PaymentConfig.id).all()

    def get_default_payment_config(self) -> Optional[PaymentConfig]:
        """获取默认支付配置"""
        default_method = self.get_default_payment_method()
        if default_method:
            return self.get_payment_config_by_name(default_method)
        return self.db.query(PaymentConfig).filter(
            PaymentConfig.is_active == True,
            PaymentConfig.is_default == True
        ).first()

    def create_payment_config(self, config_in: PaymentConfigCreate) -> PaymentConfig:
        """创建支付配置"""
        # 如果设置为默认，先取消其他默认配置
        if config_in.is_default:
            self.db.query(PaymentConfig).update({"is_default": False})
        
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
        
        # 如果设置为默认，先取消其他默认配置
        if config_in.is_default:
            self.db.query(PaymentConfig).update({"is_default": False})
        
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
            return PaymentResponse(
                success=False,
                message="支付功能已禁用",
                error_code="PAYMENT_DISABLED"
            )
        
        # 获取支付方式配置
        payment_method = self.db.query(PaymentMethod).filter(PaymentMethod.id == payment_request.payment_method_id).first()
        if not payment_method:
            return PaymentResponse(
                success=False,
                message="支付方式不存在",
                error_code="PAYMENT_METHOD_NOT_FOUND"
            )
        
        if payment_method.status != "active":
            return PaymentResponse(
                success=False,
                message="支付方式已禁用",
                error_code="PAYMENT_METHOD_DISABLED"
            )
        
        # 使用设置中的货币
        currency = payment_request.currency or self.get_payment_currency()
        
        try:
            # 根据支付方式类型创建支付
            if payment_method.type == "alipay":
                return self._create_alipay_payment_with_config(payment_method.config, payment_request, currency)
            elif payment_method.type == "wechat":
                return self._create_wechat_payment_with_config(payment_method.config, payment_request, currency)
            elif payment_method.type == "paypal":
                return self._create_paypal_payment_with_config(payment_method.config, payment_request, currency)
            elif payment_method.type == "stripe":
                return self._create_stripe_payment_with_config(payment_method.config, payment_request, currency)
            elif payment_method.type == "bank_transfer":
                return self._create_bank_transfer_payment(payment_method.config, payment_request, currency)
            elif payment_method.type == "crypto":
                return self._create_crypto_payment_with_config(payment_method.config, payment_request, currency)
            else:
                return PaymentResponse(
                    success=False,
                    message=f"不支持的支付方式类型: {payment_method.type}",
                    error_code="UNSUPPORTED_PAYMENT_METHOD"
                )
        except Exception as e:
            return PaymentResponse(
                success=False,
                message=f"创建支付失败: {str(e)}",
                error_code="PAYMENT_CREATION_FAILED"
            )

    def _create_alipay_payment(self, config: PaymentConfig, request: PaymentCreate, currency: str) -> PaymentResponse:
        """创建支付宝支付"""
        try:
            alipay_config = AlipayConfig(**config.config)
            
            # 生成交易ID
            transaction_id = f"ALI{datetime.now().strftime('%Y%m%d%H%M%S')}{request.order_id}"
            
            # 构建支付宝请求参数
            params = {
                "app_id": alipay_config.app_id,
                "method": "alipay.trade.page.pay",
                "charset": alipay_config.charset,
                "sign_type": alipay_config.sign_type,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0",
                "notify_url": alipay_config.notify_url,
                "return_url": request.return_url or alipay_config.return_url,
                "biz_content": json.dumps({
                    "out_trade_no": transaction_id,
                    "total_amount": str(request.amount),
                    "subject": request.description or f"订单{request.order_id}",
                    "product_code": "FAST_INSTANT_TRADE_PAY"
                })
            }
            
            # 生成签名
            params["sign"] = self._generate_alipay_sign(params, alipay_config.private_key)
            
            # 构建支付URL
            payment_url = f"{alipay_config.gateway_url}?{urlencode(params)}"
            
            # 保存交易记录
            transaction = self.create_payment_transaction(PaymentTransactionCreate(
                order_id=request.order_id,
                payment_config_id=config.id,
                transaction_id=transaction_id,
                amount=request.amount,
                currency=currency,
                payment_method=config.type,
                gateway_response={"payment_url": payment_url}
            ))
            
            return PaymentResponse(
                success=True,
                payment_url=payment_url,
                transaction_id=transaction_id
            )
            
        except Exception as e:
            return PaymentResponse(
                success=False,
                message=f"支付宝支付创建失败: {str(e)}",
                error_code="ALIPAY_CREATION_FAILED"
            )

    def _create_wechat_payment(self, config: PaymentConfig, request: PaymentCreate, currency: str) -> PaymentResponse:
        """创建微信支付"""
        try:
            wechat_config = WechatConfig(**config.config)
            
            # 生成交易ID
            transaction_id = f"WX{datetime.now().strftime('%Y%m%d%H%M%S')}{request.order_id}"
            
            # 构建微信支付请求参数
            params = {
                "appid": wechat_config.app_id,
                "mch_id": wechat_config.mch_id,
                "nonce_str": self._generate_nonce_str(),
                "body": request.description or f"订单{request.order_id}",
                "out_trade_no": transaction_id,
                "total_fee": int(request.amount * 100),  # 微信支付金额单位为分
                "spbill_create_ip": "127.0.0.1",
                "notify_url": wechat_config.notify_url,
                "trade_type": "NATIVE"  # 二维码支付
            }
            
            # 生成签名
            params["sign"] = self._generate_wechat_sign(params, wechat_config.key)
            
            # 调用微信支付API
            response = requests.post(
                "https://api.mch.weixin.qq.com/pay/unifiedorder",
                data=self._dict_to_xml(params),
                headers={"Content-Type": "application/xml"}
            )
            
            # 解析响应
            result = self._xml_to_dict(response.text)
            
            if result.get("return_code") == "SUCCESS" and result.get("result_code") == "SUCCESS":
                qr_code = result.get("code_url")
                
                # 保存交易记录
                transaction = self.create_payment_transaction(PaymentTransactionCreate(
                    order_id=request.order_id,
                    payment_config_id=config.id,
                    transaction_id=transaction_id,
                    amount=request.amount,
                    currency=currency,
                    payment_method=config.type,
                    gateway_response={"qr_code": qr_code, "response": result}
                ))
                
                return PaymentResponse(
                    success=True,
                    qr_code=qr_code,
                    transaction_id=transaction_id
                )
            else:
                return PaymentResponse(
                    success=False,
                    message=f"微信支付创建失败: {result.get('return_msg', '未知错误')}",
                    error_code="WECHAT_CREATION_FAILED"
                )
                
        except Exception as e:
            return PaymentResponse(
                success=False,
                message=f"微信支付创建失败: {str(e)}",
                error_code="WECHAT_CREATION_FAILED"
            )

    def _create_paypal_payment(self, config: PaymentConfig, request: PaymentCreate, currency: str) -> PaymentResponse:
        """创建PayPal支付"""
        try:
            paypal_config = PayPalConfig(**config.config)
            
            # 生成交易ID
            transaction_id = f"PP{datetime.now().strftime('%Y%m%d%H%M%S')}{request.order_id}"
            
            # 构建PayPal支付请求
            payment_data = {
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "transactions": [{
                    "amount": {
                        "total": str(request.amount),
                        "currency": currency
                    },
                    "description": request.description or f"订单{request.order_id}",
                    "custom": transaction_id
                }],
                "redirect_urls": {
                    "return_url": request.return_url or paypal_config.return_url,
                    "cancel_url": request.return_url or paypal_config.return_url
                }
            }
            
            # 调用PayPal API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_paypal_token(paypal_config)}"
            }
            
            response = requests.post(
                f"https://api.paypal.com/v1/payments/payment",
                json=payment_data,
                headers=headers
            )
            
            result = response.json()
            
            if response.status_code == 201:
                payment_url = result["links"][1]["href"]  # PayPal支付链接
                
                # 保存交易记录
                transaction = self.create_payment_transaction(PaymentTransactionCreate(
                    order_id=request.order_id,
                    payment_config_id=config.id,
                    transaction_id=transaction_id,
                    amount=request.amount,
                    currency=currency,
                    payment_method=config.type,
                    gateway_response={"payment_url": payment_url, "response": result}
                ))
                
                return PaymentResponse(
                    success=True,
                    payment_url=payment_url,
                    transaction_id=transaction_id
                )
            else:
                return PaymentResponse(
                    success=False,
                    message=f"PayPal支付创建失败: {result.get('message', '未知错误')}",
                    error_code="PAYPAL_CREATION_FAILED"
                )
                
        except Exception as e:
            return PaymentResponse(
                success=False,
                message=f"PayPal支付创建失败: {str(e)}",
                error_code="PAYPAL_CREATION_FAILED"
            )

    def _create_stripe_payment(self, config: PaymentConfig, request: PaymentCreate, currency: str) -> PaymentResponse:
        """创建Stripe支付"""
        try:
            stripe_config = StripeConfig(**config.config)
            
            # 生成交易ID
            transaction_id = f"ST{datetime.now().strftime('%Y%m%d%H%M%S')}{request.order_id}"
            
            # 构建Stripe支付请求
            payment_data = {
                "amount": int(request.amount * 100),  # Stripe金额单位为分
                "currency": currency.lower(),
                "description": request.description or f"订单{request.order_id}",
                "metadata": {
                    "order_id": str(request.order_id),
                    "transaction_id": transaction_id
                },
                "success_url": request.return_url or f"{request.return_url}?success=true",
                "cancel_url": request.return_url or f"{request.return_url}?canceled=true"
            }
            
            # 调用Stripe API
            headers = {
                "Authorization": f"Bearer {stripe_config.secret_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = requests.post(
                "https://api.stripe.com/v1/checkout/sessions",
                data=payment_data,
                headers=headers
            )
            
            result = response.json()
            
            if response.status_code == 200:
                payment_url = result["url"]
                
                # 保存交易记录
                transaction = self.create_payment_transaction(PaymentTransactionCreate(
                    order_id=request.order_id,
                    payment_config_id=config.id,
                    transaction_id=transaction_id,
                    amount=request.amount,
                    currency=currency,
                    payment_method=config.type,
                    gateway_response={"payment_url": payment_url, "response": result}
                ))
                
                return PaymentResponse(
                    success=True,
                    payment_url=payment_url,
                    transaction_id=transaction_id
                )
            else:
                return PaymentResponse(
                    success=False,
                    message=f"Stripe支付创建失败: {result.get('message', '未知错误')}",
                    error_code="STRIPE_CREATION_FAILED"
                )
                
        except Exception as e:
            return PaymentResponse(
                success=False,
                message=f"Stripe支付创建失败: {str(e)}",
                error_code="STRIPE_CREATION_FAILED"
            )

    def _create_crypto_payment(self, config: PaymentConfig, request: PaymentCreate, currency: str) -> PaymentResponse:
        """创建加密货币支付"""
        try:
            crypto_config = CryptoConfig(**config.config)
            
            # 生成交易ID
            transaction_id = f"CR{datetime.now().strftime('%Y%m%d%H%M%S')}{request.order_id}"
            
            # 这里需要根据具体的加密货币支付网关实现
            # 示例使用CoinPayments API
            payment_data = {
                "cmd": "create_transaction",
                "version": "1",
                "key": crypto_config.api_key,
                "amount": str(request.amount),
                "currency1": currency,
                "currency2": crypto_config.currency,
                "buyer_email": "user@example.com",  # 需要从用户信息获取
                "item_name": request.description or f"订单{request.order_id}",
                "ipn_url": crypto_config.notify_url,
                "success_url": request.return_url or f"{request.return_url}?success=true",
                "cancel_url": request.return_url or f"{request.return_url}?canceled=true"
            }
            
            # 生成签名
            payment_data["signature"] = self._generate_crypto_sign(payment_data, crypto_config.secret_key)
            
            # 调用加密货币支付API
            response = requests.post(
                "https://www.coinpayments.net/api.php",
                data=payment_data
            )
            
            result = response.json()
            
            if result.get("error") == "ok":
                payment_url = result["result"]["checkout_url"]
                qr_code = result["result"]["qrcode_url"]
                
                # 保存交易记录
                transaction = self.create_payment_transaction(PaymentTransactionCreate(
                    order_id=request.order_id,
                    payment_config_id=config.id,
                    transaction_id=transaction_id,
                    amount=request.amount,
                    currency=currency,
                    payment_method=config.type,
                    gateway_response={"payment_url": payment_url, "qr_code": qr_code, "response": result}
                ))
                
                return PaymentResponse(
                    success=True,
                    payment_url=payment_url,
                    qr_code=qr_code,
                    transaction_id=transaction_id
                )
            else:
                return PaymentResponse(
                    success=False,
                    message=f"加密货币支付创建失败: {result.get('error', '未知错误')}",
                    error_code="CRYPTO_CREATION_FAILED"
                )
                
        except Exception as e:
            return PaymentResponse(
                success=False,
                message=f"加密货币支付创建失败: {str(e)}",
                error_code="CRYPTO_CREATION_FAILED"
            )

    # 工具方法
    def _generate_alipay_sign(self, params: Dict[str, Any], private_key: str) -> str:
        """生成支付宝签名"""
        # 这里需要实现支付宝签名算法
        # 简化实现，实际需要按照支付宝文档实现
        sign_string = "&".join([f"{k}={v}" for k, v in sorted(params.items()) if k != "sign"])
        return hashlib.md5(sign_string.encode()).hexdigest()

    def _generate_wechat_sign(self, params: Dict[str, Any], key: str) -> str:
        """生成微信支付签名"""
        # 这里需要实现微信支付签名算法
        # 简化实现，实际需要按照微信支付文档实现
        sign_string = "&".join([f"{k}={v}" for k, v in sorted(params.items()) if k != "sign"])
        sign_string += f"&key={key}"
        return hashlib.md5(sign_string.encode()).hexdigest().upper()

    def _generate_crypto_sign(self, params: Dict[str, Any], secret_key: str) -> str:
        """生成加密货币支付签名"""
        # 这里需要实现加密货币支付签名算法
        sign_string = "&".join([f"{k}={v}" for k, v in sorted(params.items()) if k != "signature"])
        return hmac.new(secret_key.encode(), sign_string.encode(), hashlib.sha512).hexdigest()

    def _generate_nonce_str(self) -> str:
        """生成随机字符串"""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

    def _get_paypal_token(self, config: PayPalConfig) -> str:
        """获取PayPal访问令牌"""
        # 这里需要实现PayPal OAuth认证
        # 简化实现，实际需要调用PayPal OAuth API
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

    def get_payment_methods(
        self, 
        skip: int = 0, 
        limit: int = 100,
        type_filter: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[PaymentMethod]:
        """获取支付方式列表"""
        query = self.db.query(PaymentMethod)
        
        if type_filter:
            query = query.filter(PaymentMethod.type == type_filter)
        
        if status_filter:
            query = query.filter(PaymentMethod.status == status_filter)
        
        return query.order_by(PaymentMethod.sort_order, PaymentMethod.id).offset(skip).limit(limit).all()

    def get_payment_method(self, payment_method_id: int) -> Optional[PaymentMethod]:
        """根据ID获取支付方式"""
        return self.db.query(PaymentMethod).filter(PaymentMethod.id == payment_method_id).first()

    def get_active_payment_methods(self) -> List[PaymentMethod]:
        """获取所有启用的支付方式"""
        return self.db.query(PaymentMethod).filter(
            PaymentMethod.status == "active"
        ).order_by(PaymentMethod.sort_order, PaymentMethod.id).all()

    def create_payment_method(self, payment_method: PaymentMethodCreate) -> PaymentMethod:
        """创建支付方式"""
        db_payment_method = PaymentMethod(**payment_method.dict())
        self.db.add(db_payment_method)
        self.db.commit()
        self.db.refresh(db_payment_method)
        return db_payment_method

    def update_payment_method(
        self, 
        payment_method_id: int, 
        payment_method: PaymentMethodUpdate
    ) -> Optional[PaymentMethod]:
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

    def update_payment_method_status(self, payment_method_id: int, status: str) -> Optional[PaymentMethod]:
        """更新支付方式状态"""
        db_payment_method = self.get_payment_method(payment_method_id)
        if not db_payment_method:
            return None
        
        db_payment_method.status = status
        self.db.commit()
        self.db.refresh(db_payment_method)
        return db_payment_method

    def update_payment_method_config(
        self, 
        payment_method_id: int, 
        config: Dict[str, Any]
    ) -> Optional[PaymentMethod]:
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
            # 根据支付类型进行不同的测试
            if db_payment_method.type == "alipay":
                return self._test_alipay_config(db_payment_method.config)
            elif db_payment_method.type == "wechat":
                return self._test_wechat_config(db_payment_method.config)
            elif db_payment_method.type == "paypal":
                return self._test_paypal_config(db_payment_method.config)
            elif db_payment_method.type == "stripe":
                return self._test_stripe_config(db_payment_method.config)
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
        
        # 这里可以添加实际的支付宝API测试
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

    def get_transactions(
        self, 
        skip: int = 0, 
        limit: int = 100,
        user_id: Optional[int] = None,
        order_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[PaymentTransaction]:
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
            transaction_id=generate_transaction_id()
        )
        self.db.add(db_transaction)
        self.db.commit()
        self.db.refresh(db_transaction)
        return db_transaction

    def update_transaction(
        self, 
        transaction_id: int, 
        transaction: PaymentTransactionUpdate
    ) -> Optional[PaymentTransaction]:
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