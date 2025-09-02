# XBoard 邮件系统完整指南

## 概述

XBoard邮件系统是一个完整的、企业级的邮件解决方案，包含邮件模板管理、异步队列处理、监控统计等功能。系统完全兼容你的VPS环境（MySQL 5.7、Redis 7.4、Nginx 1.28）。

## 系统特性

### ✅ 已实现功能

1. **邮件模板系统**
   - 使用数据库模板替代硬编码
   - 支持Jinja2模板语法
   - 模板变量验证和管理
   - 模板预览和测试功能

2. **异步邮件队列**
   - 真正的异步队列处理
   - 智能重试机制
   - 失败邮件处理
   - 队列状态监控

3. **邮件模板管理**
   - 完整的CRUD操作
   - 模板状态管理（激活/停用）
   - 模板复制和版本控制
   - 变量说明和验证

4. **监控和统计**
   - 实时邮件发送统计
   - 队列健康度监控
   - 性能指标分析
   - 失败邮件重试

5. **用户体验优化**
   - HTML邮件支持
   - 邮件预览功能
   - 响应式管理界面
   - 实时状态更新

## VPS环境兼容性

### 环境要求

- **操作系统**: Ubuntu 18.04+ / Debian 9+
- **Python**: 3.9+
- **MySQL**: 5.7+
- **Redis**: 7.0+
- **Nginx**: 1.18+

### 兼容性解决方案

1. **MySQL 5.7兼容**
   - 使用mysqlclient 2.1.1版本
   - 优化SQL查询语法
   - 添加字符集支持

2. **Redis 7.4兼容**
   - 使用redis 4.5.4版本
   - 支持新版本特性
   - 保持向后兼容

3. **系统依赖**
   - 自动安装Python开发包
   - 配置系统库路径
   - 设置正确的权限

## 快速部署

### 1. 自动部署（推荐）

```bash
# 下载部署脚本
wget https://raw.githubusercontent.com/your-repo/xboard/main/deploy_email_system.sh

# 设置执行权限
chmod +x deploy_email_system.sh

# 运行部署脚本
sudo ./deploy_email_system.sh
```

### 2. 手动部署

```bash
# 克隆项目
git clone https://github.com/your-repo/xboard.git
cd xboard

# 运行环境适配脚本
sudo python3 setup_vps_environment.py

# 安装依赖
pip install -r requirements_vps.txt

# 启动邮件系统
python start_email_system.py
```

## 配置说明

### 环境变量配置

创建 `.env` 文件：

```bash
# 数据库配置
DATABASE_URL=mysql://username:password@localhost/xboard?charset=utf8mb4

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 邮件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_ENCRYPTION=tls
SMTP_FROM_NAME=XBoard System
SMTP_FROM_EMAIL=noreply@yourdomain.com

# 安全配置
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 应用配置
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

### Nginx配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /var/www/xboard/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 使用指南

### 1. 邮件模板管理

#### 创建模板

```python
from app.services.email_template import EmailTemplateService

# 创建模板服务
template_service = EmailTemplateService(db)

# 创建新模板
template_data = {
    "name": "welcome",
    "subject": "欢迎使用 {{site_name}}",
    "content": "<h1>欢迎 {{username}}</h1>",
    "variables": '["username", "site_name"]',
    "is_active": True
}

template = template_service.create_template(template_data)
```

#### 发送模板邮件

```python
from app.services.email_enhanced import EnhancedEmailService

# 创建邮件服务
email_service = EnhancedEmailService(db)

# 发送模板邮件
variables = {
    "username": "张三",
    "site_name": "XBoard"
}

success = email_service.send_template_email(
    "welcome",
    "user@example.com",
    variables
)
```

### 2. 队列管理

#### 启动队列处理器

```python
from app.services.email_queue_processor import get_email_queue_processor

# 获取队列处理器
processor = get_email_queue_processor()

# 启动处理
processor.start_processing()

# 检查状态
if processor.is_running:
    print("队列处理器运行中")
```

#### 监控队列状态

```python
# 获取队列统计
stats = processor.get_queue_stats()
print(f"待处理邮件: {stats['pending']}")
print(f"已发送邮件: {stats['sent']}")
print(f"失败邮件: {stats['failed']}")
```

### 3. 邮件统计

#### 获取概览统计

```python
from app.services.email import EmailService

email_service = EmailService(db)
stats = email_service.get_email_stats()

print(f"总邮件数: {stats['total']}")
print(f"成功率: {(stats['sent'] / stats['total']) * 100:.2f}%")
```

#### 每日统计

```python
# 获取最近7天的统计
daily_stats = email_service.get_daily_email_stats(7)

for day in daily_stats:
    print(f"{day['date']}: 发送 {day['sent']}, 失败 {day['failed']}")
```

## API接口

### 邮件模板API

- `GET /api/v1/email-templates/` - 获取模板列表
- `POST /api/v1/email-templates/` - 创建模板
- `PUT /api/v1/email-templates/{id}` - 更新模板
- `DELETE /api/v1/email-templates/{id}` - 删除模板
- `POST /api/v1/email-templates/preview` - 预览模板
- `POST /api/v1/email-templates/test` - 测试模板

### 邮件统计API

- `GET /api/v1/email-stats/overview` - 概览统计
- `GET /api/v1/email-stats/daily` - 每日统计
- `GET /api/v1/email-stats/by-type` - 按类型统计
- `POST /api/v1/email-stats/queue/start` - 启动队列
- `POST /api/v1/email-stats/queue/stop` - 停止队列

## 监控和维护

### 1. 服务状态监控

```bash
# 检查邮件系统状态
sudo systemctl status xboard-email

# 查看实时日志
sudo journalctl -u xboard-email -f

# 检查队列状态
curl http://localhost:8000/api/v1/email-stats/queue/status
```

### 2. 性能监控

```bash
# 查看邮件统计
curl http://localhost:8000/api/v1/email-stats/overview

# 查看队列健康度
curl http://localhost:8000/api/v1/email-stats/performance
```

### 3. 故障排查

#### 常见问题

1. **邮件发送失败**
   - 检查SMTP配置
   - 查看错误日志
   - 验证网络连接

2. **队列处理异常**
   - 检查Redis连接
   - 查看队列状态
   - 重启队列处理器

3. **模板渲染错误**
   - 检查模板语法
   - 验证变量定义
   - 查看错误日志

## 安全建议

### 1. 访问控制

- 使用HTTPS加密传输
- 设置强密码策略
- 启用API访问限制

### 2. 数据保护

- 定期备份数据库
- 加密敏感信息
- 设置访问日志

### 3. 系统安全

- 定期更新系统
- 配置防火墙规则
- 监控异常访问

## 性能优化

### 1. 数据库优化

- 添加适当的索引
- 优化查询语句
- 定期清理旧数据

### 2. 队列优化

- 调整批处理大小
- 优化重试策略
- 监控队列性能

### 3. 缓存优化

- 使用Redis缓存
- 优化模板渲染
- 减少数据库查询

## 扩展功能

### 1. 邮件分类

- 按类型分类
- 按优先级处理
- 支持批量发送

### 2. 高级模板

- 条件渲染
- 循环结构
- 自定义函数

### 3. 集成功能

- Webhook支持
- API集成
- 第三方服务

## 技术支持

### 1. 文档资源

- [API文档](https://your-domain.com/docs/api)
- [用户手册](https://your-domain.com/docs/user)
- [开发者指南](https://your-domain.com/docs/dev)

### 2. 社区支持

- [GitHub Issues](https://github.com/your-repo/xboard/issues)
- [讨论论坛](https://your-domain.com/forum)
- [邮件支持](support@yourdomain.com)

### 3. 商业支持

- 专业技术支持
- 定制开发服务
- 培训和技术咨询

## 更新日志

### v1.0.0 (2024-01-XX)

- ✅ 完整的邮件模板系统
- ✅ 异步队列处理
- ✅ 实时监控统计
- ✅ VPS环境兼容
- ✅ 管理界面
- ✅ API接口
- ✅ 安全配置

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

**注意**: 在生产环境中使用前，请务必：
1. 修改默认密码
2. 配置SSL证书
3. 设置防火墙规则
4. 定期备份数据
5. 监控系统状态
