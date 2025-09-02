# XBoard Modern 安装指南

## 🚀 快速安装

### 一键安装（推荐）

```bash
# 克隆项目
git clone <your-repo-url>
cd xboard-modern

# 运行智能安装脚本
./install_xboard_complete.sh
```

### 安装脚本特性

- ✅ **智能环境检测** - 自动检测操作系统、Python版本、Node.js等
- ✅ **重复安装保护** - 检测现有安装，跳过已完成的步骤
- ✅ **数据库连通性测试** - 自动测试数据库连接和初始化
- ✅ **API连通性测试** - 测试后端服务是否正常启动
- ✅ **跨平台支持** - 支持Linux、macOS和Windows（WSL）
- ✅ **自动配置** - 自动创建环境变量文件和启动脚本

## 🔧 系统要求

### 最低要求
- **操作系统**: Linux (Ubuntu 18.04+ / CentOS 7+) / macOS 10.14+ / Windows 10+ (WSL)
- **内存**: 2GB RAM
- **磁盘**: 20GB 可用空间
- **Python**: 3.8+
- **Node.js**: 16+ (可选，用于前端构建)

### 推荐配置
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / macOS 11+
- **内存**: 4GB+ RAM
- **磁盘**: 50GB+ 可用空间
- **Python**: 3.9+
- **Node.js**: 18+

## 📋 安装步骤

### 1. 环境检查
安装脚本会自动检查：
- 操作系统兼容性
- 内存和磁盘空间
- Python环境
- Node.js环境（可选）
- 数据库环境（MySQL/Redis/SQLite）

### 2. 项目路径检测
脚本会自动检测项目目录，支持：
- 当前目录运行
- 脚本在项目目录内
- 脚本在项目父目录

### 3. 依赖安装
- 创建Python虚拟环境
- 安装Python依赖包
- 安装前端依赖包
- 构建前端项目

### 4. 配置管理
- 自动创建`.env`配置文件
- 生成随机安全密钥
- 配置数据库连接
- 设置邮件和支付参数

### 5. 数据库初始化
- 测试数据库连接
- 创建数据库表
- 验证数据模型

### 6. 连通性测试
- 测试API服务启动
- 验证数据库连接
- 检查前端构建

### 7. 启动脚本
- 创建`start.sh`启动脚本
- 创建`stop.sh`停止脚本
- 配置服务管理

## 🗄️ 数据库支持

### SQLite (默认)
- 无需额外安装
- 适合开发和测试
- 自动创建数据库文件

### MySQL
```bash
# 设置环境变量
export USE_MYSQL=true
export MYSQL_HOST=localhost
export MYSQL_USER=xboard_user
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=xboard_db

# 运行安装脚本
./install_xboard_complete.sh
```

### PostgreSQL
```bash
# 设置环境变量
export USE_POSTGRES=true
export POSTGRES_SERVER=localhost
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password
export POSTGRES_DB=xboard

# 运行安装脚本
./install_xboard_complete.sh
```

## ⚙️ 环境变量配置

安装完成后，编辑`.env`文件配置：

```bash
# 数据库配置
DATABASE_URL=sqlite:///./xboard.db

# 邮件配置
SMTP_HOST=smtp.qq.com
SMTP_USERNAME=your-email@qq.com
SMTP_PASSWORD=your-email-password

# 支付配置
ALIPAY_APP_ID=your-alipay-app-id
ALIPAY_PRIVATE_KEY=your-private-key
ALIPAY_PUBLIC_KEY=alipay-public-key

# 安全配置
SECRET_KEY=your-secret-key
JWT_EXPIRE_HOURS=24
```

## 🚀 启动服务

### 开发环境
```bash
# 启动服务
./start.sh

# 停止服务
./stop.sh
```

### 生产环境
```bash
# 使用Gunicorn启动后端
cd backend
source ../venv/bin/activate
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 使用Nginx服务前端
# 配置Nginx指向 frontend/dist 目录
```

## 🔍 故障排除

### 常见问题

#### 1. Python版本过低
```bash
# 升级Python到3.8+
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-pip
```

#### 2. 依赖安装失败
```bash
# 清理虚拟环境重新安装
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### 3. 数据库连接失败
```bash
# 检查数据库配置
cat .env | grep DATABASE

# 测试数据库连接
python3 test_db_connection.py
```

#### 4. 前端构建失败
```bash
# 检查Node.js版本
node --version

# 清理并重新安装依赖
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### 日志查看
```bash
# 查看后端日志
tail -f backend/logs/app.log

# 查看安装日志
tail -f install.log
```

## 📚 更多信息

- **项目文档**: [docs/](docs/)
- **API文档**: http://localhost:8000/docs
- **前端地址**: http://localhost:8080
- **后端地址**: http://localhost:8000

## 🤝 技术支持

如果遇到问题，请：
1. 查看故障排除部分
2. 检查日志文件
3. 提交Issue到项目仓库
4. 联系技术支持团队

---

*XBoard Modern - 现代化订阅管理系统* 