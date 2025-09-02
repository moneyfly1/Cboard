# XBoard Modern

一个现代化的订阅管理系统，基于 Python FastAPI + Vue 3 构建。

## 功能特性

### 用户端功能
- 🔐 用户认证（QQ邮箱注册、登录、密码重置）
- 📱 订阅管理（查看状态、重置地址、设备管理）
- 💳 套餐购买（多种支付方式）
- 📊 订单记录
- 🌐 节点列表
- 📧 邮件通知
- 🎨 主题切换

### 管理端功能
- 👥 用户管理（增删改查、批量操作）
- 📦 订阅管理（状态管理、设备监控）
- 💰 订单管理
- 🎯 套餐管理
- ⚙️ 系统设置（统一配置中心）
- 📈 数据统计
- 📢 通知管理
- 🔧 配置管理

## 技术栈

### 后端
- **Python 3.8+**
- **FastAPI** - 现代化Web框架
- **SQLAlchemy** - ORM
- **Pydantic** - 数据验证
- **JWT** - 身份认证
- **SQLite/MySQL/PostgreSQL** - 数据库
- **Uvicorn** - ASGI服务器

### 前端
- **Vue 3** - 渐进式框架
- **Element Plus** - UI组件库
- **Vite** - 构建工具
- **Vue Router 4** - 路由管理
- **Pinia** - 状态管理
- **Axios** - HTTP客户端

### 部署
- **Docker** - 容器化
- **Nginx** - 反向代理
- **Systemd** - 服务管理

## 快速开始

### VPS一键部署（推荐）
```bash
# 在您的VPS上执行（需要root权限）
git clone https://github.com/moneyfly1/xboard.git
cd xboard/xboard-modern

# 自动安装
sudo ./install_vps_complete.sh --auto

# 或手动配置安装
sudo ./install_vps_complete.sh
```

### 本地开发环境

#### 系统要求
- Python 3.8+
- Node.js 16+
- 数据库（SQLite/MySQL/PostgreSQL）

#### Linux/macOS
```bash
# 下载项目
git clone https://github.com/moneyfly1/xboard.git
cd xboard/xboard-modern

# 运行安装脚本
chmod +x install_complete.sh
./install_complete.sh
```

#### Windows
```cmd
# 下载项目
git clone https://github.com/moneyfly1/xboard.git
cd xboard\xboard-modern

# 运行安装脚本
install_windows.bat
```

### 数据库配置（重要）

XBoard Modern 支持多种数据库：

- ✅ **SQLite** - 推荐用于开发环境
- ✅ **MySQL/MariaDB** - 推荐用于生产环境
- ✅ **PostgreSQL** - 适用于大型应用

📖 [详细的数据库配置指南](README_DATABASE.md)

### 手动安装

1. **克隆项目**
```bash
git clone https://github.com/moneyfly1/xboard.git
cd xboard/xboard-modern
```

2. **配置数据库**
```bash
# 运行数据库配置脚本
python3 setup_database.py

# 或手动配置
cp .env.example .env
# 编辑 .env 文件配置数据库连接
```

3. **安装后端依赖**
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate.bat  # Windows

# 安装依赖
pip install -r backend/requirements.txt
```

3. **安装前端依赖**
```bash
cd frontend
npm install
npm run build
cd ..
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库、邮件等信息
```

5. **初始化数据库**
```bash
cd backend
python -c "from app.core.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
cd ..
```

6. **启动服务**
```bash
# 开发模式
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 配置说明

### 环境变量

创建 `.env` 文件并配置以下变量：

```env
# 数据库配置
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./xboard.db

# 应用配置
APP_NAME=XBoard Modern
SECRET_KEY=your-secret-key-here

# 管理员配置
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-password

# 邮件配置
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@qq.com
EMAIL_PASSWORD=your-password
SENDER_NAME=XBoard

# 缓存配置
CACHE_TYPE=memory
CACHE_DEFAULT_TIMEOUT=300

# 安全配置
JWT_SECRET_KEY=your-jwt-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 支付配置
ALIPAY_APP_ID=your-alipay-app-id
ALIPAY_PRIVATE_KEY=your-alipay-private-key
ALIPAY_PUBLIC_KEY=your-alipay-public-key
```

### 数据库配置

#### SQLite（推荐开发环境）
```env
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./xboard.db
```

#### MySQL
```env
DATABASE_TYPE=mysql
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/xboard
```

#### PostgreSQL
```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@localhost:5432/xboard
```

### 邮件配置

#### QQ邮箱
```env
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
EMAIL_USERNAME=your-qq@qq.com
EMAIL_PASSWORD=your-authorization-code
```

#### 163邮箱
```env
SMTP_HOST=smtp.163.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@163.com
EMAIL_PASSWORD=your-authorization-code
```

## 部署指南

### VPS 生产环境部署
📖 [详细的VPS部署指南](README_VPS.md) - 推荐阅读

### Docker部署

1. **构建镜像**
```bash
docker build -t xboard-modern .
```

2. **运行容器**
```bash
docker run -d \
  --name xboard \
  -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  xboard-modern
```

### 宝塔面板部署

1. **上传项目文件到网站目录**
2. **运行安装脚本**
```bash
cd /www/wwwroot/your-domain
chmod +x install_complete.sh
./install_complete.sh
```

3. **配置Nginx反向代理**
```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 系统服务

创建systemd服务文件：

```ini
[Unit]
Description=XBoard Backend Service
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/xboard-modern
Environment=PATH=/path/to/xboard-modern/venv/bin
ExecStart=/path/to/xboard-modern/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl enable xboard-backend
sudo systemctl start xboard-backend
```

## API文档

启动服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发指南

### 项目结构

```
xboard-modern/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # 数据验证
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   ├── requirements.txt    # Python依赖
│   └── main.py            # 应用入口
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面
│   │   ├── router/         # 路由
│   │   ├── store/          # 状态管理
│   │   └── utils/          # 工具函数
│   ├── package.json        # Node.js依赖
│   └── vite.config.js      # Vite配置
├── docs/                   # 文档
├── install_complete.sh     # Linux安装脚本
├── install_windows.bat     # Windows安装脚本
└── uninstall.sh           # 卸载脚本
```

### 开发模式

1. **启动后端**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **启动前端**
```bash
cd frontend
npm run dev
```

### 代码规范

- 后端使用 `black` 格式化代码
- 前端使用 `prettier` 格式化代码
- 遵循 PEP 8 和 Vue 3 官方规范

## 常见问题

### Q: 安装时遇到依赖问题？
A: 确保使用Python 3.8+和Node.js 16+，对于ARM架构，脚本会自动适配兼容版本。

### Q: 邮件发送失败？
A: 检查SMTP配置，确保使用正确的授权码而非登录密码。

### Q: 数据库连接失败？
A: 检查数据库配置，确保数据库服务正在运行。

### Q: 前端构建失败？
A: 确保Node.js版本正确，清除node_modules后重新安装。

### Q: 宝塔面板冲突？
A: 安装脚本已优化，不会重启现有服务，避免与宝塔面板冲突。

## 更新日志

### v1.0.0
- 初始版本发布
- 完整的用户和管理功能
- 支持多种数据库
- 响应式设计
- 主题系统

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 支持

如有问题，请提交 Issue 或联系开发者。

---

**XBoard Modern** - 现代化的订阅管理系统 