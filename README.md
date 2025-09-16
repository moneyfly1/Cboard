# CBoard 系统

一个现代化的订阅管理系统，支持用户管理、套餐订阅、订单处理等功能。

## 🚀 快速开始

### 系统要求
- Python 3.8+
- Node.js 16+
- npm 或 yarn
- SQLite3

### 一键安装
```bash
# 克隆项目
git clone <your-repo-url>
cd xboard

# 运行安装脚本
chmod +x install.sh
./install.sh
```

### 启动系统
```bash
# 启动所有服务
./start_all.sh

# 或者分别启动
./start_backend.sh    # 启动后端
./start_frontend.sh   # 启动前端
```

### 停止系统
```bash
./stop_all.sh
```

## 📱 访问地址
- **前端**: http://localhost:5173
- **后端**: http://127.0.0.1:8000
- **健康检查**: http://127.0.0.1:8000/health

## 🔐 初始账户
- **管理员**: 请通过安装脚本创建管理员账户
- **普通用户**: 请通过注册页面创建用户账户

## 🏗️ 项目结构
```
xboard/
├── app/                    # 后端应用代码
│   ├── api/               # API 路由
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── schemas/           # 数据验证
│   ├── services/          # 业务逻辑
│   └── utils/             # 工具函数
├── frontend/              # 前端 Vue.js 应用
├── static/                # 静态文件
├── uploads/               # 上传文件
├── nginx/                 # Nginx 配置
├── main.py                # 后端入口文件
├── requirements.txt       # Python 依赖
├── install.sh             # 安装脚本
├── database_setup.sql     # 数据库初始化
└── xboard.db             # SQLite 数据库
```

## 🛠️ 技术栈

### 后端
- **FastAPI** - 现代、快速的 Web 框架
- **SQLAlchemy** - Python ORM
- **SQLite** - 轻量级数据库
- **JWT** - 身份认证
- **Pydantic** - 数据验证

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 快速构建工具
- **SCSS** - CSS 预处理器
- **Axios** - HTTP 客户端

## 📊 功能特性
- ✅ 用户认证和授权
- ✅ 套餐管理
- ✅ 订阅管理
- ✅ 订单处理
- ✅ 支付配置
- ✅ 通知系统
- ✅ 邮件系统
- ✅ 设备管理
- ✅ 节点管理

## 🔧 开发

### 后端开发
```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python -m uvicorn main:app --reload
```

### 前端开发
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 📝 数据库

### 初始化数据库
```bash
sqlite3 xboard.db < database_setup.sql
```

### 查看数据库
```bash
sqlite3 xboard.db
.tables
.schema users
```

## 🚀 部署

### 生产环境
1. 配置环境变量
2. 使用 Gunicorn 或 uWSGI 部署后端
3. 使用 Nginx 部署前端
4. 配置 SSL 证书

### Docker 部署
```bash
docker-compose up -d
```

## 📚 文档
- [API 文档](http://127.0.0.1:8000/docs) - 后端 API 文档
- [测试账户](TEST_ACCOUNTS.md) - 测试账户信息

## 🤝 贡献
欢迎提交 Issue 和 Pull Request！

## 📄 许可证
MIT License 
