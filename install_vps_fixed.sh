#!/bin/bash

# ================================
# XBoard Modern VPS 智能安装脚本 (修复版)
# 解决环境检测、前端构建和依赖安装问题
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
PYTHON_CMD=""
PYTHON_VERSION=""
DOMAIN=""
DB_TYPE="sqlite"
DB_HOST="localhost"
DB_PORT="3306"
DB_NAME="xboard"
DB_USER="xboard"
DB_PASSWORD=""
ADMIN_EMAIL="admin@localhost"
ADMIN_PASSWORD=""
INSTALL_MODE="auto"

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root用户运行此脚本"
        exit 1
    fi
}

# 检测VPS提供商和系统信息
detect_vps_info() {
    log_info "检测VPS信息..."

    # 检测操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        OS="rhel"
        OS_VERSION=$(cat /etc/redhat-release | grep -oE '[0-9]+\.[0-9]+' | head -1)
    else
        log_error "无法检测操作系统类型"
        exit 1
    fi

    # 检测VPS提供商
    PROVIDER="unknown"
    if [ -f /sys/devices/virtual/dmi/id/product_name ]; then
        PRODUCT_NAME=$(cat /sys/devices/virtual/dmi/id/product_name)
        case $PRODUCT_NAME in
            *"DigitalOcean"*) PROVIDER="digitalocean" ;;
            *"Linode"*) PROVIDER="linode" ;;
            *"Vultr"*) PROVIDER="vultr" ;;
            *"AWS"*) PROVIDER="aws" ;;
            *"Google"*) PROVIDER="gcp" ;;
            *"Alibaba"*) PROVIDER="alibaba" ;;
            *"Tencent"*) PROVIDER="tencent" ;;
        esac
    fi

    # 检测系统架构
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        ARCH="amd64"
    elif [ "$ARCH" = "aarch64" ]; then
        ARCH="arm64"
    fi

    log_success "检测结果: $OS $OS_VERSION, 架构: $ARCH, 提供商: $PROVIDER"
}

# 智能检测项目路径
detect_project_path() {
    log_info "智能检测项目路径..."

    # 策略1: 检查当前目录
    if [ -d "backend" ] && [ -d "frontend" ]; then
        PROJECT_ROOT="$(pwd)"
        log_success "检测到当前目录为项目根目录: $PROJECT_ROOT"
        return 0
    fi

    # 策略2: 检查脚本目录
    if [ -d "$SCRIPT_DIR/backend" ] && [ -d "$SCRIPT_DIR/frontend" ]; then
        PROJECT_ROOT="$SCRIPT_DIR"
        log_success "检测到脚本在项目目录内: $PROJECT_ROOT"
        return 0
    fi

    # 策略3: 检查脚本父目录
    if [ -d "$(dirname "$SCRIPT_DIR")/backend" ] && [ -d "$(dirname "$SCRIPT_DIR")/frontend" ]; then
        PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
        log_success "检测到项目在脚本父目录: $PROJECT_ROOT"
        return 0
    fi

    # 策略4: 递归向上查找
    local current_dir="$(pwd)"
    while [ "$current_dir" != "/" ]; do
        if [ -d "$current_dir/backend" ] && [ -d "$current_dir/frontend" ]; then
            PROJECT_ROOT="$current_dir"
            log_success "递归查找到项目目录: $PROJECT_ROOT"
            return 0
        fi
        current_dir="$(dirname "$current_dir")"
    done

    # 策略5: 检查常见路径
    local common_paths=("/www/wwwroot" "/var/www" "/home" "/root")
    for path in "${common_paths[@]}"; do
        if [ -d "$path" ]; then
            for item in "$path"/*; do
                if [ -d "$item" ] && [ -d "$item/backend" ] && [ -d "$item/frontend" ]; then
                    PROJECT_ROOT="$item"
                    log_success "在常见路径找到项目: $PROJECT_ROOT"
                    return 0
                fi
            done
        fi
    done

    log_error "无法检测到项目目录"
    log_info "请确保项目包含 backend/ 和 frontend/ 目录"
    log_info "当前目录: $(pwd)"
    log_info "脚本目录: $SCRIPT_DIR"
    exit 1
}

# 更新系统并安装基础依赖
update_system() {
    log_info "更新系统并安装基础依赖..."

    case $OS in
        "ubuntu"|"debian")
            apt update && apt upgrade -y
            apt install -y curl wget git unzip software-properties-common ufw build-essential
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                dnf update -y
                dnf install -y curl wget git unzip firewalld gcc gcc-c++ make
            else
                yum update -y
                yum install -y curl wget git unzip firewalld gcc gcc-c++ make
            fi
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac

    log_success "系统更新完成"
}

# 智能检测和安装Python
install_python() {
    log_info "智能检测Python环境..."

    # 检测已安装的Python版本
    PYTHON_VERSIONS=()
    PYTHON_CMD=""
    
    # 检查python3命令
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        PYTHON_VERSIONS+=("$PYTHON_VERSION")
        log_info "检测到已安装的Python3: $PYTHON_VERSION"
    fi
    
    # 检查python命令
    if command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        if [[ ! " ${PYTHON_VERSIONS[@]} " =~ " ${PYTHON_VERSION} " ]]; then
            PYTHON_VERSIONS+=("$PYTHON_VERSION")
        fi
        log_info "检测到已安装的Python: $PYTHON_VERSION"
    fi
    
    # 检查特定版本
    for version in "3.11" "3.10" "3.9" "3.8" "3.7" "3.6"; do
        if command -v "python$version" &> /dev/null; then
            PYTHON_VERSION=$(python$version --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
            if [[ ! " ${PYTHON_VERSIONS[@]} " =~ " ${PYTHON_VERSION} " ]]; then
                PYTHON_VERSIONS+=("$PYTHON_VERSION")
            fi
            log_info "检测到已安装的Python$version: $PYTHON_VERSION"
        fi
    done
    
    # 选择最佳Python版本
    if [ ${#PYTHON_VERSIONS[@]} -gt 0 ]; then
        # 按版本号排序，选择最高版本
        IFS=$'\n' sorted_versions=($(sort -V -r <<<"${PYTHON_VERSIONS[*]}"))
        unset IFS
        
        BEST_VERSION="${sorted_versions[0]}"
        log_success "选择最佳Python版本: $BEST_VERSION"
        
        # 设置主要Python命令
        if command -v "python$BEST_VERSION" &> /dev/null; then
            PYTHON_CMD="python$BEST_VERSION"
            ln -sf "/usr/bin/python$BEST_VERSION" /usr/bin/python3 2>/dev/null || true
        elif command -v python3 &> /dev/null; then
            PYTHON_CMD="python3"
        elif command -v python &> /dev/null; then
            PYTHON_CMD="python"
        fi
        
        log_success "使用Python命令: $PYTHON_CMD"
        return 0
    fi
    
    # 如果没有安装Python，则安装合适的版本
    log_info "未检测到Python，开始安装..."
    
    case $OS in
        "ubuntu")
                    if [ "$OS_VERSION" = "18.04" ]; then
            # Ubuntu 18.04 默认有Python 3.6，使用现有版本
            log_info "Ubuntu 18.04 使用默认Python 3.6"
            apt install -y python3-venv python3-dev python3-pip
            PYTHON_CMD="python3"
        elif [ "$OS_VERSION" = "20.04" ]; then
                # Ubuntu 20.04 默认有Python 3.8
                apt install -y python3.8-venv python3.8-dev python3-pip
                PYTHON_CMD="python3.8"
            elif [ "$OS_VERSION" = "22.04" ]; then
                # Ubuntu 22.04 默认有Python 3.10
                apt install -y python3.10-venv python3.10-dev python3-pip
                PYTHON_CMD="python3.10"
            else
                # 其他版本安装Python 3.8
                add-apt-repository ppa:deadsnakes/ppa -y
                apt update
                apt install -y python3.8 python3.8-venv python3.8-dev python3-pip
                PYTHON_CMD="python3.8"
                ln -sf /usr/bin/python3.8 /usr/bin/python3
            fi
            ;;
        "debian")
            # Debian 通常有Python 3
            apt install -y python3-venv python3-dev python3-pip
            PYTHON_CMD="python3"
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                # 尝试安装Python 3.8
                dnf install -y python38 python38-devel python38-pip || \
                dnf install -y python3 python3-devel python3-pip
                PYTHON_CMD="python3.8" || PYTHON_CMD="python3"
            else
                # 尝试安装Python 3.6
                yum install -y python36 python36-devel python36-pip || \
                yum install -y python3 python3-devel python3-pip
                PYTHON_CMD="python3.6" || PYTHON_CMD="python3"
            fi
            ;;
    esac
    
    # 验证安装
    if [ -n "$PYTHON_CMD" ] && command -v "$PYTHON_CMD" &> /dev/null; then
        PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        log_success "Python安装完成: $PYTHON_VERSION"
        
        # 创建软链接
        if [ "$PYTHON_CMD" != "python3" ]; then
            ln -sf "/usr/bin/$PYTHON_CMD" /usr/bin/python3 2>/dev/null || true
        fi
    else
        log_error "Python安装失败"
        exit 1
    fi
}

# 智能检测和安装Node.js
install_nodejs() {
    log_info "智能检测Node.js环境..."

    # 检测已安装的Node.js版本
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version 2>&1 | grep -oE 'v[0-9]+' | head -1)
        NODE_MAJOR_VERSION=$(echo $NODE_VERSION | grep -oE '[0-9]+' | head -1)
        
        log_info "检测到已安装的Node.js: $NODE_VERSION"
        
        # 检查版本是否满足要求
        if [ "$NODE_MAJOR_VERSION" -ge 14 ]; then
            log_success "Node.js版本满足要求: $NODE_VERSION"
            return 0
        elif [ "$NODE_MAJOR_VERSION" -ge 8 ]; then
            log_warning "Node.js版本较低: $NODE_VERSION，但可以继续使用"
            return 0
        else
            log_warning "Node.js版本过低: $NODE_VERSION，需要升级"
        fi
    else
        log_info "未检测到Node.js，开始安装..."
    fi
    
    # 安装或升级Node.js
    case $OS in
        "ubuntu"|"debian")
            # 尝试安装Node.js 16 (LTS版本，兼容性更好)
            curl -fsSL https://deb.nodesource.com/setup_16.x | bash -
            apt install -y nodejs
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            curl -fsSL https://rpm.nodesource.com/setup_16.x | bash -
            if command -v dnf &> /dev/null; then
                dnf install -y nodejs
            else
                yum install -y nodejs
            fi
            ;;
    esac

    # 验证安装
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version 2>&1 | grep -oE 'v[0-9]+' | head -1)
        log_success "Node.js安装完成: $NODE_VERSION"
    else
        log_error "Node.js安装失败"
        exit 1
    fi
}

# 安装和配置Nginx
install_nginx() {
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
    root /var/www/xboard/frontend/dist;
    index index.html;

    # 前端静态文件
    location / {
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

    # 上传文件
    location /uploads/ {
        alias /var/www/xboard/uploads/;
    }
}
EOF

    # 启用站点
    ln -sf /etc/nginx/sites-available/xboard /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    # 创建网站目录
    mkdir -p /var/www/xboard
    chown -R www-data:www-data /var/www/xboard

    log_success "Nginx安装完成"
}

# 设置Python环境
setup_python_environment() {
    log_info "设置Python环境..."

    cd "$PROJECT_ROOT"

    # 使用检测到的Python命令
    if [ -z "$PYTHON_CMD" ]; then
        log_error "Python命令未设置，请先运行install_python"
        exit 1
    fi

    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        log_info "使用 $PYTHON_CMD 创建Python虚拟环境..."
        $PYTHON_CMD -m venv venv
    fi

    # 激活虚拟环境
    source venv/bin/activate

    # 升级pip
    pip install --upgrade pip

    # 智能选择兼容的requirements文件
    if [ -n "$PYTHON_VERSION" ]; then
        log_info "检测到Python版本: $PYTHON_VERSION"
        
        # 根据Python版本选择兼容的requirements文件
        if [ "$PYTHON_VERSION" = "3.6" ]; then
            if [ -f "backend/requirements_python36.txt" ]; then
                log_info "使用Python 3.6兼容的requirements文件"
                pip install -r backend/requirements_python36.txt
            else
                log_warning "未找到Python 3.6兼容文件，使用基础依赖..."
                pip install "fastapi<0.84.0" "uvicorn[standard]<0.19.0" "sqlalchemy<1.5.0" "pydantic<2.0.0" python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv email-validator
            fi
        elif [ "$PYTHON_VERSION" = "3.7" ]; then
            if [ -f "backend/requirements_python37.txt" ]; then
                log_info "使用Python 3.7兼容的requirements文件"
                pip install -r backend/requirements_python37.txt
            else
                log_warning "未找到Python 3.7兼容文件，使用基础依赖..."
                pip install "fastapi<0.95.0" "uvicorn[standard]<0.21.0" "sqlalchemy<2.0.0" "pydantic<2.0.0" python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv email-validator
            fi
        elif [ -f "backend/requirements_vps.txt" ]; then
            log_info "使用VPS专用requirements文件"
            pip install -r backend/requirements_vps.txt
        elif [ -f "backend/requirements.txt" ]; then
            log_info "使用标准requirements文件"
            pip install -r backend/requirements.txt
        else
            log_warning "未找到requirements文件，安装基础依赖..."
            pip install fastapi uvicorn sqlalchemy pymysql python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv email-validator
        fi
    else
        log_warning "无法检测Python版本，使用默认requirements..."
        if [ -f "backend/requirements_vps.txt" ]; then
            pip install -r backend/requirements_vps.txt
        elif [ -f "backend/requirements.txt" ]; then
            pip install -r backend/requirements.txt
        else
            pip install fastapi uvicorn sqlalchemy pymysql python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv email-validator
        fi
    fi

    log_success "Python环境设置完成"
}

# 构建前端
build_frontend() {
    log_info "构建前端..."

    cd "$PROJECT_ROOT/frontend"

    # 检查package.json
    if [ ! -f "package.json" ]; then
        log_error "前端目录中未找到package.json文件"
        return 1
    fi

    # 安装依赖
    log_info "安装前端依赖..."
    npm install --production=false

    # 检查构建脚本
    if grep -q '"build"' package.json; then
        log_info "执行前端构建..."
        npm run build
        log_success "前端构建完成"
    else
        log_warning "package.json中未找到build脚本，跳过构建"
    fi

    cd "$PROJECT_ROOT"
}

# 配置环境变量
configure_environment() {
    log_info "配置环境变量..."

    cd "$PROJECT_ROOT"

    # 生成随机密钥
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)

    # 创建.env文件
    cat > .env << EOF
# ================================
# XBoard Modern 环境变量配置
# ================================

# 数据库配置
DATABASE_URL=sqlite:///./xboard.db

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

# Redis配置 (可选)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# 文件上传配置
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760

# 订阅配置
SUBSCRIPTION_URL_PREFIX=https://localhost/sub
DEVICE_LIMIT_DEFAULT=3

# 管理员配置
ADMIN_EMAIL=$ADMIN_EMAIL
ADMIN_PASSWORD=$ADMIN_PASSWORD
EOF

    log_success "环境变量配置完成"
}

# 初始化数据库
initialize_database() {
    log_info "初始化数据库..."

    cd "$PROJECT_ROOT"

    # 激活虚拟环境
    source venv/bin/activate

    # 运行数据库初始化
    if [ -f "backend/main.py" ]; then
        log_info "运行数据库初始化..."
        cd backend
        python main.py --init-db
        cd ..
    fi

    log_success "数据库初始化完成"
}

# 创建systemd服务
create_systemd_service() {
    log_info "创建systemd服务..."

    cat > /etc/systemd/system/xboard.service << EOF
[Unit]
Description=XBoard Modern Backend
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_ROOT/backend
Environment=PATH=$PROJECT_ROOT/venv/bin
ExecStart=$PROJECT_ROOT/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载systemd
    systemctl daemon-reload
    systemctl enable xboard.service

    log_success "systemd服务创建完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."

    case $OS in
        "ubuntu"|"debian")
            ufw allow 22/tcp
            ufw allow 80/tcp
            ufw allow 443/tcp
            ufw --force enable
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v firewall-cmd &> /dev/null; then
                firewall-cmd --permanent --add-service=ssh
                firewall-cmd --permanent --add-service=http
                firewall-cmd --permanent --add-service=https
                firewall-cmd --reload
            fi
            ;;
    esac

    log_success "防火墙配置完成"
}

# 复制项目文件到网站目录
copy_project_files() {
    log_info "复制项目文件到网站目录..."

    # 复制前端构建文件
    if [ -d "$PROJECT_ROOT/frontend/dist" ]; then
        cp -r "$PROJECT_ROOT/frontend/dist"/* /var/www/xboard/frontend/
    fi

    # 复制后端文件
    cp -r "$PROJECT_ROOT/backend" /var/www/xboard/
    cp -r "$PROJECT_ROOT/uploads" /var/www/xboard/ 2>/dev/null || mkdir -p /var/www/xboard/uploads

    # 复制环境文件
    cp "$PROJECT_ROOT/.env" /var/www/xboard/

    # 设置权限
    chown -R www-data:www-data /var/www/xboard
    chmod -R 755 /var/www/xboard

    log_success "项目文件复制完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."

    # 启动后端服务
    systemctl start xboard.service
    systemctl status xboard.service

    # 重启Nginx
    systemctl restart nginx
    systemctl status nginx

    log_success "服务启动完成"
}

# 显示完成信息
show_completion_info() {
    echo ""
    echo "=========================================="
    echo "🎉 XBoard Modern 安装完成！"
    echo "=========================================="
    echo ""
    echo "📱 访问地址:"
    echo "   前端: http://$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip")"
    echo "   API文档: http://$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip")/docs"
    echo ""
    echo "🔧 管理命令:"
    echo "   查看服务状态: systemctl status xboard"
    echo "   重启服务: systemctl restart xboard"
    echo "   查看日志: journalctl -u xboard -f"
    echo ""
    echo "📁 项目位置: $PROJECT_ROOT"
    echo "🌐 网站目录: /var/www/xboard"
    echo ""
    echo "⚠️  重要提醒:"
    echo "   1. 请修改 .env 文件中的邮件配置"
    echo "   2. 建议配置SSL证书"
    echo "   3. 定期备份数据库"
    echo ""
}

# 主安装流程
main() {
    echo "=========================================="
    echo "🚀 XBoard Modern VPS 智能安装脚本 (修复版)"
    echo "=========================================="
    echo ""

    # 检查是否为root
    check_root

    # 检测VPS信息
    detect_vps_info

    # 智能检测项目路径
    detect_project_path

    # 更新系统
    update_system

    # 安装基础软件
    install_python
    install_nodejs

    # 设置Python环境
    setup_python_environment

    # 构建前端
    build_frontend

    # 配置环境变量
    configure_environment

    # 初始化数据库
    initialize_database

    # 安装Nginx
    install_nginx

    # 创建systemd服务
    create_systemd_service

    # 配置防火墙
    configure_firewall

    # 复制项目文件
    copy_project_files

    # 启动服务
    start_services

    # 显示完成信息
    show_completion_info
}

# 运行主函数
main "$@"
