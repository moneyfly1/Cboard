# VPS部署配置指南

## 🚀 自动域名配置系统

本系统已实现自动域名检测和配置功能，支持VPS部署时的动态域名替换。

## 📋 部署前准备

### 1. 环境变量配置

创建 `.env` 文件：

```bash
# 基本配置
PROJECT_NAME=XBoard Modern
VERSION=1.0.0
DEBUG=False
SECRET_KEY=your-super-secret-key-here

# 域名配置（重要！）
DOMAIN_NAME=your-actual-domain.com
SSL_ENABLED=true
FRONTEND_DOMAIN=your-actual-domain.com  # 可选，如果前端使用不同域名

# 数据库配置
DATABASE_URL=sqlite:///./xboard.db

# CORS配置（自动使用DOMAIN_NAME）
BACKEND_CORS_ORIGINS=["https://your-actual-domain.com","https://www.your-actual-domain.com"]

# 邮件配置
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USERNAME=your-email@your-actual-domain.com
SMTP_PASSWORD=your-email-password
SMTP_ENCRYPTION=tls
FROM_EMAIL=noreply@your-actual-domain.com
FROM_NAME=XBoard Modern

# 前端配置
VITE_API_BASE_URL=https://your-actual-domain.com
VITE_CONTACT_EMAIL=support@your-actual-domain.com
```

### 2. 系统配置

系统会自动从以下来源获取域名信息（按优先级）：

1. **请求头中的Host**（最高优先级）
2. **环境变量** `DOMAIN_NAME`
3. **数据库配置** `system_configs` 表
4. **默认值**（开发环境）

## 🔧 自动配置功能

### 1. 域名自动检测

系统会自动检测：
- 当前请求的域名
- SSL状态（通过 `X-Forwarded-Proto` 头）
- 前端和后端域名

### 2. 动态URL生成

所有URL都会自动使用正确的域名：
- 订阅地址：`https://your-domain.com/api/v1/subscriptions/...`
- 支付回调：`https://your-domain.com/api/v1/payment/...`
- 邮件链接：`https://your-domain.com/dashboard`

### 3. 邮件模板自动适配

邮件模板会自动使用：
- 正确的域名
- 真实的用户数据
- 动态生成的订阅地址

## 🛠️ 部署步骤

### 1. 上传代码

```bash
# 克隆或上传代码到VPS
git clone your-repo-url
cd xboard
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp env.production.example .env

# 编辑环境变量
nano .env
```

### 3. 安装依赖

```bash
# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

### 4. 构建前端

```bash
# 设置环境变量
export VITE_API_BASE_URL=https://your-actual-domain.com
export VITE_CONTACT_EMAIL=support@your-actual-domain.com

# 构建
npm run build
```

### 5. 配置Nginx

```nginx
server {
    listen 80;
    server_name your-actual-domain.com www.your-actual-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-actual-domain.com www.your-actual-domain.com;
    
    # SSL配置
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # 前端静态文件
    location / {
        root /path/to/xboard/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # 后端API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6. 启动服务

```bash
# 启动后端
python main.py

# 或使用systemd服务
sudo systemctl start xboard
sudo systemctl enable xboard
```

## 🔍 验证配置

### 1. 检查域名配置

访问管理后台的域名配置页面：
- 检查域名是否正确显示
- 测试域名配置功能
- 验证SSL状态

### 2. 测试邮件功能

- 发送测试邮件
- 检查邮件中的链接是否正确
- 验证订阅地址格式

### 3. 测试支付功能

- 创建测试订单
- 检查支付回调URL
- 验证支付成功邮件

## 🚨 常见问题

### 1. 域名不自动更新

**问题**：系统仍使用旧域名
**解决**：
- 检查环境变量 `DOMAIN_NAME`
- 清除浏览器缓存
- 重启服务

### 2. SSL检测错误

**问题**：系统认为未启用SSL
**解决**：
- 检查Nginx配置中的 `X-Forwarded-Proto` 头
- 设置环境变量 `SSL_ENABLED=true`

### 3. 邮件链接错误

**问题**：邮件中的链接使用错误域名
**解决**：
- 检查邮件模板配置
- 验证域名配置API
- 重新发送邮件

## 📝 配置API

系统提供域名配置API：

```bash
# 获取当前配置
GET /api/v1/domain-config

# 更新配置
POST /api/v1/domain-config
{
    "domain_name": "your-domain.com",
    "ssl_enabled": true
}

# 自动检测配置
GET /api/v1/domain-config/auto-detect

# 测试配置
POST /api/v1/domain-config/test
```

## 🔒 安全注意事项

1. **环境变量安全**：确保 `.env` 文件不被公开访问
2. **SSL配置**：生产环境必须使用HTTPS
3. **防火墙**：只开放必要端口
4. **定期备份**：配置数据库和文件
5. **监控日志**：关注系统运行状态

---

通过以上配置，系统将自动适配VPS环境，无需手动修改代码中的域名配置。
