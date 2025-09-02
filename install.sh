#!/bin/bash

# ================================
# XBoard Modern 智能安装脚本
# 支持本地开发环境和VPS生产环境
# 自动检测环境并选择最佳配置
# ================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }

# 全局变量
PROJECT_NAME="XBoard Modern"
PROJECT_VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT=""
DOMAIN=""
DB_TYPE=""
DB_HOST=""
DB_PORT=""
DB_NAME=""
DB_USER=""
DB_PASSWORD=""
ADMIN_EMAIL=""
ADMIN_PASSWORD=""
SSL_CERT_PATH=""
SSL_KEY_PATH=""
INSTALL_MODE="" # auto/manual
ENVIRONMENT_TYPE="" # local/vps
IS_ROOT=false

# 检测运行环境类型
detect_environment() {
    log_info "检测运行环境..."

    # 检查是否为root用户
    if [ "$EUID" -eq 0 ]; then
        IS_ROOT=true
        log_info "检测到root权限"
    else
        IS_ROOT=false
        log_info "检测到普通用户权限"
    fi

    # 检测系统类型
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        OS="rhel"
        OS_VERSION=$(cat /etc/redhat-release | grep -oE '[0-9]+\.[0-9]+' | head -1)
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        OS_VERSION=$(sw_vers -productVersion)
    else
        log_error "无法检测操作系统类型"
        exit 1
    fi

    # 检测内存
    if [[ "$OS" == "macos" ]]; then
        MEM=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024)}')
    else
        MEM=$(free -m 2>/dev/null | awk 'NR==2{printf "%.0f", $2}' || echo "2048")
    fi

    # 检测是否为VPS环境
    # 基于多个指标判断：内存、CPU核心数、磁盘空间、是否有虚拟化特征等
    VPS_INDICATORS=0

    # 内存小于4GB可能是VPS
    if [ $MEM -lt 4096 ]; then
        ((VPS_INDICATORS++))
    fi

    # CPU核心数少可能是VPS
    CPU_CORES=$(nproc 2>/dev/null || echo "4")
    if [ $CPU_CORES -le 2 ]; then
        ((VPS_INDICATORS++))
    fi

    # 检查是否有云服务提供商特征
    if [ -f /sys/devices/virtual/dmi/id/product_name ]; then
        PRODUCT_NAME=$(cat /sys/devices/virtual/dmi/id/product_name)
        case $PRODUCT_NAME in
            *"DigitalOcean"*|*"Linode"*|*"Vultr"*|*"AWS"*|*"Google"*|*"Alibaba"*|*"Tencent"*)
                ((VPS_INDICATORS++))
                ;;
        esac
    fi

    # 检查网络接口（VPS通常有eth0或ens等）
    if ip link show 2>/dev/null | grep -q "eth0\|ens"; then
        ((VPS_INDICATORS++))
    fi

    # 根据指标判断环境类型
    if [ $VPS_INDICATORS -ge 2 ] || [ "$IS_ROOT" = true ]; then
        ENVIRONMENT_TYPE="vps"
        log_info "检测到VPS生产环境 (指标: $VPS_INDICATORS)"
    else
        ENVIRONMENT_TYPE="local"
        log_info "检测到本地开发环境"
    fi

    log_success "环境检测完成: $OS $OS_VERSION, $MEM MB内存, $CPU_CORES CPU核心, 类型: $ENVIRONMENT_TYPE"
}

# 本地开发环境安装函数
install_local() {
    log_info "开始本地开发环境安装..."

    # 检查Python环境
    check_python_local

    # 检查Node.js环境
    check_nodejs_local

    # 创建虚拟环境
    create_venv_local

    # 安装Python依赖
    install_python_deps_local

    # 安装前端依赖
    install_frontend_deps_local

    # 配置环境变量
    configure_env_local

    # 初始化数据库
    init_database_local

    # 构建前端
    build_frontend_local

    # 创建启动脚本
    create_startup_scripts_local
}

# VPS生产环境安装函数
install_vps() {
    log_info "开始VPS生产环境安装..."

    # 检查系统要求
    check_system_requirements_vps

    # 更新系统
    update_system_vps

    # 安装Python
    install_python_vps

    # 安装Node.js
    install_nodejs_vps

    # 检测项目路径
    detect_project_path

    # 选择数据库
    select_database_vps

    # 安装数据库
    install_database_vps

    # 安装Nginx
    install_nginx_vps

    # 设置Python环境
    setup_python_env_vps

    # 构建前端
    build_frontend_vps

    # 配置环境
    configure_env_vps

    # 初始化数据库
    init_database_vps

    # 创建systemd服务
    create_systemd_service_vps

    # 配置防火墙
    configure_firewall_vps

    # 安装SSL证书
    install_ssl_vps

    # 创建备份脚本
    create_backup_script_vps
}

# 本地环境：检查Python
check_python_local() {
    log_info "检查本地Python环境..."

    if ! command -v python3 &> /dev/null; then
        log_error "Python3未安装，请先安装Python 3.8+"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ $PYTHON_MAJOR -lt 3 ] || ([ $PYTHON_MAJOR -eq 3 ] && [ $PYTHON_MINOR -lt 8 ]); then
        log_error "Python版本过低，需要3.8+，当前: $PYTHON_VERSION"
        exit 1
    fi

    log_success "Python环境检查通过: $PYTHON_VERSION"
}

# 本地环境：检查Node.js
check_nodejs_local() {
    log_info "检查本地Node.js环境..."

    if ! command -v node &> /dev/null; then
        log_warning "Node.js未安装，将跳过前端构建"
        return 1
    fi

    NODE_VERSION=$(node --version | sed 's/v//')
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)

    if [ $NODE_MAJOR -lt 16 ]; then
        log_warning "Node.js版本过低，建议16+，当前: $NODE_VERSION"
        return 1
    fi

    log_success "Node.js环境检查通过: $NODE_VERSION"
    return 0
}

# 本地环境：创建虚拟环境
create_venv_local() {
    log_info "创建Python虚拟环境..."

    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "虚拟环境创建成功"
    else
        log_warning "虚拟环境已存在，跳过创建"
    fi
}

# 本地环境：安装Python依赖
install_python_deps_local() {
    log_info "安装Python依赖..."

    source venv/bin/activate
    pip install --upgrade pip

    # 使用简化的requirements文件（移除可能有问题的依赖）
    cat > backend/requirements_local.txt << 'EOF'
# 基础依赖
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# 数据库驱动（仅SQLite用于本地开发）
aiosqlite==0.21.0

# 邮件和模板相关
jinja2==3.1.2
email-validator==2.1.0

# 工具库
httpx==0.25.2
watchfiles==0.21.0
websockets==12.0

# 开发和测试
pytest==7.4.3
EOF

    pip install -r backend/requirements_local.txt
    log_success "Python依赖安装完成"
}

# 本地环境：安装前端依赖
install_frontend_deps_local() {
    log_info "安装前端依赖..."

    if ! command -v npm &> /dev/null; then
        log_warning "npm未安装，跳过前端依赖安装"
        return 1
    fi

    cd frontend
    npm install
    cd ..
    log_success "前端依赖安装完成"
}

# 本地环境：配置环境变量
configure_env_local() {
    log_info "配置环境变量..."

    # 生成随机密钥
    SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || echo "dev-secret-key-12345678901234567890")
    JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || echo "dev-jwt-secret-12345678901234567890")

    # 创建.env文件
    cat > .env << EOF
# ================================
# XBoard Modern 本地开发环境配置
# ================================

# 数据库配置（SQLite用于本地开发）
DATABASE_URL=sqlite:///./xboard_dev.db

# 应用配置
DEBUG=True
HOST=127.0.0.1
PORT=8000
WORKERS=1

# 安全配置
SECRET_KEY=$SECRET_KEY
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_SECRET_KEY=$JWT_SECRET

# 邮件配置（开发环境可使用控制台输出）
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_ENCRYPTION=
SMTP_FROM_EMAIL=dev@xboard.local
SMTP_FROM_NAME=XBoard Dev

# 文件上传配置
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760

# 订阅配置
SUBSCRIPTION_URL_PREFIX=http://localhost:8000/sub
DEVICE_LIMIT_DEFAULT=3

# 管理员配置
ADMIN_EMAIL=admin@xboard.local
ADMIN_PASSWORD=admin123

# 开发模式
DEVELOPMENT_MODE=True
EOF

    log_success "环境变量配置完成"
}

# 本地环境：初始化数据库
init_database_local() {
    log_info "初始化数据库..."

    source venv/bin/activate
    cd backend

    python3 -c "
from app.core.database import init_database
import logging
logging.basicConfig(level=logging.INFO)

if init_database():
    print('数据库初始化成功')
else:
    print('数据库初始化失败')
"

    cd ..
    log_success "数据库初始化完成"
}

# 本地环境：构建前端
build_frontend_local() {
    log_info "构建前端..."

    if ! command -v npm &> /dev/null; then
        log_warning "npm未安装，跳过前端构建"
        return 1
    fi

    cd frontend
    npm run build
    cd ..
    log_success "前端构建完成"
}

# 本地环境：创建启动脚本
create_startup_scripts_local() {
    log_info "创建启动脚本..."

    # 创建开发启动脚本
    cat > dev_start.sh << 'EOF'
#!/bin/bash

# XBoard Modern 本地开发启动脚本

cd "$(dirname "$0")"

echo "启动 XBoard Modern (开发模式)..."
echo ""

# 激活虚拟环境
source venv/bin/activate

# 启动后端（后台运行）
echo "启动后端服务..."
cd backend
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 检查后端是否启动成功
if curl -s http://127.0.0.1:8000/docs > /dev/null; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
fi

# 启动前端（如果有node_modules）
if [ -d "frontend/node_modules" ]; then
    echo "启动前端开发服务器..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
fi

echo ""
echo "🎉 XBoard Modern 开发环境启动完成！"
echo ""
echo "📋 访问地址:"
echo "  后端API: http://127.0.0.1:8000"
echo "  API文档: http://127.0.0.1:8000/docs"
if [ -d "frontend/node_modules" ]; then
    echo "  前端开发: http://127.0.0.1:5173"
fi
echo "  前端构建: http://127.0.0.1:8000 (生产构建)"
echo ""
echo "🛑 按 Ctrl+C 停止服务"

# 等待用户中断
cleanup() {
    echo ""
    echo "正在停止服务..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "服务已停止"
    exit 0
}

trap cleanup INT TERM
wait
EOF

    # 创建生产启动脚本
    cat > start.sh << 'EOF'
#!/bin/bash

# XBoard Modern 本地生产启动脚本

cd "$(dirname "$0")"

echo "启动 XBoard Modern (本地生产模式)..."
echo ""

# 激活虚拟环境
source venv/bin/activate

# 启动后端
echo "启动后端服务..."
cd backend
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
cd ..

# 启动前端静态文件服务
if [ -d "frontend/dist" ]; then
    echo "启动前端静态文件服务..."
    cd frontend/dist
    python3 -m http.server 8080 &
    FRONTEND_PID=$!
    cd ../..
fi

echo ""
echo "🎉 XBoard Modern 本地生产环境启动完成！"
echo ""
echo "📋 访问地址:"
echo "  后端API: http://127.0.0.1:8000"
echo "  前端页面: http://127.0.0.1:8080"
echo "  API文档: http://127.0.0.1:8000/docs"
echo ""
echo "🛑 按 Ctrl+C 停止服务"

# 等待用户中断
cleanup() {
    echo ""
    echo "正在停止服务..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "服务已停止"
    exit 0
}

trap cleanup INT TERM
wait
EOF

    # 创建停止脚本
    cat > stop.sh << 'EOF'
#!/bin/bash

# XBoard Modern 停止脚本

echo "停止 XBoard Modern 服务..."

# 停止所有相关进程
pkill -f "uvicorn app.main:app" || true
pkill -f "python3 -m http.server" || true
pkill -f "npm run dev" || true

echo "✅ 服务已停止"
EOF

    chmod +x dev_start.sh start.sh stop.sh

    log_success "启动脚本创建完成"
}

# VPS环境检查系统要求
check_system_requirements_vps() {
    log_info "检查系统要求..."

    # 检查操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS=$NAME
            VER=$VERSION_ID
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
        VER=$(sw_vers -productVersion)
    else
        log_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi

    # 检查内存
    if [[ "$OS" == "macOS" ]]; then
        MEM=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024)}')
    else
        MEM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    fi

    if [ $MEM -lt 1024 ]; then
        log_error "内存不足，需要至少1GB内存，当前: ${MEM}MB"
        exit 1
    fi

    # 检查磁盘空间
    if [[ "$OS" == "macOS" ]]; then
        DISK=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    else
        DISK=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    fi

    if [ $DISK -lt 5 ]; then
        log_error "磁盘空间不足，需要至少5GB，当前: ${DISK}GB"
        exit 1
    fi

    log_success "系统检查通过: $OS $VER, 内存: ${MEM}MB, 磁盘: ${DISK}GB"
}

# VPS环境更新系统
update_system_vps() {
    log_info "更新系统..."

    case $OS in
        "ubuntu"|"debian")
            apt update && apt upgrade -y
            apt install -y curl wget git unzip software-properties-common ufw
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                dnf update -y
                dnf install -y curl wget git unzip firewalld
            else
                yum update -y
                yum install -y curl wget git unzip firewalld
            fi
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac

    log_success "系统更新完成"
}

# VPS环境安装Python
install_python_vps() {
    log_info "安装Python 3.9+..."

    case $OS in
        "ubuntu")
            if [ "$OS_VERSION" = "20.04" ]; then
                apt install -y python3.9 python3.9-venv python3.9-dev python3-pip
            elif [ "$OS_VERSION" = "22.04" ]; then
                apt install -y python3.10 python3.10-venv python3.10-dev python3-pip
            else
                add-apt-repository ppa:deadsnakes/ppa -y
                apt update
                apt install -y python3.9 python3.9-venv python3.9-dev python3-pip
            fi
            ;;
        "debian")
            apt install -y python3 python3-venv python3-dev python3-pip
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                dnf install -y python39 python39-devel python39-pip
            else
                yum install -y python39 python39-devel python39-pip
            fi
            ;;
    esac

    # 创建python3和pip3的软链接
    ln -sf $(which python3.9 || which python3.10 || which python3) /usr/bin/python3
    ln -sf $(which pip3) /usr/bin/pip3

    log_success "Python安装完成"
}

# VPS环境安装Node.js
install_nodejs_vps() {
    log_info "安装Node.js 18+..."

    case $OS in
        "ubuntu"|"debian")
            curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
            apt install -y nodejs
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
            if command -v dnf &> /dev/null; then
                dnf install -y nodejs
            else
                yum install -y nodejs
            fi
            ;;
    esac

    log_success "Node.js安装完成"
}

# 检测项目路径
detect_project_path() {
    log_info "检测项目路径..."

    # 策略1: 检查当前目录是否就是项目根目录
    if [ -d "backend" ] && [ -d "frontend" ] && [ -f "backend/requirements.txt" ]; then
        PROJECT_ROOT="$(pwd)"
        log_info "检测到当前目录为项目根目录: $PROJECT_ROOT"
    # 策略2: 检查脚本目录是否在项目内
    elif [ -d "$SCRIPT_DIR/backend" ] && [ -d "$SCRIPT_DIR/frontend" ]; then
        PROJECT_ROOT="$SCRIPT_DIR"
        log_info "检测到脚本在项目目录内: $PROJECT_ROOT"
    # 策略3: 检查脚本目录的父目录是否包含项目
    elif [ -d "$(dirname "$SCRIPT_DIR")/backend" ] && [ -d "$(dirname "$SCRIPT_DIR")/frontend" ]; then
        PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
        log_info "检测到项目在脚本父目录: $PROJECT_ROOT"
    else
        log_error "无法检测到项目目录，请确保在正确的目录中运行脚本"
        exit 1
    fi

    cd "$PROJECT_ROOT"
    log_success "项目路径: $PROJECT_ROOT"
}

# VPS环境选择数据库
select_database_vps() {
    log_info "选择数据库类型..."

    if [ "$INSTALL_MODE" = "auto" ]; then
        DB_TYPE="sqlite"
        log_info "自动选择: SQLite"
        return
    fi

    echo "请选择数据库类型:"
    echo "1) SQLite (推荐 - 无需额外配置)"
    echo "2) MySQL/MariaDB"
    echo "3) PostgreSQL"

    read -p "请输入选择 (1-3): " db_choice
    case $db_choice in
        1)
            DB_TYPE="sqlite"
            ;;
        2)
            DB_TYPE="mysql"
            ;;
        3)
            DB_TYPE="postgresql"
            ;;
        *)
            log_warning "无效选择，使用SQLite"
            DB_TYPE="sqlite"
            ;;
    esac
}

# VPS环境安装数据库
install_database_vps() {
    log_info "安装和配置数据库..."

    case $DB_TYPE in
        "sqlite")
            install_sqlite_vps
            ;;
        "mysql")
            install_mysql_vps
            ;;
        "postgresql")
            install_postgresql_vps
            ;;
    esac
}

# 安装SQLite (VPS)
install_sqlite_vps() {
    log_info "配置SQLite..."

    case $OS in
        "ubuntu"|"debian")
            apt install -y sqlite3
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                dnf install -y sqlite
            else
                yum install -y sqlite
            fi
            ;;
    esac

    log_success "SQLite配置完成"
}

# 安装MySQL (VPS)
install_mysql_vps() {
    log_info "安装MySQL..."

    case $OS in
        "ubuntu"|"debian")
            apt install -y mysql-server
            systemctl start mysql
            systemctl enable mysql

            # 安全配置
            mysql_secure_installation << EOF

y
y
y
y
y
EOF
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                dnf install -y mysql-server
            else
                yum install -y mysql-server
            fi
            systemctl start mysqld
            systemctl enable mysqld
            ;;
    esac

    # 创建数据库和用户
    DB_HOST="localhost"
    DB_PORT="3306"
    DB_NAME="xboard"
    DB_USER="xboard"
    DB_PASSWORD=$(openssl rand -base64 12)

    mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

    log_success "MySQL安装和配置完成"
}

# 安装PostgreSQL (VPS)
install_postgresql_vps() {
    log_info "安装PostgreSQL..."

    case $OS in
        "ubuntu"|"debian")
            apt install -y postgresql postgresql-contrib
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                dnf install -y postgresql-server postgresql-contrib
                postgresql-setup initdb
            else
                yum install -y postgresql-server postgresql-contrib
                service postgresql initdb
            fi
            ;;
    esac

    systemctl start postgresql
    systemctl enable postgresql

    # 创建数据库和用户
    DB_HOST="localhost"
    DB_PORT="5432"
    DB_NAME="xboard"
    DB_USER="xboard"
    DB_PASSWORD=$(openssl rand -base64 12)

    sudo -u postgres psql << EOF
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

    log_success "PostgreSQL安装和配置完成"
}

# VPS环境安装Nginx
install_nginx_vps() {
    log_info "安装和配置Nginx..."

    case $OS in
        "ubuntu"|"debian")
            apt install -y nginx
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                dnf install -y nginx
            else
                yum install -y nginx
            fi
            ;;
    esac

    # 备份默认配置
    cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

    # 配置Nginx
    cat > /etc/nginx/sites-available/xboard << 'EOF'
server {
    listen 80;
    server_name _;

    # 静态文件缓存
    location /static/ {
        alias /var/www/xboard/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 前端应用
    location / {
        root /var/www/xboard/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # 日志
    access_log /var/log/nginx/xboard_access.log;
    error_log /var/log/nginx/xboard_error.log;
}
EOF

    # 启用站点
    ln -sf /etc/nginx/sites-available/xboard /etc/nginx/sites-enabled/

    # 删除默认站点
    rm -f /etc/nginx/sites-enabled/default

    # 创建日志目录
    mkdir -p /var/log/nginx

    # 启动Nginx
    systemctl enable nginx
    systemctl start nginx

    log_success "Nginx安装和配置完成"
}

# VPS环境设置Python环境
setup_python_env_vps() {
    log_info "设置Python环境..."

    # 创建虚拟环境
    python3 -m venv venv

    # 激活虚拟环境
    source venv/bin/activate

    # 升级pip
    pip install --upgrade pip

    # 安装Python依赖
    pip install -r backend/requirements.txt

    log_success "Python环境设置完成"
}

# VPS环境构建前端
build_frontend_vps() {
    log_info "构建前端..."

    cd frontend
    npm install
    npm run build
    cd ..

    log_success "前端构建完成"
}

# VPS环境配置环境变量
configure_env_vps() {
    log_info "配置环境变量..."

    # 生成随机密钥
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)

    # 创建.env文件
    cat > .env << EOF
# ================================
# XBoard Modern 环境变量配置
# ================================

# 数据库配置
EOF

    # 根据数据库类型配置
    case $DB_TYPE in
        "sqlite")
            cat >> .env << EOF
DATABASE_URL=sqlite:///./xboard.db
EOF
            ;;
        "mysql")
            cat >> .env << EOF
DATABASE_URL=mysql+pymysql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME
EOF
            ;;
        "postgresql")
            cat >> .env << EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME
EOF
            ;;
    esac

    cat >> .env << EOF

# 应用配置
DEBUG=False
HOST=127.0.0.1
PORT=8000
WORKERS=4

# 安全配置
SECRET_KEY=$SECRET_KEY
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_SECRET_KEY=$JWT_SECRET

# 邮件配置
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USERNAME=your-email@qq.com
SMTP_PASSWORD=your-email-password
SMTP_ENCRYPTION=tls
SMTP_FROM_EMAIL=your-email@qq.com
SMTP_FROM_NAME=XBoard System

# 文件上传配置
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760

# 订阅配置
SUBSCRIPTION_URL_PREFIX=https://$DOMAIN/sub
DEVICE_LIMIT_DEFAULT=3

# 管理员配置
ADMIN_EMAIL=$ADMIN_EMAIL
ADMIN_PASSWORD=$ADMIN_PASSWORD
EOF

    log_success "环境变量配置完成"
}

# VPS环境初始化数据库
init_database_vps() {
    log_info "初始化数据库..."

    source venv/bin/activate
    cd backend

    python3 -c "
from app.core.database import init_database
import logging
logging.basicConfig(level=logging.INFO)

if init_database():
    print('数据库初始化成功')
else:
    print('数据库初始化失败')
"

    cd ..
    log_success "数据库初始化完成"
}

# VPS环境创建systemd服务
create_systemd_service_vps() {
    log_info "创建systemd服务..."

    cat > /etc/systemd/system/xboard.service << EOF
[Unit]
Description=XBoard Modern Backend Service
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_ROOT
Environment=PATH=$PROJECT_ROOT/venv/bin
ExecStart=$PROJECT_ROOT/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable xboard
    systemctl start xboard

    log_success "systemd服务创建完成"
}

# VPS环境配置防火墙
configure_firewall_vps() {
    log_info "配置防火墙..."

    case $OS in
        "ubuntu"|"debian")
            ufw --force enable
            ufw allow 80
            ufw allow 443
            ufw allow ssh
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            systemctl start firewalld
            systemctl enable firewalld
            firewall-cmd --permanent --add-service=http
            firewall-cmd --permanent --add-service=https
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --reload
            ;;
    esac

    log_success "防火墙配置完成"
}

# VPS环境安装SSL证书
install_ssl_vps() {
    if [ -z "$DOMAIN" ]; then
        log_warning "未配置域名，跳过SSL证书安装"
        return
    fi

    log_info "安装SSL证书..."

    # 安装certbot
    case $OS in
        "ubuntu"|"debian")
            apt install -y certbot python3-certbot-nginx
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                dnf install -y certbot python3-certbot-nginx
            else
                yum install -y certbot python3-certbot-nginx
            fi
            ;;
    esac

    # 获取SSL证书
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $ADMIN_EMAIL

    log_success "SSL证书安装完成"
}

# VPS环境创建备份脚本
create_backup_script_vps() {
    log_info "创建备份脚本..."

    cat > backup.sh << 'EOF'
#!/bin/bash

# XBoard Modern 备份脚本

BACKUP_DIR="/var/backups/xboard"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="xboard_backup_$DATE"

mkdir -p $BACKUP_DIR

echo "开始备份 XBoard Modern..."

# 备份数据库
if [ -f "xboard.db" ]; then
    cp xboard.db $BACKUP_DIR/xboard_$DATE.db
    echo "数据库备份完成"
fi

# 备份配置文件
cp .env $BACKUP_DIR/.env_$DATE

# 备份上传文件
if [ -d "uploads" ]; then
    tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz uploads/
    echo "上传文件备份完成"
fi

echo "备份完成: $BACKUP_DIR/$BACKUP_NAME"
EOF

    chmod +x backup.sh

    # 添加到crontab (每周日凌晨2点备份)
    (crontab -l ; echo "0 2 * * 0 $PROJECT_ROOT/backup.sh") | crontab -

    log_success "备份脚本创建完成"
}

# 显示安装完成信息
show_completion_info() {
    echo ""
    echo "=========================================="
    echo "🎉 $PROJECT_NAME 安装完成！"
    echo "=========================================="
    echo ""
    echo "📊 安装信息:"
    echo "  项目路径: $PROJECT_ROOT"
    echo "  环境类型: $ENVIRONMENT_TYPE"

    if [ "$ENVIRONMENT_TYPE" = "vps" ]; then
        echo "  数据库类型: $DB_TYPE"
        if [ "$DB_TYPE" != "sqlite" ]; then
            echo "  数据库: $DB_NAME"
            echo "  用户: $DB_USER"
        fi
        echo "  域名: ${DOMAIN:-未配置}"
    fi

    echo ""
    echo "🌐 访问地址:"

    if [ "$ENVIRONMENT_TYPE" = "local" ]; then
        echo "  后端API: http://127.0.0.1:8000"
        echo "  API文档: http://127.0.0.1:8000/docs"
        echo "  前端开发: http://127.0.0.1:5173 (如果安装了前端)"
        echo "  前端构建: http://127.0.0.1:8000"
        echo ""
        echo "🚀 启动命令:"
        echo "  开发模式: ./dev_start.sh"
        echo "  生产模式: ./start.sh"
        echo "  停止服务: ./stop.sh"
    else
        echo "  网站地址: http://${DOMAIN:-your-server-ip}"
        if [ -n "$DOMAIN" ]; then
            echo "  HTTPS地址: https://$DOMAIN"
        fi
        echo "  API文档: http://${DOMAIN:-your-server-ip}/docs"
    fi

    echo ""
    echo "👤 管理员账户:"
    if [ "$ENVIRONMENT_TYPE" = "local" ]; then
        echo "  邮箱: admin@xboard.local"
        echo "  密码: admin123"
    else
        echo "  邮箱: $ADMIN_EMAIL"
        echo "  密码: $ADMIN_PASSWORD"
    fi

    echo ""
    echo "📁 重要文件位置:"
    if [ "$ENVIRONMENT_TYPE" = "vps" ]; then
        echo "  配置文件: $PROJECT_ROOT/.env"
        echo "  日志文件: /var/log/nginx/"
        echo "  备份文件: /var/backups/xboard/"
        echo "  systemd服务: /etc/systemd/system/xboard.service"
        echo ""
        echo "🛠️ 管理命令:"
        echo "  启动服务: sudo systemctl start xboard"
        echo "  停止服务: sudo systemctl stop xboard"
        echo "  重启服务: sudo systemctl restart xboard"
        echo "  查看日志: sudo journalctl -u xboard -f"
        echo "  备份数据: ./backup.sh"
    fi

    echo ""
    log_success "🎊 安装成功完成！"
}

# 显示使用帮助
show_help() {
    echo "$PROJECT_NAME 智能安装脚本"
    echo ""
    echo "自动检测运行环境并选择最佳配置："
    echo "  本地开发环境：使用SQLite，简化配置"
    echo "  VPS生产环境：完整生产配置，支持多种数据库"
    echo ""
    echo "用法:"
    echo "  $0                    # 自动检测环境并安装"
    echo "  $0 --local           # 强制本地开发模式"
    echo "  $0 --vps             # 强制VPS生产模式"
    echo "  $0 --help            # 显示帮助信息"
    echo ""
    echo "本地开发模式特性:"
    echo "  - 使用SQLite数据库"
    echo "  - 不需要root权限"
    echo "  - 简化配置和依赖"
    echo "  - 开发友好的启动脚本"
    echo ""
    echo "VPS生产模式特性:"
    echo "  - 支持SQLite/MySQL/PostgreSQL"
    echo "  - 完整的系统服务配置"
    echo "  - Nginx反向代理"
    echo "  - 防火墙配置"
    echo "  - SSL证书支持"
    echo ""
}

# 主安装流程
main() {
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --local)
                ENVIRONMENT_TYPE="local"
                shift
                ;;
            --vps)
                ENVIRONMENT_TYPE="vps"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    echo "=========================================="
    echo "🚀 $PROJECT_NAME 智能安装脚本"
    echo "=========================================="
    echo ""

    # 检测环境类型
    if [ -z "$ENVIRONMENT_TYPE" ]; then
        detect_environment
    else
        log_info "手动指定环境类型: $ENVIRONMENT_TYPE"
    fi

    # 检查是否为VPS环境且需要root权限
    if [ "$ENVIRONMENT_TYPE" = "vps" ] && [ "$IS_ROOT" != true ]; then
        log_error "VPS生产环境安装需要root权限，请使用: sudo $0"
        exit 1
    fi

    # 根据环境类型执行相应的安装流程
    if [ "$ENVIRONMENT_TYPE" = "local" ]; then
        install_local
    else
        # VPS环境的配置
        if [ "$ENVIRONMENT_TYPE" = "vps" ]; then
            # 如果没有手动指定域名，尝试自动检测
            if [ -z "$DOMAIN" ]; then
                DOMAIN=$(curl -s ifconfig.me 2>/dev/null || echo "")
                if [ -n "$DOMAIN" ]; then
                    log_info "检测到公网IP: $DOMAIN"
                fi
            fi

            # 设置默认管理员信息
            if [ -z "$ADMIN_EMAIL" ]; then
                ADMIN_EMAIL="admin@$DOMAIN"
            fi

            if [ -z "$ADMIN_PASSWORD" ]; then
                ADMIN_PASSWORD=$(openssl rand -base64 12)
            fi
        fi

        install_vps
    fi

    # 显示完成信息
    show_completion_info
}

# 运行主函数
main "$@"
