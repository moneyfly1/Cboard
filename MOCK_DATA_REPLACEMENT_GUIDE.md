# 模拟数据替换指南

## 📋 概述

本文档列出了项目中所有需要替换的模拟数据，以及如何正确配置这些值以用于生产环境。

## 🔧 需要配置的项目

### 1. 域名配置

**需要替换**: `yourdomain.com` 和 `localhost`

**文件位置**:
- `app/api/api_v1/endpoints/admin.py`
- `app/services/payment.py`
- `app/services/email_template_enhanced.py`
- `app/services/config_update_service.py`

**配置方法**:
```bash
# 设置环境变量
export DOMAIN_NAME="your-actual-domain.com"
export BASE_URL="https://your-actual-domain.com"
```

### 2. 邮件配置

**需要替换**: `yourdomain.com` 邮箱地址

**文件位置**:
- `uploads/config/system/system.conf`
- `frontend/src/views/Help.vue`
- `app/services/email_template_enhanced.py`

**配置方法**:
```bash
# 系统配置文件
smtp_host = smtp.your-actual-domain.com
smtp_username = noreply@your-actual-domain.com
alert_email = admin@your-actual-domain.com

# 帮助页面
support@your-actual-domain.com
```

### 3. 支付配置

**需要替换**: PayPal、支付宝等支付方式的占位符

**文件位置**:
- `app/services/payment.py`
- `app/services/order.py`

**配置方法**:
1. 在管理后台配置真实的支付方式
2. 设置正确的回调URL
3. 配置真实的支付网关地址

### 4. 代理服务器配置

**需要替换**: 示例代理服务器配置

**文件位置**:
- `app/api/api_v1/endpoints/admin.py`

**配置方法**:
1. 在管理后台的配置管理中
2. 替换Clash和V2Ray配置中的示例服务器
3. 设置真实的服务器IP、端口、密码等

### 5. 教程链接

**已修复**: 所有教程链接现在指向本地帮助页面

**文件位置**:
- `frontend/src/views/Dashboard.vue`

**说明**: 教程链接已改为指向 `/help#软件名称` 格式，用户可以在帮助页面添加具体的教程内容。

## 🚀 部署前检查清单

### 必须配置的项目
- [ ] 域名配置（替换所有 `yourdomain.com`）
- [ ] 邮件服务器配置
- [ ] 支付方式配置
- [ ] 代理服务器配置
- [ ] SSL证书配置

### 可选配置的项目
- [ ] 联系信息（邮箱、QQ群等）
- [ ] 帮助页面内容
- [ ] 软件下载链接
- [ ] 教程内容

## 📝 配置步骤

### 1. 环境变量配置
```bash
# 创建生产环境配置文件
cp env.example .env.production

# 编辑配置文件
vim .env.production
```

### 2. 数据库配置
```bash
# 更新系统配置
UPDATE system_configs SET value = 'https://your-actual-domain.com' WHERE key = 'base_url';
```

### 3. 前端配置
```bash
# 构建前端时设置正确的API地址
npm run build -- --mode production
```

## ⚠️ 安全注意事项

1. **不要使用默认密码**: 确保所有默认密码都已更改
2. **配置HTTPS**: 生产环境必须使用HTTPS
3. **设置防火墙**: 限制不必要的端口访问
4. **定期备份**: 设置自动备份机制
5. **监控日志**: 启用日志监控和告警

## 🔍 验证配置

### 1. 功能测试
- [ ] 用户注册和登录
- [ ] 支付功能测试
- [ ] 邮件发送测试
- [ ] 订阅生成测试

### 2. 安全检查
- [ ] 所有模拟数据已替换
- [ ] 默认密码已更改
- [ ] HTTPS配置正确
- [ ] 敏感信息已加密

## 📞 技术支持

如果在配置过程中遇到问题，请：
1. 查看相关日志文件
2. 检查配置文件格式
3. 验证网络连接
4. 联系技术支持团队

---

**注意**: 本指南涵盖了主要的配置项目，实际部署时请根据具体需求进行调整。
