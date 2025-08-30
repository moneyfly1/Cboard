# XBoard Modern - 高性能面板系统

## 📖 项目简介

XBoard Modern 是一个基于现代技术栈构建的高性能面板系统，采用前后端分离架构，提供完整的用户管理、订阅管理、支付系统、主题管理等功能。

## 🚀 技术栈

### 后端
- **框架**: Python + FastAPI
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **ORM**: SQLAlchemy
- **认证**: JWT
- **邮件**: SMTP
- **缓存**: Redis

### 前端
- **框架**: Vue 3 + Composition API
- **路由**: Vue Router 4
- **状态管理**: Pinia
- **UI组件**: Element Plus
- **构建工具**: Vite
- **样式**: SCSS

### 部署
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **进程管理**: Uvicorn

## 📁 项目结构

```
xboard-modern/
├── backend/                 # 后端代码
│   ├── app/                # 应用代码
│   │   ├── api/           # API接口
│   │   ├── core/          # 核心配置
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # 数据验证
│   │   ├── services/      # 业务逻辑
│   │   └── utils/         # 工具函数
│   ├── main.py            # 应用入口
│   └── requirements.txt   # 依赖包
├── frontend/               # 前端代码
│   ├── src/               # 源代码
│   │   ├── components/    # 组件
│   │   ├── views/         # 页面
│   │   ├── store/         # 状态管理
│   │   ├── router/        # 路由
│   │   ├── utils/         # 工具函数
│   │   └── styles/        # 样式文件
│   ├── package.json       # 依赖配置
│   └── vite.config.js     # 构建配置
├── nginx/                  # Nginx配置
├── docs/                   # 文档
├── docker-compose.yml      # Docker编排
├── env.example            # 环境变量示例
├── dev.sh                 # 开发环境启动脚本
└── start.sh               # 生产环境启动脚本
```

## ✨ 主要功能

### 用户管理
- 用户注册/登录
- 邮箱验证
- 密码重置
- 用户资料管理
- 权限控制

### 订阅管理
- 订阅创建/续费
- 设备管理
- 流量统计
- 到期提醒

### 支付系统
- 多支付方式支持
- 支付宝/微信支付
- PayPal/Stripe
- 加密货币支付
- 支付回调处理

### 管理后台
- 用户管理
- 订阅管理
- 订单管理
- 套餐管理
- 系统设置
- 数据统计

### 主题系统
- 多主题支持
- 动态主题切换
- 响应式设计
- 移动端优化

### 系统设置
- 基本设置
- 邮件配置
- 支付配置
- 主题配置
- 安全设置
- 性能优化

## 🛠️ 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- Docker & Docker Compose

### 开发环境

1. **克隆项目**
```bash
git clone <repository-url>
cd xboard-modern
```

2. **启动开发环境**
```bash
./dev.sh
```

3. **访问应用**
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 生产环境

1. **配置环境变量**
```bash
cp env.example .env
# 编辑 .env 文件，配置数据库、邮件等
```

2. **启动生产环境**
```bash
./start.sh
```

## 📚 文档

详细文档请查看 `docs/` 目录：

- [项目概述](docs/PROJECT_SUMMARY.md)
- [后端开发总结](docs/BACKEND_DEVELOPMENT_SUMMARY.md)
- [前端页面检查](docs/FRONTEND_PAGES_CHECK.md)
- [支付系统总结](docs/PAYMENT_SYSTEM_SUMMARY.md)
- [系统设置总结](docs/SYSTEM_SETTINGS_SUMMARY.md)
- [主题优化总结](docs/THEME_OPTIMIZATION_SUMMARY.md)
- [项目结构优化](docs/PROJECT_STRUCTURE_OPTIMIZATION.md)

## 🔧 配置说明

### 环境变量
- `DATABASE_URL`: 数据库连接地址
- `SECRET_KEY`: JWT密钥
- `SMTP_HOST`: SMTP服务器地址
- `SMTP_PORT`: SMTP端口
- `SMTP_USERNAME`: SMTP用户名
- `SMTP_PASSWORD`: SMTP密码

### 系统设置
系统支持通过管理后台动态配置：
- 网站基本信息
- 注册设置
- 邮件配置
- 支付配置
- 主题设置
- 安全设置
- 性能优化

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📞 支持

如有问题，请提交 Issue 或联系开发团队。 