from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.contracts.payment_interface import PaymentInterface, PaymentRequest, PaymentResponse, PaymentNotify
from app.payments.alipay import AlipayPayment
from app.payments.wechat import WechatPayment
from app.payments.paypal import PaypalPayment
from app.payments.stripe import StripePayment
from app.payments.bank_transfer import BankTransferPayment
from app.models.payment import PaymentTransaction
from app.models.order import Order
from app.core.database import get_db
import uuid
import time


class PaymentService:
    """支付服务管理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.payment_methods = {
            'alipay': AlipayPayment,
            'wechat': WechatPayment,
            'paypal': PaypalPayment,
            'stripe': StripePayment,
            'bank_transfer': BankTransferPayment
        }
    
    def get_payment_config(self) -> Dict[str, Any]:
        """获取支付配置"""
        from app.models.config import SystemConfig
        configs = self.db.query(SystemConfig).filter(
            SystemConfig.category == 'payment'
        ).all()
        
        config_dict = {}
        for config in configs:
            config_dict[config.key] = config.value
        
        return config_dict
    
    def get_available_payment_methods(self) -> List[Dict[str, Any]]:
        """获取可用的支付方式"""
        config = self.get_payment_config()
        available_methods = []
        
        # 检查支付宝
        if (config.get('alipay_app_id') and 
            config.get('alipay_private_key') and 
            config.get('alipay_public_key')):
            available_methods.append({
                'key': 'alipay',
                'name': '支付宝',
                'icon': 'alipay',
                'description': '使用支付宝扫码支付'
            })
        
        # 检查微信支付
        if (config.get('wechat_app_id') and 
            config.get('wechat_mch_id') and 
            config.get('wechat_api_key')):
            available_methods.append({
                'key': 'wechat',
                'name': '微信支付',
                'icon': 'wechat',
                'description': '使用微信扫码支付'
            })
        
        # 检查PayPal
        if (config.get('paypal_client_id') and 
            config.get('paypal_secret')):
            available_methods.append({
                'key': 'paypal',
                'name': 'PayPal',
                'icon': 'paypal',
                'description': '使用PayPal在线支付'
            })
        
        # 检查Stripe
        if (config.get('stripe_publishable_key') and 
            config.get('stripe_secret_key')):
            available_methods.append({
                'key': 'stripe',
                'name': 'Stripe',
                'icon': 'stripe',
                'description': '使用Stripe信用卡支付'
            })
        
        # 检查银行转账
        if (config.get('bank_name') and 
            config.get('bank_account') and 
            config.get('account_holder')):
            available_methods.append({
                'key': 'bank_transfer',
                'name': '银行转账',
                'icon': 'bank',
                'description': '银行转账支付'
            })
        
        return available_methods
    
    def create_payment(self, order: Order, payment_method: str) -> PaymentResponse:
        """创建支付订单"""
        try:
            # 获取支付配置
            config = self.get_payment_config()
            
            # 检查支付方式是否可用
            if payment_method not in self.payment_methods:
                raise Exception(f"不支持的支付方式: {payment_method}")
            
            # 创建支付实例
            payment_class = self.payment_methods[payment_method]
            payment_instance = payment_class(config)
            
            # 生成交易号
            trade_no = f"{payment_method}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # 获取套餐信息
            from app.models.package import Package
            package = self.db.query(Package).filter(Package.id == order.package_id).first()
            package_name = package.name if package else "未知套餐"
            package_duration = package.duration_days if package else 30
            
            # 构建支付请求
            payment_request = PaymentRequest(
                trade_no=trade_no,
                total_amount=int(order.amount * 100),  # 转换为分
                subject=f"订阅套餐 - {package_name}",
                body=f"购买{package_duration}天订阅套餐",
                notify_url=config.get('notify_url', ''),
                return_url=config.get('return_url', ''),
                user_id=order.user_id
            )
            
            # 创建支付
            payment_response = payment_instance.pay(payment_request)
            
            # 保存支付记录
            from datetime import datetime
            payment_transaction = PaymentTransaction(
                order_id=order.id,
                user_id=order.user_id,
                payment_method_id=1,  # 临时设置
                amount=int(order.amount * 100),  # 转换为分
                currency=config.get('currency', 'CNY'),
                status='pending',
                payment_data={
                    'method': payment_method,
                    'trade_no': trade_no,
                    'payment_url': payment_response.data,
                    'payment_type': payment_response.type
                },
                created_at=datetime.now()
            )
            
            self.db.add(payment_transaction)
            self.db.commit()
            
            return payment_response
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"创建支付订单失败: {str(e)}")
    
    def verify_payment_notify(self, payment_method: str, params: Dict[str, Any]) -> Optional[PaymentNotify]:
        """验证支付回调"""
        try:
            # 获取支付配置
            config = self.get_payment_config()
            
            # 检查支付方式是否可用
            if payment_method not in self.payment_methods:
                return None
            
            # 创建支付实例
            payment_class = self.payment_methods[payment_method]
            payment_instance = payment_class(config)
            
            # 验证回调
            notify = payment_instance.verify_notify(params)
            
            if notify:
                # 更新支付记录
                payment_transaction = self.db.query(PaymentTransaction).filter(
                    PaymentTransaction.payment_data['trade_no'].astext == notify.trade_no
                ).first()
                
                if payment_transaction:
                    payment_transaction.status = 'completed'
                    payment_transaction.payment_data['callback_no'] = notify.callback_no
                    payment_transaction.payment_data['notify_amount'] = notify.amount
                    payment_transaction.updated_at = datetime.now()
                    
                    # 更新订单状态
                    order = self.db.query(Order).filter(
                        Order.id == payment_transaction.order_id
                    ).first()
                    
                    if order:
                        order.status = 'paid'
                        order.payment_time = datetime.now()
                        
                        # 处理订阅和设备数量
                        from app.services.subscription_manager import SubscriptionManager
                        subscription_manager = SubscriptionManager(self.db)
                        subscription_manager.process_paid_order(order)
                    
                    self.db.commit()
            
            return notify
            
        except Exception as e:
            self.db.rollback()
            print(f"验证支付回调失败: {str(e)}")
            return None
    
    def get_payment_config_form(self, payment_method: str) -> Dict[str, Any]:
        """获取支付方式配置表单"""
        try:
            if payment_method not in self.payment_methods:
                return {}
            
            payment_class = self.payment_methods[payment_method]
            payment_instance = payment_class({})
            
            return payment_instance.get_config_form()
            
        except Exception as e:
            print(f"获取支付配置表单失败: {str(e)}")
            return {}
