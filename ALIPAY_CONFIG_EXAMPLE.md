# 支付宝配置指南

## 为什么没有显示支付宝官方二维码？

当前系统运行在**演示模式**下，显示的是模拟的支付URL，而不是支付宝官方二维码。要显示真正的支付宝官方二维码，需要配置真实的支付宝开发者账号。

## 如何配置真实的支付宝支付？

### 1. 申请支付宝开发者账号

1. 访问 [支付宝开放平台](https://open.alipay.com/)
2. 注册并登录开发者账号
3. 创建应用，选择"网页&移动应用"
4. 获取以下信息：
   - **APPID**：应用ID
   - **应用私钥**：商户私钥
   - **支付宝公钥**：支付宝公钥

### 2. 配置支付方式

在数据库中为支付宝支付方式添加配置：

```sql
-- 更新支付宝支付方式配置
UPDATE payment_methods 
SET config = '{
    "app_id": "你的APPID",
    "merchant_private_key": "你的应用私钥",
    "alipay_public_key": "支付宝公钥",
    "notify_url": "http://你的域名/api/v1/payment/alipay/notify",
    "return_url": "http://你的域名/payment/success",
    "debug": false
}'
WHERE type = 'alipay';
```

### 3. 配置示例

```json
{
    "app_id": "2021001234567890",
    "merchant_private_key": "-----BEGIN PRIVATE KEY-----\n你的私钥内容\n-----END PRIVATE KEY-----",
    "alipay_public_key": "-----BEGIN PUBLIC KEY-----\n支付宝公钥内容\n-----END PUBLIC KEY-----",
    "notify_url": "https://yourdomain.com/api/v1/payment/alipay/notify",
    "return_url": "https://yourdomain.com/payment/success",
    "debug": false
}
```

### 4. 测试环境配置

如果使用支付宝沙箱环境进行测试：

```json
{
    "app_id": "沙箱APPID",
    "merchant_private_key": "沙箱应用私钥",
    "alipay_public_key": "沙箱支付宝公钥",
    "notify_url": "http://localhost:8000/api/v1/payment/alipay/notify",
    "return_url": "http://localhost:3000/payment/success",
    "debug": true
}
```

## 当前演示模式说明

在没有配置真实支付宝的情况下，系统会：

1. 生成模拟的支付URL
2. 显示演示用的支付信息
3. 在支付信息中包含提示："这是演示模式，请使用真实的支付宝配置来生成官方二维码"

## 验证配置

配置完成后，创建订单时会：

1. 检查是否有真实的支付宝配置
2. 如果有配置，调用支付宝官方API生成真实的支付二维码
3. 如果没有配置，使用演示模式

## 注意事项

1. **安全性**：私钥和公钥信息需要妥善保管
2. **域名**：notify_url 和 return_url 需要使用真实的域名
3. **HTTPS**：生产环境必须使用HTTPS
4. **测试**：建议先在沙箱环境测试

## 其他支付方式

同样的配置方式也适用于：
- 微信支付
- PayPal
- Stripe
- 其他支付网关

只需要在对应的支付方式配置中添加相应的API密钥和配置信息即可。
