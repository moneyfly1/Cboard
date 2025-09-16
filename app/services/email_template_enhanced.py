"""
增强版邮件模板服务
使用中性词汇，避免敏感关键词
"""

from datetime import datetime
from typing import Dict, Any, Optional
from app.core.domain_config import get_domain_config


class EmailTemplateEnhanced:
    """增强版邮件模板类"""
    
    @staticmethod
    def _get_base_url(request=None, db=None) -> str:
        """获取基础URL"""
        domain_config = get_domain_config()
        return domain_config.get_email_base_url(request, db)
    
    @staticmethod
    def get_base_template(title: str, content: str, footer_text: str = '') -> str:
        """基础邮件模板"""
        current_year = datetime.now().year
        site_name = "网络服务"
        
        return f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            background-color: #f4f4f4;
            color: #333;
        }}
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 300;
        }}
        .header .subtitle {{
            margin: 10px 0 0 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .content h2 {{
            color: #333;
            font-size: 24px;
            margin-bottom: 20px;
            font-weight: 400;
        }}
        .content p {{
            line-height: 1.6;
            margin-bottom: 16px;
            color: #555;
        }}
        .info-box {{
            background-color: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .info-table th,
        .info-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }}
        .info-table th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
            width: 30%;
        }}
        .btn {{
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 500;
            margin: 20px 0;
            transition: all 0.3s ease;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}
        .warning-box {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 15px;
            margin: 20px 0;
            color: #856404;
        }}
        .success-box {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 4px;
            padding: 15px;
            margin: 20px 0;
            color: #155724;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e9ecef;
        }}
        .footer p {{
            margin: 5px 0;
            color: #6c757d;
            font-size: 14px;
        }}
        .url-box {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
            word-break: break-all;
            font-family: monospace;
            color: #667eea;
        }}
        .url-list {{
            margin: 15px 0;
        }}
        .url-item {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #667eea;
        }}
        .url-item strong {{
            color: #333;
            font-size: 14px;
            display: block;
            margin-bottom: 8px;
        }}
        .url-code {{
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 10px;
            margin: 5px 0;
            word-break: break-all;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #495057;
            display: block;
            line-height: 1.4;
        }}
        @media only screen and (max-width: 600px) {{
            .email-container {{
                width: 100% !important;
            }}
            .content {{
                padding: 20px !important;
            }}
            .header {{
                padding: 20px !important;
            }}
            .header h1 {{
                font-size: 24px !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>{site_name}</h1>
            <p class="subtitle">{title}</p>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p><strong>{site_name}</strong></p>
            <p>{footer_text or '感谢您选择我们的服务'}</p>
            <p style="font-size: 12px; color: #999;">此邮件由系统自动发送，请勿直接回复</p>
            <p style="font-size: 12px; color: #999;">© {current_year} {site_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>'''

    @staticmethod
    def get_subscription_template(subscription_id: int, request=None, db=None) -> str:
        """订阅地址通知邮件模板"""
        import urllib.parse
        
        if not request or not db:
            return "请求或数据库连接不可用"
        
        # 使用API客户端获取完整的订阅数据
        from app.services.email_api_client import EmailAPIClient
        api_client = EmailAPIClient(request, db)
        subscription_data = api_client.get_complete_subscription_data(subscription_id)
        
        if not subscription_data:
            return "订阅信息不存在"
        
        title = "服务配置信息"
        
        # 从数据库获取的真实数据
        username = subscription_data.get('username', '用户')
        nickname = subscription_data.get('nickname', username)
        v2ray_url = subscription_data.get('v2ray_url', '')
        clash_url = subscription_data.get('clash_url', '')
        ssr_url = subscription_data.get('ssr_url', '')
        subscription_url = subscription_data.get('subscription_url', '')
        expire_time = subscription_data.get('expire_time', '永久')
        device_limit = subscription_data.get('device_limit', 3)
        current_devices = subscription_data.get('current_devices', 0)
        max_devices = subscription_data.get('max_devices', device_limit)
        package_name = subscription_data.get('package_name', '未知套餐')
        user_email = subscription_data.get('email', '')
        
        # 从数据库获取的详细信息
        user_id = subscription_data.get('user_id', '')
        is_verified = subscription_data.get('is_verified', False)
        created_at = subscription_data.get('created_at', '未知')
        last_login = subscription_data.get('last_login', '从未登录')
        subscription_id = subscription_data.get('id', '')
        is_active = subscription_data.get('is_active', False)
        status = subscription_data.get('status', '未知')
        remaining_days = subscription_data.get('remaining_days', 0)
        subscription_created = subscription_data.get('created_at', '未知')
        package_description = subscription_data.get('package_description', '无描述')
        package_price = subscription_data.get('package_price', 0.0)
        package_duration = subscription_data.get('package_duration', 0)
        package_bandwidth_limit = subscription_data.get('package_bandwidth_limit', None)
        site_name = subscription_data.get('site_name', '网络服务')
        
        # 使用动态域名配置
        base_url = subscription_data.get('base_url', EmailTemplateEnhanced._get_base_url(request, db))
        
        # 正确编码URL用于二维码
        qr_url = urllib.parse.quote(v2ray_url, safe='')
        
        content = f'''
            <h2>您的服务配置信息</h2>
            <p>亲爱的 {username}，</p>
            <p>您的服务配置已生成完成，请查收以下信息：</p>
            
            <table class="info-table">
                <tr>
                    <th>用户账号</th>
                    <td>{username}</td>
                </tr>
                <tr>
                    <th>用户ID</th>
                    <td>{user_id}</td>
                </tr>
                <tr>
                    <th>用户邮箱</th>
                    <td>{user_email}</td>
                </tr>
                <tr>
                    <th>邮箱验证状态</th>
                    <td style="color: {'#27ae60' if is_verified else '#e74c3c'};">{'已验证' if is_verified else '未验证'}</td>
                </tr>
                <tr>
                    <th>注册时间</th>
                    <td>{created_at}</td>
                </tr>
                <tr>
                    <th>最后登录</th>
                    <td>{last_login}</td>
                </tr>
                <tr>
                    <th>订阅ID</th>
                    <td>{subscription_id}</td>
                </tr>
                <tr>
                    <th>套餐名称</th>
                    <td>{package_name}</td>
                </tr>
                <tr>
                    <th>套餐描述</th>
                    <td>{package_description}</td>
                </tr>
                <tr>
                    <th>套餐价格</th>
                    <td>¥{package_price}</td>
                </tr>
                <tr>
                    <th>套餐时长</th>
                    <td>{package_duration} 天</td>
                </tr>
                <tr>
                    <th>流量限制</th>
                    <td>{package_bandwidth_limit if package_bandwidth_limit else '无限制'} GB</td>
                </tr>
                <tr>
                    <th>配置标识</th>
                    <td style="font-family: monospace;">{subscription_url}</td>
                </tr>
                <tr>
                    <th>设备使用情况</th>
                    <td style="color: {'#e74c3c' if current_devices >= max_devices else '#27ae60'};">{current_devices}/{max_devices} 台设备</td>
                </tr>
                <tr>
                    <th>订阅状态</th>
                    <td style="color: {'#27ae60' if is_active else '#e74c3c'};">{'活跃' if is_active else '非活跃'}</td>
                </tr>
                <tr>
                    <th>服务期限</th>
                    <td style="color: #e74c3c; font-weight: bold;">{expire_time}</td>
                </tr>
                <tr>
                    <th>剩余天数</th>
                    <td style="color: {'#e74c3c' if remaining_days <= 7 else '#27ae60'}; font-weight: bold;">{remaining_days} 天</td>
                </tr>
                <tr>
                    <th>订阅创建时间</th>
                    <td>{subscription_created}</td>
                </tr>
            </table>
            
            <h3>📱 配置地址</h3>
            <div class="success-box">
                <div class="url-list">
                    <div class="url-item">
                        <strong>🔗 通用配置地址（推荐）：</strong>
                        <p style="margin: 5px 0; color: #666; font-size: 12px;">适用于大部分客户端，包括手机和电脑</p>
                        <code class="url-code">{v2ray_url}</code>
                    </div>
                    
                    <div class="url-item">
                        <strong>⚡ 移动端专用地址：</strong>
                        <p style="margin: 5px 0; color: #666; font-size: 12px;">专为移动设备优化，支持规则分流</p>
                        <code class="url-code">{clash_url}</code>
                    </div>
                    
                </div>
                
                <div style="margin-top: 20px; text-align: center;">
                    <p><strong>📱 扫码快速配置</strong></p>
                    <p style="color: #666; font-size: 14px; margin-bottom: 10px;">使用相机扫描下方二维码即可快速添加配置</p>
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_url}" style="border: 1px solid #ddd; border-radius: 8px; max-width: 200px;" alt="配置二维码">
                </div>
            </div>
            
            <h3>📖 使用说明</h3>
            <div class="info-box">
                <p><strong>客户端配置步骤：</strong></p>
                <ol>
                    <li><strong>复制配置地址</strong>：点击上方配置地址进行复制</li>
                    <li><strong>添加配置</strong>：在您的客户端中添加配置</li>
                    <li><strong>更新配置</strong>：点击更新获取最新配置</li>
                    <li><strong>开始使用</strong>：选择节点并连接即可</li>
                </ol>
            </div>
            
            <h3>🔧 支持的客户端</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0;">
                <span style="background: #667eea; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px;">Clash</span>
                <span style="background: #667eea; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px;">V2rayN</span>
                <span style="background: #667eea; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px;">Shadowrocket</span>
                <span style="background: #667eea; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px;">Quantumult X</span>
                <span style="background: #667eea; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px;">Surge</span>
                <span style="background: #667eea; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px;">Sparkle</span>
                <span style="background: #667eea; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px;">Mihomo</span>
            </div>
            
            <div class="warning-box">
                <p><strong>⚠️ 安全提醒：</strong></p>
                <ul>
                    <li>请妥善保管您的配置地址，切勿分享给他人</li>
                    <li>如发现地址泄露，请及时联系客服重置</li>
                    <li>建议定期更换配置地址以确保安全</li>
                    <li>服务到期前会收到续费提醒邮件</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{base_url}/" class="btn">查看我的服务</a>
            </div>
            
            <p style="text-align: center; color: #666; font-size: 14px;">如有任何问题，请随时联系我们的客服团队</p>
        '''
        
        return EmailTemplateEnhanced.get_base_template(title, content, '享受高速稳定的网络服务')

    @staticmethod
    def get_activation_template(username: str, activation_link: str) -> str:
        """用户注册激活邮件模板"""
        title = "账户激活"
        content = f'''
            <h2>欢迎注册！</h2>
            <p>亲爱的用户 <strong>{username}</strong>，</p>
            <p>感谢您注册我们的服务！为了确保账户安全，请点击下方按钮激活您的账户：</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{activation_link}" class="btn">立即激活账户</a>
            </div>
            
            <div class="info-box">
                <p><strong>重要提醒：</strong></p>
                <ul>
                    <li>此激活链接仅限本次使用</li>
                    <li>如果按钮无法点击，请复制以下链接到浏览器：</li>
                    <li style="word-break: break-all; color: #667eea;">{activation_link}</li>
                </ul>
            </div>
            
            <p>激活成功后，您将可以享受我们提供的所有服务功能。</p>
        '''
        
        return EmailTemplateEnhanced.get_base_template(title, content, '开启您的专属网络体验')

    @staticmethod
    def get_order_confirmation_template(username: str, order_data: dict) -> str:
        """下单确认邮件模板"""
        title = "订单确认"
        content = f'''
            <h2>订单确认</h2>
            <p>亲爱的用户 <strong>{username}</strong>，</p>
            <p>感谢您的购买！您的订单已成功创建，详情如下：</p>
            
            <div class="info-box">
                <table class="info-table">
                    <tr>
                        <th>订单号</th>
                        <td>{order_data.get('order_no', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>套餐名称</th>
                        <td>{order_data.get('package_name', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>订单金额</th>
                        <td>¥{order_data.get('amount', '0.00')}</td>
                    </tr>
                    <tr>
                        <th>支付方式</th>
                        <td>{order_data.get('payment_method', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>下单时间</th>
                        <td>{order_data.get('created_at', 'N/A')}</td>
                    </tr>
                </table>
            </div>
            
            <div class="warning-box">
                <p><strong>重要提醒：</strong></p>
                <ul>
                    <li>请尽快完成支付，订单将在24小时后自动取消</li>
                    <li>支付成功后，服务将自动激活</li>
                    <li>如有疑问，请联系客服</li>
                </ul>
            </div>
            
            <p>感谢您选择我们的服务！</p>
        '''
        
        return EmailTemplateEnhanced.get_base_template(title, content, '开启您的专属网络体验')


    @staticmethod
    def get_account_deletion_template(username: str, deletion_data: dict) -> str:
        """账号删除邮件模板"""
        title = "账号删除确认"
        content = f'''
            <h2>账号删除确认</h2>
            <p>亲爱的用户 <strong>{username}</strong>，</p>
            <p>您的账号删除请求已收到，我们对此表示遗憾。</p>
            
            <div class="info-box">
                <table class="info-table">
                    <tr>
                        <th>删除原因</th>
                        <td>{deletion_data.get('reason', '用户主动删除')}</td>
                    </tr>
                    <tr>
                        <th>删除时间</th>
                        <td>{deletion_data.get('deletion_date', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>数据保留期</th>
                        <td>{deletion_data.get('data_retention_period', '30天')}</td>
                    </tr>
                </table>
            </div>
            
            <div class="warning-box">
                <p><strong>重要提醒：</strong></p>
                <ul>
                    <li>您的账号将在数据保留期结束后永久删除</li>
                    <li>删除后无法恢复，请谨慎操作</li>
                    <li>如有疑问，请在保留期内联系客服</li>
                </ul>
            </div>
            
            <p>感谢您曾经选择我们的服务！</p>
        '''
        
        return EmailTemplateEnhanced.get_base_template(title, content, '开启您的专属网络体验')

    @staticmethod
    def get_renewal_confirmation_template(username: str, renewal_data: dict) -> str:
        """续费确认邮件模板"""
        title = "续费成功"
        content = f'''
            <h2>续费成功</h2>
            <p>亲爱的用户 <strong>{username}</strong>，</p>
            <p>恭喜！您的服务续费已成功完成。</p>
            
            <div class="success-box">
                <p><strong>续费详情：</strong></p>
                <table class="info-table">
                    <tr>
                        <th>套餐名称</th>
                        <td>{renewal_data.get('package_name', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>原到期时间</th>
                        <td>{renewal_data.get('old_expiry_date', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>新到期时间</th>
                        <td>{renewal_data.get('new_expiry_date', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>续费金额</th>
                        <td>¥{renewal_data.get('amount', '0.00')}</td>
                    </tr>
                    <tr>
                        <th>续费时间</th>
                        <td>{renewal_data.get('renewal_date', 'N/A')}</td>
                    </tr>
                </table>
            </div>
            
            <div class="info-box">
                <p><strong>服务说明：</strong></p>
                <ul>
                    <li>您的服务已成功续费，可继续使用</li>
                    <li>新的订阅地址已更新</li>
                    <li>如有技术问题，请联系技术支持</li>
                </ul>
            </div>
            
            <p>感谢您的续费，祝您使用愉快！</p>
        '''
        
        return EmailTemplateEnhanced.get_base_template(title, content, '开启您的专属网络体验')

    @staticmethod
    def get_password_reset_template(username: str, reset_link: str) -> str:
        """密码重置邮件模板"""
        title = "密码重置"
        content = f'''
            <h2>🔐 密码重置请求</h2>
            <p>亲爱的用户 <strong>{username}</strong>，</p>
            <p>我们收到了您的密码重置请求。如果这不是您本人的操作，请忽略此邮件。</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" class="btn">重置密码</a>
            </div>
            
            <div class="info-box">
                <p><strong>安全提醒：</strong></p>
                <ul>
                    <li>此重置链接仅在24小时内有效</li>
                    <li>链接仅可使用一次</li>
                    <li>如果链接失效，请重新申请密码重置</li>
                    <li>重置链接：<span style="word-break: break-all; color: #667eea;">{reset_link}</span></li>
                </ul>
            </div>
            
            <p>为了您的账户安全，建议设置一个强密码，包含字母、数字和特殊字符。</p>
        '''
        
        return EmailTemplateEnhanced.get_base_template(title, content, '保护您的账户安全')

    @staticmethod
    def get_expiration_template(subscription_id: int, is_expired: bool = False, request=None, db=None) -> str:
        """到期提醒邮件模板"""
        title = "订阅已到期" if is_expired else "订阅即将到期"
        
        if not request or not db:
            return "请求或数据库连接不可用"
        
        # 使用API客户端获取订阅数据
        from app.services.email_api_client import EmailAPIClient
        api_client = EmailAPIClient(request, db)
        subscription_data = api_client.get_complete_subscription_data(subscription_id)
        
        if not subscription_data:
            return "订阅信息不存在"
        
        # 获取动态base_url
        base_url = subscription_data.get('base_url', EmailTemplateEnhanced._get_base_url(request, db))
        
        # 从数据库获取的真实数据
        username = subscription_data.get('username', '用户')
        nickname = subscription_data.get('nickname', username)
        expire_date = subscription_data.get('expire_time', '未知')
        package_name = subscription_data.get('package_name', '未知套餐')
        device_limit = subscription_data.get('device_limit', 3)
        current_devices = subscription_data.get('current_devices', 0)
        remaining_days = subscription_data.get('remaining_days', 0)
        
        if is_expired:
            content = f'''
                <h2>⚠️ 服务已到期</h2>
                <p>亲爱的用户 <strong>{username}</strong>，</p>
                <p>您的服务已于 <strong style="color: #e74c3c;">{expire_date}</strong> 到期。</p>
                
                <div class="warning-box">
                    <p><strong>服务已暂停：</strong></p>
                    <ul>
                        <li>您的配置地址已停止更新</li>
                        <li>无法获取最新的节点配置</li>
                        <li>请及时续费以恢复服务</li>
                    </ul>
                </div>
            '''
        else:
            content = f'''
                <h2>服务即将到期</h2>
                <p>亲爱的用户 <strong>{username}</strong>，</p>
                <p>您的服务将于 <strong style="color: #ffc107;">{expire_date}</strong> 到期。</p>
                
                <div class="warning-box">
                    <p><strong>温馨提醒：</strong></p>
                    <ul>
                        <li>为避免服务中断，请提前续费</li>
                        <li>到期后配置地址将停止更新</li>
                        <li>续费后服务将自动恢复</li>
                    </ul>
                </div>
            '''
        
        content += f'''
            <table class="info-table">
                <tr>
                    <th>用户账号</th>
                    <td>{username}</td>
                </tr>
                <tr>
                    <th>到期时间</th>
                    <td style="color: #e74c3c; font-weight: bold;">{expire_date}</td>
                </tr>
            </table>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{base_url}/" class="btn">立即续费</a>
            </div>
            
            <p>如有任何问题，请随时联系我们的客服团队。</p>
        '''
        
        return EmailTemplateEnhanced.get_base_template(title, content, '我们期待继续为您服务')

    @staticmethod
    def get_subscription_reset_template(subscription_id: int, reset_time: str, reset_reason: str, request=None, db=None) -> str:
        """订阅重置通知邮件模板"""
        title = "订阅重置通知"
        
        if not db:
            return "数据库连接不可用"
        
        # 使用API客户端获取完整的订阅数据
        from app.services.email_api_client import EmailAPIClient
        api_client = EmailAPIClient(request, db)
        subscription_data = api_client.get_complete_subscription_data(subscription_id)
        
        if not subscription_data:
            return "订阅信息不存在"
        
        # 获取动态base_url
        base_url = subscription_data.get('base_url', EmailTemplateEnhanced._get_base_url(request, db))
        
        # 从数据库获取的真实数据
        username = subscription_data.get('username', '用户')
        nickname = subscription_data.get('nickname', username)
        v2ray_url = subscription_data.get('v2ray_url', '')
        clash_url = subscription_data.get('clash_url', '')
        ssr_url = subscription_data.get('ssr_url', '')
        device_limit = subscription_data.get('device_limit', 3)
        current_devices = subscription_data.get('current_devices', 0)
        package_name = subscription_data.get('package_name', '未知套餐')
        expire_time = subscription_data.get('expire_time', '永久')
        
        # 调试信息
        print(f"🔍 邮件模板调试信息:")
        print(f"   - 用户名: {username}")
        print(f"   - V2Ray地址: {v2ray_url}")
        print(f"   - Clash地址: {clash_url}")
        print(f"   - SSR地址: {ssr_url}")
        print(f"   - 基础URL: {base_url}")
        print(f"   - 订阅数据键: {list(subscription_data.keys())}")
        
        content = f'''
            <h2>您的订阅已重置</h2>
            <p>亲爱的 {username}，</p>
            <p>您的订阅地址已被重置，请使用新的订阅地址更新您的客户端配置。</p>
            
            <div class="info-box">
                <h3>📋 重置信息</h3>
                <table class="info-table">
                    <tr>
                        <td><strong>重置时间：</strong></td>
                        <td>{reset_time}</td>
                    </tr>
                    <tr>
                        <td><strong>重置原因：</strong></td>
                        <td>{reset_reason}</td>
                    </tr>
                </table>
            </div>
            
            <div class="success-box">
                <h3>🔗 新的订阅地址</h3>
                <div class="url-list">
                    <div class="url-item">
                        <strong>V2Ray/SSR 配置：</strong><br>
                        <code class="url-code">{v2ray_url}</code>
                    </div>
                    <div class="url-item">
                        <strong>Clash 配置：</strong><br>
                        <code class="url-code">{clash_url}</code>
                    </div>
                </div>
            </div>
            
            <div class="warning-box">
                <h3>⚠️ 重要提醒</h3>
                <ul>
                    <li>请立即更新您的客户端配置，使用新的订阅地址</li>
                    <li>旧的订阅地址将无法使用</li>
                    <li>请妥善保管新的订阅地址，不要分享给他人</li>
                    <li>如有疑问，请及时联系客服</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{base_url}/dashboard" class="btn">查看订阅详情</a>
            </div>
            
            <p>如有任何问题，请随时联系我们的客服团队。</p>
        '''
        
        return EmailTemplateEnhanced.get_base_template(title, content, '请及时更新您的客户端配置')
    
    @staticmethod
    def get_payment_success_template(order_id: int, request=None, db=None) -> str:
        """支付成功通知邮件模板"""
        title = "支付成功通知"
        
        if not request or not db:
            return "请求或数据库连接不可用"
        
        # 使用API客户端获取订单数据
        from app.services.email_api_client import EmailAPIClient
        api_client = EmailAPIClient(request, db)
        
        # 先获取订单信息，然后获取用户和订阅信息
        # 这里需要根据实际的API端点调整
        order_data = api_client.get_order_info(order_id)  # 这个方法需要在EmailAPIClient中实现
        
        if not order_data:
            return "订单信息不存在"
        
        # 获取动态base_url
        base_url = order_data.get('base_url', EmailTemplateEnhanced._get_base_url(request, db))
        
        # 从数据库获取的真实数据
        username = order_data.get('username', '用户')
        nickname = order_data.get('username', username)  # 订单表中没有nickname字段
        amount = order_data.get('amount', 0.0)
        package_name = order_data.get('package_name', '未知套餐')
        order_no = order_data.get('order_no', '')
        payment_method = order_data.get('payment_method_name', '未知')
        created_at = order_data.get('created_at', '未知')
        package_description = order_data.get('package_description', '无描述')
        package_duration = order_data.get('package_duration', 0)
        content = f'''
            <h2>🎉 支付成功！</h2>
            <p>亲爱的 {username}，</p>
            <p>您的支付已成功处理，感谢您的购买！</p>
            
            <div class="info-box">
                <h3>📋 订单信息</h3>
                <table class="info-table">
                    <tr>
                        <th>订单号</th>
                        <td>{order_id}</td>
                    </tr>
                    <tr>
                        <th>套餐名称</th>
                        <td>{package_name}</td>
                    </tr>
                    <tr>
                        <th>支付金额</th>
                        <td style="color: #27ae60; font-weight: bold;">¥{amount}</td>
                    </tr>
                    <tr>
                        <th>支付时间</th>
                        <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                </table>
            </div>
            
            <div class="success-box">
                <p><strong>✅ 服务状态：</strong></p>
                <ul>
                    <li>您的订阅已激活</li>
                    <li>配置地址已更新</li>
                    <li>可以立即使用服务</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{base_url}/dashboard" class="btn">查看订阅详情</a>
            </div>
            
            <p>如有任何问题，请随时联系我们的客服团队。</p>
        '''
        
        return EmailTemplateEnhanced.get_base_template(title, content, '感谢您的信任')
    
    @staticmethod
    def get_welcome_template(user_id: int, request=None, db=None) -> str:
        """新用户欢迎邮件模板"""
        title = "欢迎加入我们！"
        
        if not request or not db:
            return "请求或数据库连接不可用"
        
        # 使用API客户端获取用户数据
        from app.services.email_api_client import EmailAPIClient
        api_client = EmailAPIClient(request, db)
        user_data = api_client.get_complete_user_data(user_id)
        
        if not user_data:
            return "用户信息不存在"
        
        # 获取动态base_url
        base_url = user_data.get('base_url', EmailTemplateEnhanced._get_base_url(request, db))
        
        # 从数据库获取的真实数据
        username = user_data.get('username', '用户')
        nickname = user_data.get('nickname', username)
        email = user_data.get('email', '')
        created_at = user_data.get('created_at', '未知')
        is_verified = user_data.get('is_verified', False)
        login_url = f"{base_url}/login"
        content = f'''
            <h2>🎉 欢迎注册成功！</h2>
            <p>亲爱的 {username}，</p>
            <p>欢迎加入我们的网络服务平台！您的账户已成功创建。</p>
            
            <div class="info-box">
                <h3>📋 账户信息</h3>
                <table class="info-table">
                    <tr>
                        <th>用户名</th>
                        <td>{username}</td>
                    </tr>
                    <tr>
                        <th>注册时间</th>
                        <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                </table>
            </div>
            
            <div class="success-box">
                <p><strong>🚀 开始使用：</strong></p>
                <ul>
                    <li>登录您的账户</li>
                    <li>选择合适的套餐</li>
                    <li>获取订阅地址</li>
                    <li>配置您的客户端</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{login_url}" class="btn">立即登录</a>
            </div>
            
            <p>如有任何问题，请随时联系我们的客服团队。</p>
        '''
        
        return EmailTemplateEnhanced.get_base_template(title, content, '期待为您提供优质服务')
    
    @staticmethod
    def get_subscription_created_template(subscription_id: int, request=None, db=None) -> str:
        """订阅创建成功邮件模板"""
        title = "订阅创建成功"
        
        if not request or not db:
            return "请求或数据库连接不可用"
        
        # 使用API客户端获取完整的订阅数据
        from app.services.email_api_client import EmailAPIClient
        api_client = EmailAPIClient(request, db)
        subscription_data = api_client.get_complete_subscription_data(subscription_id)
        
        if not subscription_data:
            return "订阅信息不存在"
        
        # 获取动态base_url
        base_url = subscription_data.get('base_url', EmailTemplateEnhanced._get_base_url(request, db))
        
        # 从数据库获取的真实数据
        username = subscription_data.get('username', '用户')
        nickname = subscription_data.get('nickname', username)
        v2ray_url = subscription_data.get('v2ray_url', '')
        clash_url = subscription_data.get('clash_url', '')
        ssr_url = subscription_data.get('ssr_url', '')
        expire_time = subscription_data.get('expire_time', '永久')
        package_name = subscription_data.get('package_name', '未知套餐')
        device_limit = subscription_data.get('device_limit', 3)
        current_devices = subscription_data.get('current_devices', 0)
        package_description = subscription_data.get('package_description', '无描述')
        package_price = subscription_data.get('package_price', 0.0)
        package_duration = subscription_data.get('package_duration', 0)
        
        content = f'''
            <h2>🎉 订阅创建成功！</h2>
            <p>亲爱的 {username}，</p>
            <p>您的订阅已成功创建，现在可以开始使用我们的服务了！</p>
            
            <div class="info-box">
                <h3>📋 订阅信息</h3>
                <table class="info-table">
                    <tr>
                        <td><strong>套餐名称：</strong></td>
                        <td>{package_name}</td>
                    </tr>
                    <tr>
                        <td><strong>设备限制：</strong></td>
                        <td>{device_limit} 台设备</td>
                    </tr>
                    <tr>
                        <td><strong>到期时间：</strong></td>
                        <td>{expire_time}</td>
                    </tr>
                </table>
            </div>
            
            <div class="success-box">
                <h3>🔗 配置地址</h3>
                <div class="url-list">
                    <div class="url-item">
                        <strong>V2Ray/SSR 配置：</strong><br>
                        <code class="url-code">{v2ray_url}</code>
                    </div>
                    <div class="url-item">
                        <strong>Clash 配置：</strong><br>
                        <code class="url-code">{clash_url}</code>
                    </div>
                </div>
            </div>
            
            <div class="info-box">
                <h3>📱 使用说明</h3>
                <ol>
                    <li>复制上述配置地址到您的客户端</li>
                    <li>选择合适的配置类型（V2Ray/Clash/SSR）</li>
                    <li>导入配置并连接</li>
                    <li>享受高速稳定的网络服务</li>
                </ol>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{base_url}/dashboard" class="btn">查看订阅详情</a>
            </div>
            
            <p>如有任何问题，请随时联系我们的客服团队。</p>
        '''
        
        return EmailTemplateEnhanced.get_base_template(title, content, '祝您使用愉快')