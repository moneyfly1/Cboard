#!/bin/bash

# ================================
# XBoard Modern VPS 智能安装脚本
# 专为VPS环境优化，支持全自动部署
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

# 更新系统并安装基础依赖
update_system() {
    log_info "更新系统并安装基础依赖..."

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

# 安装Python 3.9+
install_python() {
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

# 安装Node.js 18+
install_nodejs() {
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

# 安装和配置数据库
install_database() {
    log_info "选择数据库类型..."

    echo "请选择数据库类型:"
    echo "1) SQLite (推荐 - 无需额外配置)"
    echo "2) MySQL/MariaDB"
    echo "3) PostgreSQL"

    if [ "$INSTALL_MODE" = "auto" ]; then
        DB_TYPE="sqlite"
        log_info "自动选择: SQLite"
    else
        read -p "请输入选择 (1-3): " db_choice
        case $db_choice in
            1)
                DB_TYPE="sqlite"
                install_sqlite
                ;;
            2)
                DB_TYPE="mysql"
                install_mysql
                ;;
            3)
                DB_TYPE="postgresql"
                install_postgresql
                ;;
            *)
                log_error "无效选择，使用SQLite"
                DB_TYPE="sqlite"
                install_sqlite
                ;;
        esac
    fi
}

# 安装SQLite
install_sqlite() {
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

# 安装MySQL
install_mysql() {
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

            # 设置root密码
            mysql -u root << EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
FLUSH PRIVILEGES;
EOF
            ;;
    esac

    # 创建数据库
    if [ "$INSTALL_MODE" = "auto" ]; then
        DB_HOST="localhost"
        DB_PORT="3306"
        DB_NAME="xboard"
        DB_USER="xboard"
        DB_PASSWORD=$(openssl rand -base64 12)

        mysql -u root -p$DB_PASSWORD << EOF
CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF
    fi

    log_success "MySQL安装和配置完成"
}

# 安装PostgreSQL
install_postgresql() {
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
    if [ "$INSTALL_MODE" = "auto" ]; then
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
    fi

    log_success "PostgreSQL安装和配置完成"
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

# 创建虚拟环境并安装Python依赖
setup_python_environment() {
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

# 构建前端
build_frontend() {
    log_info "构建前端..."

    cd frontend
    npm install
    npm run build
    cd ..

    log_success "前端构建完成"
}

# 配置环境变量
configure_environment() {
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

# Redis配置 (可选)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

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

# 初始化数据库
initialize_database() {
    log_info "初始化数据库..."

    source venv/bin/activate
    cd backend

    # 运行数据库初始化脚本
    python3 -c "
from app.core.database import init_database
from app.models import Base
from sqlalchemy import create_engine

if init_database():
    print('数据库初始化成功')
else:
    print('数据库初始化失败')
    exit(1)
"

    cd ..
    log_success "数据库初始化完成"
}

# 创建systemd服务
create_systemd_service() {
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

# 配置防火墙
configure_firewall() {
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

# 安装SSL证书 (Let's Encrypt)
install_ssl_certificate() {
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

# 创建备份脚本
create_backup_script() {
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
    log_success "=========================================="
    log_success "🎉 XBoard Modern 安装完成！"
    log_success "=========================================="
    echo ""
    echo "📊 安装信息:"
    echo "  项目路径: $PROJECT_ROOT"
    echo "  数据库类型: $DB_TYPE"
    if [ "$DB_TYPE" != "sqlite" ]; then
        echo "  数据库: $DB_NAME"
        echo "  用户: $DB_USER"
        echo "  密码: $DB_PASSWORD"
    fi
    echo "  域名: ${DOMAIN:-未配置}"
    echo ""
    echo "🌐 访问地址:"
    echo "  前端: http://${DOMAIN:-your-server-ip}"
    if [ -n "$DOMAIN" ]; then
        echo "  HTTPS: https://$DOMAIN"
    fi
    echo "  API文档: http://${DOMAIN:-your-server-ip}/docs"
    echo ""
    echo "👤 管理员账户:"
    echo "  邮箱: $ADMIN_EMAIL"
    echo "  密码: $ADMIN_PASSWORD"
    echo ""
    echo "🛠️ 管理命令:"
    echo "  启动服务: sudo systemctl start xboard"
    echo "  停止服务: sudo systemctl stop xboard"
    echo "  重启服务: sudo systemctl restart xboard"
    echo "  查看日志: sudo journalctl -u xboard -f"
    echo "  备份数据: ./backup.sh"
    echo ""
    echo "📁 重要文件位置:"
    echo "  配置文件: $PROJECT_ROOT/.env"
    echo "  日志文件: /var/log/nginx/"
    echo "  备份文件: /var/backups/xboard/"
    echo ""
    log_success "🎊 安装成功完成！"
}

# 自动模式配置
auto_configure() {
    log_info "开始自动配置模式..."

    # 自动生成配置
    if [ -z "$DOMAIN" ]; then
        DOMAIN=$(curl -s ifconfig.me)
        log_warning "自动检测域名/IP: $DOMAIN"
    fi

    if [ -z "$ADMIN_EMAIL" ]; then
        ADMIN_EMAIL="admin@$DOMAIN"
        log_warning "自动设置管理员邮箱: $ADMIN_EMAIL"
    fi

    if [ -z "$ADMIN_PASSWORD" ]; then
        ADMIN_PASSWORD=$(openssl rand -base64 12)
        log_warning "自动生成管理员密码: $ADMIN_PASSWORD"
    fi

    DB_TYPE="sqlite"
    log_info "自动选择数据库: SQLite"
}

# 手动模式配置
manual_configure() {
    log_info "开始手动配置模式..."

    # 获取域名
    read -p "请输入您的域名 (留空使用IP): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        DOMAIN=$(curl -s ifconfig.me)
        log_info "使用IP地址: $DOMAIN"
    fi

    # 获取管理员邮箱
    while [ -z "$ADMIN_EMAIL" ]; do
        read -p "请输入管理员邮箱: " ADMIN_EMAIL
    done

    # 获取管理员密码
    while [ -z "$ADMIN_PASSWORD" ]; do
        read -s -p "请输入管理员密码 (至少8位): " ADMIN_PASSWORD
        echo ""
        if [ ${#ADMIN_PASSWORD} -lt 8 ]; then
            log_error "密码长度至少8位"
            ADMIN_PASSWORD=""
        fi
    done
}

# 安装项目依赖
install_project_dependencies() {
    log_info "安装项目依赖..."
    
    # 检查是否在项目目录中
    if [ ! -f "backend/main.py" ]; then
        log_error "未找到项目文件，请确保在正确的目录中运行脚本"
        exit 1
    fi
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    if [ -f "backend/$COMPATIBLE_REQUIREMENTS" ]; then
        log_info "使用兼容的requirements文件: $COMPATIBLE_REQUIREMENTS"
        pip install -r "backend/$COMPATIBLE_REQUIREMENTS"
    elif [ -f "backend/requirements_vps.txt" ]; then
        log_info "使用标准requirements文件: requirements_vps.txt"
        pip install -r backend/requirements_vps.txt
    else
        log_warning "未找到requirements文件，安装基础依赖..."
        pip install fastapi uvicorn sqlalchemy pymysql python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv email-validator
    fi
    
    log_success "项目依赖安装完成"
}

# 主安装流程
main() {
    echo "=========================================="
    echo "🚀 XBoard Modern VPS 智能安装脚本"
    echo "=========================================="
    echo ""

    # 检查是否为root
    check_root

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --auto)
                INSTALL_MODE="auto"
                shift
                ;;
            --domain=*)
                DOMAIN="${1#*=}"
                shift
                ;;
            --email=*)
                ADMIN_EMAIL="${1#*=}"
                shift
                ;;
            --password=*)
                ADMIN_PASSWORD="${1#*=}"
                shift
                ;;
            --help)
                echo "使用方法:"
                echo "  $0 --auto                                    # 自动安装模式"
                echo "  $0 --domain=example.com                     # 指定域名"
                echo "  $0 --email=admin@example.com                # 指定管理员邮箱"
                echo "  $0 --password=yourpassword                  # 指定管理员密码"
                echo ""
                echo "示例:"
                echo "  $0 --auto --domain=xboard.example.com"
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done

    # 检测VPS信息
    detect_vps_info

    # 更新系统
    update_system

    # 安装基础软件
    install_python
    install_nodejs

    # 检测项目路径
    detect_project_path

    # 配置模式选择
    if [ "$INSTALL_MODE" = "auto" ]; then
        auto_configure
    else
        manual_configure
    fi

    # 安装数据库
    install_database

    # 安装Nginx
    install_nginx

    # 设置Python环境
    setup_python_environment

    # 构建前端
    build_frontend

    # 配置环境变量
    configure_environment

    # 初始化数据库
    initialize_database

    # 创建systemd服务
    create_systemd_service

    # 配置防火墙
    configure_firewall

    # 安装SSL证书
    install_ssl_certificate

    # 创建备份脚本
    create_backup_script

    # 显示完成信息
    show_completion_info
}

# 运行主函数
main "$@"
