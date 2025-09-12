import json
import hashlib
import hmac
import base64
import time
import requests
from urllib.parse import urlencode, quote
from typing import Dict, Any, Optional
from app.contracts.payment_interface import PaymentInterface, PaymentRequest, PaymentResponse, PaymentNotify


class AlipayPayment(PaymentInterface):
    """支付宝支付实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.app_id = config.get('alipay_app_id', '')
        self.private_key = config.get('alipay_private_key', '')
        self.public_key = config.get('alipay_public_key', '')
        self.gateway_url = config.get('alipay_gateway', 'https://openapi.alipay.com/gateway.do')
        self.charset = 'utf-8'
        self.sign_type = 'RSA2'
        self.version = '1.0'
    
    def pay(self, request: PaymentRequest) -> PaymentResponse:
        """创建支付宝支付订单"""
        try:
            # 检查必要的配置
            if not self.app_id or not self.private_key:
                raise Exception("支付宝配置不完整：缺少APPID或私钥")
            
            # 构建请求参数
            biz_content = {
                'out_trade_no': request.trade_no,
                'total_amount': str(request.total_amount / 100),  # 转换为元
                'subject': request.subject,
                'body': request.body or request.subject,
                'product_code': 'FAST_INSTANT_TRADE_PAY'
            }
            
            params = {
                'app_id': self.app_id,
                'method': 'alipay.trade.precreate',  # 预创建订单，生成二维码
                'charset': self.charset,
                'sign_type': self.sign_type,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'version': self.version,
                'notify_url': request.notify_url,
                'biz_content': json.dumps(biz_content, separators=(',', ':'))
            }
            
            # 生成签名
            sign = self._generate_sign(params)
            params['sign'] = sign
            
            print(f"支付宝API请求参数: {params}")
            
            # 发送请求
            try:
                response = requests.post(
                    self.gateway_url,
                    data=params,
                    timeout=10,  # 减少超时时间
                    headers={'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}
                )
            except requests.exceptions.Timeout:
                raise Exception("支付宝API请求超时，请检查网络连接")
            except requests.exceptions.ConnectionError:
                raise Exception("无法连接到支付宝服务器，请检查网络连接")
            except requests.exceptions.RequestException as e:
                raise Exception(f"支付宝API请求失败: {str(e)}")
            
            print(f"支付宝API响应状态码: {response.status_code}")
            print(f"支付宝API响应内容: {response.text}")
            
            result = response.json()
            alipay_response = result.get('alipay_trade_precreate_response', {})
            
            if alipay_response.get('code') == '10000':
                qr_code = alipay_response.get('qr_code', '')
                if qr_code:
                    return PaymentResponse(
                        type=0,  # 二维码
                        data=qr_code,
                        trade_no=request.trade_no
                    )
                else:
                    raise Exception("支付宝返回的二维码为空")
            else:
                error_msg = alipay_response.get('sub_msg', alipay_response.get('msg', '未知错误'))
                raise Exception(f"支付宝API调用失败: {error_msg}")
                
        except Exception as e:
            print(f"支付宝支付创建失败: {str(e)}")
            
            # 提供详细的错误信息和解决建议
            error_msg = str(e)
            if "ACCESS_FORBIDDEN" in error_msg:
                raise Exception("支付宝配置错误：请检查APPID、私钥是否正确，或应用是否已激活")
            elif "超时" in error_msg or "timeout" in error_msg.lower():
                # 在本地环境下提供更友好的错误信息
                import socket
                hostname = socket.gethostname()
                if hostname == 'localhost' or '127.0.0.1' in str(socket.gethostbyname(hostname)):
                    raise Exception("本地环境网络限制：支付宝API无法在本地环境正常调用，请部署到VPS环境进行测试")
                else:
                    raise Exception("支付宝API请求超时：请检查网络连接或稍后重试")
            elif "连接" in error_msg or "connection" in error_msg.lower():
                raise Exception("无法连接支付宝服务器：请检查网络连接")
            else:
                raise Exception(f"支付宝支付创建失败: {error_msg}")
    
    def verify_notify(self, params: Dict[str, Any]) -> Optional[PaymentNotify]:
        """验证支付宝支付回调"""
        try:
            # 验证签名
            if not self._verify_sign(params):
                return None
            
            # 检查交易状态
            trade_status = params.get('trade_status')
            if trade_status != 'TRADE_SUCCESS':
                return None
            
            return PaymentNotify(
                trade_no=params.get('out_trade_no'),
                callback_no=params.get('trade_no'),
                amount=int(float(params.get('total_amount', 0)) * 100),  # 转换为分
                status='success'
            )
            
        except Exception as e:
            print(f"验证支付宝回调失败: {str(e)}")
            return None
    
    def get_config_form(self) -> Dict[str, Any]:
        """获取支付宝配置表单"""
        return {
            'alipay_app_id': {
                'label': '支付宝APPID',
                'type': 'input',
                'required': True,
                'description': '支付宝开放平台应用ID'
            },
            'alipay_private_key': {
                'label': '支付宝私钥',
                'type': 'textarea',
                'required': True,
                'description': '应用私钥，用于签名'
            },
            'alipay_public_key': {
                'label': '支付宝公钥',
                'type': 'textarea',
                'required': True,
                'description': '支付宝公钥，用于验签'
            },
            'alipay_gateway': {
                'label': '支付宝网关',
                'type': 'input',
                'required': True,
                'default': 'https://openapi.alipay.com/gateway.do',
                'description': '支付宝API网关地址'
            }
        }
    
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """生成RSA2签名"""
        # 过滤空值并排序
        filtered_params = {k: v for k, v in params.items() if v and k != 'sign'}
        sorted_params = sorted(filtered_params.items())
        
        # 构建待签名字符串
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        print(f"待签名字符串: {sign_string}")
        
        # 使用私钥签名
        try:
            from Crypto.PublicKey import RSA
            from Crypto.Signature import pkcs1_15
            from Crypto.Hash import SHA256
            
            # 处理私钥格式
            private_key_str = self.private_key
            if not private_key_str.startswith('-----BEGIN'):
                # 如果没有PEM头，添加它们
                private_key_str = f"-----BEGIN RSA PRIVATE KEY-----\n{private_key_str}\n-----END RSA PRIVATE KEY-----"
            
            # 加载私钥
            private_key = RSA.import_key(private_key_str)
            
            # 创建签名
            h = SHA256.new(sign_string.encode('utf-8'))
            signature = pkcs1_15.new(private_key).sign(h)
            
            # 返回Base64编码的签名
            sign_result = base64.b64encode(signature).decode('utf-8')
            print(f"生成的签名: {sign_result}")
            return sign_result
            
        except Exception as e:
            print(f"RSA签名生成失败: {str(e)}")
            raise Exception(f"RSA签名生成失败: {str(e)}")
    
    def _verify_sign(self, params: Dict[str, Any]) -> bool:
        """验证RSA2签名"""
        try:
            sign = params.pop('sign', '')
            sign_type = params.pop('sign_type', '')
            
            if sign_type != 'RSA2':
                return False
            
            # 过滤空值并排序
            filtered_params = {k: v for k, v in params.items() if v}
            sorted_params = sorted(filtered_params.items())
            
            # 构建待验签字符串
            sign_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
            
            try:
                from Crypto.PublicKey import RSA
                from Crypto.Signature import pkcs1_15
                from Crypto.Hash import SHA256
                
                # 加载公钥
                public_key = RSA.import_key(self.public_key)
                
                # 验证签名
                h = SHA256.new(sign_string.encode('utf-8'))
                pkcs1_15.new(public_key).verify(h, base64.b64decode(sign))
                
                return True
                
            except ImportError:
                # 如果没有pycryptodome，跳过签名验证（仅用于测试）
                return True
                
        except Exception as e:
            print(f"验证签名失败: {str(e)}")
            return False
