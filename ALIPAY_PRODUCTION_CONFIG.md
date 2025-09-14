# 支付宝生产环境配置指南

## 概述

本指南将详细说明如何配置真实的支付宝 SDK 环境，从开发测试到生产环境的完整配置流程。

## 第一步：申请支付宝开发者账号

### 1.1 注册开发者账号

1. 访问 [支付宝开放平台](https://open.alipay.com/)
2. 点击"立即入驻"
3. 选择"个人开发者"或"企业开发者"
4. 填写相关信息并完成实名认证

### 1.2 创建应用

1. 登录开发者控制台
2. 点击"创建应用"
3. 选择"网页&移动应用"
4. 填写应用信息：
   - 应用名称：XBoard 支付系统
   - 应用描述：订阅服务支付系统
   - 应用图标：上传应用图标

### 1.3 获取应用信息

创建应用后，记录以下信息：
- **APPID**：应用 ID（如：2021001234567890）
- **应用私钥**：商户私钥
- **支付宝公钥**：支付宝公钥

## 第二步：配置应用功能

### 2.1 添加功能

在应用管理中添加以下功能：
- **电脑网站支付**：用于网页支付
- **手机网站支付**：用于移动端支付
- **当面付**：用于扫码支付

### 2.2 配置回调地址

设置以下回调地址：
- **支付结果通知地址**：`https://yourdomain.com/api/v1/payment/alipay/notify`
- **支付成功返回地址**：`https://yourdomain.com/payment/success`
- **支付失败返回地址**：`https://yourdomain.com/payment/failure`

### 2.3 配置应用网关

设置应用网关：
- **应用网关**：`https://yourdomain.com/api/v1/payment/alipay/gateway`

## 第三步：生成密钥对

### 3.1 生成应用私钥

使用支付宝提供的密钥生成工具：

1. 下载 [密钥生成工具](https://opendocs.alipay.com/common/02kipl)
2. 运行工具生成 RSA2 密钥对
3. 保存私钥文件（.txt 格式）
4. 复制私钥内容

### 3.2 配置支付宝公钥

1. 在开发者控制台中上传公钥
2. 获取支付宝公钥
3. 保存公钥内容

### 3.3 密钥格式示例

**应用私钥格式：**
```
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
-----END PRIVATE KEY-----
```

**支付宝公钥格式：**
```
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----
```

## 第四步：环境配置

### 4.1 开发环境配置

在开发环境中使用支付宝沙箱：

```bash
# 沙箱环境配置
ALIPAY_APP_ID=沙箱APPID
ALIPAY_PRIVATE_KEY=沙箱应用私钥
ALIPAY_PUBLIC_KEY=沙箱支付宝公钥
ALIPAY_NOTIFY_URL=http://localhost:8000/api/v1/payment/alipay/notify
ALIPAY_RETURN_URL=http://localhost:3000/payment/success
ALIPAY_DEBUG=true
```

### 4.2 生产环境配置

在生产环境中使用真实配置：

```bash
# 生产环境配置
ALIPAY_APP_ID=2021001234567890
ALIPAY_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
-----END PRIVATE KEY-----
ALIPAY_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----
ALIPAY_NOTIFY_URL=https://yourdomain.com/api/v1/payment/alipay/notify
ALIPAY_RETURN_URL=https://yourdomain.com/payment/success
ALIPAY_DEBUG=false
```

## 第五步：代码配置

### 5.1 更新支付服务

确保支付服务正确配置：

```python
# app/services/payment.py
class AlipayPaymentService:
    def __init__(self, config):
        self.app_id = config.get('app_id')
        self.private_key = config.get('merchant_private_key')
        self.alipay_public_key = config.get('alipay_public_key')
        self.notify_url = config.get('notify_url')
        self.return_url = config.get('return_url')
        self.debug = config.get('debug', False)
        
        # 初始化支付宝客户端
        self.alipay = AliPay(
            appid=self.app_id,
            app_notify_url=self.notify_url,
            app_private_key_string=self.private_key,
            alipay_public_key_string=self.alipay_public_key,
            sign_type="RSA2",
            debug=self.debug
        )
```

### 5.2 配置回调处理

确保回调处理正确：

```python
# app/api/api_v1/endpoints/payment.py
@router.post("/alipay/notify")
async def alipay_notify(request: Request, db: Session = Depends(get_db)):
    """支付宝支付回调"""
    try:
        # 获取回调数据
        data = await request.form()
        
        # 验证签名
        if alipay.verify(data, data.get('sign')):
            # 处理支付成功
            order_no = data.get('out_trade_no')
            trade_no = data.get('trade_no')
            
            # 更新订单状态
            # ... 处理逻辑
            
            return "success"
        else:
            return "fail"
    except Exception as e:
        logger.error(f"支付宝回调处理失败: {e}")
        return "fail"
```

## 第六步：测试配置

### 6.1 沙箱环境测试

1. 使用支付宝沙箱环境进行测试
2. 创建测试订单
3. 验证支付流程
4. 检查回调处理

### 6.2 生产环境测试

1. 配置生产环境参数
2. 创建小额测试订单
3. 验证支付流程
4. 检查回调处理

### 6.3 测试检查清单

- [ ] 支付页面正常显示
- [ ] 支付二维码正常生成
- [ ] 支付流程正常完成
- [ ] 回调处理正常
- [ ] 订单状态正确更新
- [ ] 用户订阅正确创建

## 第七步：安全配置

### 7.1 密钥安全

1. **私钥保护**：
   - 私钥文件不要提交到代码仓库
   - 使用环境变量存储私钥
   - 定期更换私钥

2. **公钥验证**：
   - 确保使用正确的支付宝公钥
   - 定期检查公钥是否更新

### 7.2 回调安全

1. **签名验证**：
   - 所有回调都必须验证签名
   - 使用官方 SDK 进行验证

2. **重复通知处理**：
   - 处理重复的支付通知
   - 使用幂等性设计

### 7.3 网络安全

1. **HTTPS 配置**：
   - 生产环境必须使用 HTTPS
   - 配置有效的 SSL 证书

2. **IP 白名单**：
   - 配置支付宝 IP 白名单
   - 限制回调来源 IP

## 第八步：监控和日志

### 8.1 支付日志

配置详细的支付日志：

```python
import logging

# 配置支付日志
payment_logger = logging.getLogger('payment')
payment_logger.setLevel(logging.INFO)

# 记录支付请求
payment_logger.info(f"支付请求: {order_no}, 金额: {amount}")

# 记录支付结果
payment_logger.info(f"支付结果: {order_no}, 状态: {status}")
```

### 8.2 异常监控

配置异常监控：

```python
# 监控支付异常
try:
    # 支付处理逻辑
    pass
except Exception as e:
    # 记录异常
    logger.error(f"支付异常: {e}")
    
    # 发送告警
    send_alert(f"支付异常: {e}")
```

### 8.3 性能监控

监控支付性能：

```python
import time

# 记录支付耗时
start_time = time.time()
# 支付处理逻辑
end_time = time.time()

logger.info(f"支付耗时: {end_time - start_time}秒")
```

## 第九步：故障排除

### 9.1 常见问题

#### 问题 1：支付页面无法显示

**可能原因：**
- APPID 配置错误
- 私钥格式错误
- 网络连接问题

**解决方案：**
1. 检查 APPID 是否正确
2. 验证私钥格式
3. 检查网络连接

#### 问题 2：支付回调失败

**可能原因：**
- 回调地址配置错误
- 签名验证失败
- 服务器无法访问

**解决方案：**
1. 检查回调地址配置
2. 验证签名算法
3. 检查服务器网络

#### 问题 3：订单状态未更新

**可能原因：**
- 回调处理逻辑错误
- 数据库连接问题
- 事务处理失败

**解决方案：**
1. 检查回调处理逻辑
2. 验证数据库连接
3. 检查事务处理

### 9.2 调试工具

1. **支付宝调试工具**：
   - 使用支付宝提供的调试工具
   - 检查请求和响应数据

2. **日志分析**：
   - 分析支付日志
   - 查找错误信息

3. **网络抓包**：
   - 使用抓包工具分析网络请求
   - 检查请求和响应数据

## 第十步：生产环境部署

### 10.1 环境变量配置

在生产环境中配置环境变量：

```bash
# 生产环境变量
export ALIPAY_APP_ID="2021001234567890"
export ALIPAY_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----"
export ALIPAY_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----"
export ALIPAY_NOTIFY_URL="https://yourdomain.com/api/v1/payment/alipay/notify"
export ALIPAY_RETURN_URL="https://yourdomain.com/payment/success"
export ALIPAY_DEBUG="false"
```

### 10.2 配置文件管理

使用配置文件管理：

```python
# config.py
import os

class AlipayConfig:
    APP_ID = os.getenv('ALIPAY_APP_ID')
    PRIVATE_KEY = os.getenv('ALIPAY_PRIVATE_KEY')
    PUBLIC_KEY = os.getenv('ALIPAY_PUBLIC_KEY')
    NOTIFY_URL = os.getenv('ALIPAY_NOTIFY_URL')
    RETURN_URL = os.getenv('ALIPAY_RETURN_URL')
    DEBUG = os.getenv('ALIPAY_DEBUG', 'false').lower() == 'true'
```

### 10.3 部署检查

部署前检查清单：

- [ ] 环境变量正确配置
- [ ] 密钥文件安全存储
- [ ] 回调地址可访问
- [ ] SSL 证书有效
- [ ] 防火墙配置正确
- [ ] 日志配置完整

## 第十一步：维护和更新

### 11.1 定期维护

1. **密钥更新**：
   - 定期更新应用私钥
   - 检查支付宝公钥更新

2. **配置检查**：
   - 定期检查配置参数
   - 验证回调地址有效性

3. **性能优化**：
   - 监控支付性能
   - 优化支付流程

### 11.2 版本更新

1. **SDK 更新**：
   - 定期更新支付宝 SDK
   - 测试新版本兼容性

2. **功能更新**：
   - 关注支付宝新功能
   - 及时更新支付方式

### 11.3 备份和恢复

1. **配置备份**：
   - 备份支付配置
   - 备份密钥文件

2. **数据备份**：
   - 备份支付数据
   - 备份订单数据

## 总结

通过本指南，您可以完整配置支付宝生产环境：

1. ✅ 申请支付宝开发者账号
2. ✅ 创建应用并获取配置信息
3. ✅ 生成和管理密钥对
4. ✅ 配置开发和生产环境
5. ✅ 实现支付和回调处理
6. ✅ 配置安全和监控
7. ✅ 处理常见问题
8. ✅ 部署到生产环境
9. ✅ 维护和更新

配置完成后，您的 XBoard 项目将支持真实的支付宝支付功能，为用户提供完整的支付体验。

## 技术支持

如果在配置过程中遇到问题，请：

1. 查看支付宝官方文档
2. 检查配置参数
3. 分析错误日志
4. 联系技术支持

**支付宝开放平台**: https://open.alipay.com/
**支付宝文档**: https://opendocs.alipay.com/
**技术支持**: https://opendocs.alipay.com/support
