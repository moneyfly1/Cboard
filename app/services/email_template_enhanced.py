"""
增强版邮件模板服务
使用中性词汇，避免敏感关键词
"""

from datetime import datetime
from typing import Dict, Any, Optional


class EmailTemplateEnhanced:
    """增强版邮件模板类"""
    
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
    def get_subscription_template(username: str, subscription_data: Dict[str, Any]) -> str:
        """订阅地址通知邮件模板"""
        title = "服务配置信息"
        
        # 使用中性词汇替换敏感词
        v2ray_url = subscription_data.get('v2ray_url', '').replace('v2ray', 'config').replace('clash', 'mobile')
        clash_url = subscription_data.get('clash_url', '').replace('v2ray', 'config').replace('clash', 'mobile')
        subscription_url = subscription_data.get('subscription_url', '')
        expire_time = subscription_data.get('expire_time', '永久')
        device_limit = subscription_data.get('device_limit', 3)
        
        content = f'''
            <h2>您的服务配置信息</h2>
            <p>亲爱的用户，</p>
            <p>您的服务配置已生成完成，请查收以下信息：</p>
            
            <table class="info-table">
                <tr>
                    <th>用户账号</th>
                    <td>{username}</td>
                </tr>
                <tr>
                    <th>配置标识</th>
                    <td style="font-family: monospace;">{subscription_url}</td>
                </tr>
                <tr>
                    <th>设备限制</th>
                    <td>{device_limit} 台设备</td>
                </tr>
                <tr>
                    <th>服务期限</th>
                    <td style="color: #e74c3c; font-weight: bold;">{expire_time}</td>
                </tr>
            </table>
            
            <h3>📱 配置地址</h3>
            <div class="info-box">
                <p><strong>🔗 通用配置地址（推荐）：</strong></p>
                <p style="margin-bottom: 5px; color: #666; font-size: 14px;">适用于大部分客户端，包括手机和电脑</p>
                <div class="url-box">{v2ray_url}</div>
                
                <p style="margin-top: 20px;"><strong>⚡ 移动端专用地址：</strong></p>
                <p style="margin-bottom: 5px; color: #666; font-size: 14px;">专为移动设备优化，支持规则分流</p>
                <div class="url-box">{clash_url}</div>
                
                <div style="margin-top: 20px; text-align: center;">
                    <p><strong>📱 扫码快速配置</strong></p>
                    <p style="color: #666; font-size: 14px; margin-bottom: 10px;">使用相机扫描下方二维码即可快速添加配置</p>
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={v2ray_url}" style="border: 1px solid #ddd; border-radius: 8px; max-width: 200px;" alt="配置二维码">
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
                <a href="http://localhost:8000/" class="btn">查看我的服务</a>
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
    def get_expiration_template(username: str, expire_date: str, is_expired: bool = False) -> str:
        """到期提醒邮件模板"""
        title = "订阅已到期" if is_expired else "订阅即将到期"
        
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
                <a href="http://localhost:8000/" class="btn">立即续费</a>
            </div>
            
            <p>如有任何问题，请随时联系我们的客服团队。</p>
        '''
        
        return EmailTemplateEnhanced.get_base_template(title, content, '我们期待继续为您服务')
