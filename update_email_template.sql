-- 更新邮件模板，使用中性词汇
UPDATE email_templates 
SET content = '<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>服务配置信息</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            background-color: #f4f4f4;
            color: #333;
        }
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 300;
        }
        .content {
            padding: 40px 30px;
        }
        .content h2 {
            color: #333;
            font-size: 24px;
            margin-bottom: 20px;
            font-weight: 400;
        }
        .info-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .info-table th,
        .info-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }
        .info-table th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
            width: 30%;
        }
        .url-box {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
            word-break: break-all;
            font-family: monospace;
            color: #667eea;
        }
        .warning-box {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 15px;
            margin: 20px 0;
            color: #856404;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e9ecef;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>网络服务</h1>
            <p>服务配置信息</p>
        </div>
        <div class="content">
            <h2>您的服务配置信息</h2>
            <p>亲爱的用户，</p>
            <p>您的服务配置已生成完成，请查收以下信息：</p>
            
            <table class="info-table">
                <tr>
                    <th>用户账号</th>
                    <td>{{ username }}</td>
                </tr>
                <tr>
                    <th>配置标识</th>
                    <td style="font-family: monospace;">{{ subscription_url }}</td>
                </tr>
                <tr>
                    <th>设备限制</th>
                    <td>{{ device_limit }} 台设备</td>
                </tr>
                <tr>
                    <th>服务期限</th>
                    <td style="color: #e74c3c; font-weight: bold;">{{ expire_time }}</td>
                </tr>
            </table>
            
            <h3>📱 配置地址</h3>
            <div class="url-box">
                <p><strong>🔗 通用配置地址（推荐）：</strong></p>
                <p style="margin-bottom: 5px; color: #666; font-size: 14px;">适用于大部分客户端，包括手机和电脑</p>
                <div class="url-box">{{ v2ray_url }}</div>
                
                <p style="margin-top: 20px;"><strong>⚡ 移动端专用地址：</strong></p>
                <p style="margin-bottom: 5px; color: #666; font-size: 14px;">专为移动设备优化，支持规则分流</p>
                <div class="url-box">{{ clash_url }}</div>
            </div>
            
            <div class="warning-box">
                <p><strong>⚠️ 安全提醒：</strong></p>
                <ul>
                    <li>请妥善保管您的配置地址，切勿分享给他人</li>
                    <li>如发现地址泄露，请及时联系客服重置</li>
                    <li>建议定期更换配置地址以确保安全</li>
                </ul>
            </div>
        </div>
        <div class="footer">
            <p><strong>网络服务</strong></p>
            <p>感谢您选择我们的服务</p>
            <p style="font-size: 12px; color: #999;">此邮件由系统自动发送，请勿直接回复</p>
        </div>
    </div>
</body>
</html>'
WHERE name = 'subscription';