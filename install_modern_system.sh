#!/bin/bash

# ================================
# XBoard Modern 现代系统安装脚本
# 支持 Nginx 1.28+, MySQL 5.7+, PHP 8.2+
# ================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

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
DB_TYPE="mysql"
DB_HOST="localhost"
DB_PORT="3306"
DB_NAME="xboard"
DB_USER="xboard"
DB_PASSWORD=""
ADMIN_EMAIL="admin@localhost"
ADMIN_PASSWORD=""
INSTALL_MODE="auto"

echo "=========================================="
echo "🚀 XBoard Modern 现代系统安装脚本"
echo "支持 Nginx 1.28+, MySQL 5.7+, PHP 8.2+"
echo "=========================================="
echo ""

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root用户运行此脚本"
        exit 1
    fi
}

# 检测系统信息
detect_system_info() {
    log_info "检测系统信息..."

    # 检测操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
        OS_CODENAME=$VERSION_CODENAME
    else
        log_error "无法检测操作系统类型"
        exit 1
    fi

    # 检测系统架构
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        ARCH="amd64"
    elif [ "$ARCH" = "aarch64" ]; then
        ARCH="arm64"
    fi

    # 检测已安装的软件版本
    NGINX_VERSION=""
    MYSQL_VERSION=""
    PHP_VERSION=""
    PYTHON_VERSION=""

    # 检测Nginx版本
    if command -v nginx &> /dev/null; then
        NGINX_VERSION=$(nginx -v 2>&1 | grep -oE 'nginx/[0-9]+\.[0-9]+\.[0-9]+' | cut -d'/' -f2)
        log_info "检测到Nginx: $NGINX_VERSION"
    fi

    # 检测MySQL版本
    if command -v mysql &> /dev/null; then
        MYSQL_VERSION=$(mysql --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        log_info "检测到MySQL: $MYSQL_VERSION"
    fi

    # 检测PHP版本
    if command -v php &> /dev/null; then
        PHP_VERSION=$(php --version | grep -oE 'PHP [0-9]+\.[0-9]+\.[0-9]+' | cut -d' ' -f2)
        log_info "检测到PHP: $PHP_VERSION"
    fi

    # 检测Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        log_info "检测到Python: $PYTHON_VERSION"
    fi

    log_success "系统信息: $OS $OS_VERSION ($OS_CODENAME), 架构: $ARCH"
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
    exit 1
}

# 检查系统依赖
check_system_dependencies() {
    log_info "检查系统依赖..."

    # 检查Python版本
    if [ -z "$PYTHON_VERSION" ]; then
        log_error "未检测到Python，请先安装Python 3.8+"
        exit 1
    fi

    # 检查Python版本是否满足要求
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        log_error "Python版本过低，需要Python 3.8+，当前版本: $PYTHON_VERSION"
        exit 1
    fi

    # 检查Nginx版本
    if [ -z "$NGINX_VERSION" ]; then
        log_warning "未检测到Nginx，将自动安装"
    else
        NGINX_MAJOR=$(echo $NGINX_VERSION | cut -d. -f1)
        NGINX_MINOR=$(echo $NGINX_VERSION | cut -d. -f2)
        
        if [ "$NGINX_MAJOR" -lt 1 ] || ([ "$NGINX_MAJOR" -eq 1 ] && [ "$NGINX_MINOR" -lt 18 ]); then
            log_warning "Nginx版本较低，建议升级到1.18+，当前版本: $NGINX_VERSION"
        fi
    fi

    # 检查MySQL版本
    if [ -z "$MYSQL_VERSION" ]; then
        log_warning "未检测到MySQL，将自动安装"
    else
        MYSQL_MAJOR=$(echo $MYSQL_VERSION | cut -d. -f1)
        MYSQL_MINOR=$(echo $MYSQL_VERSION | cut -d. -f2)
        
        if [ "$MYSQL_MAJOR" -lt 5 ] || ([ "$MYSQL_MAJOR" -eq 5 ] && [ "$MYSQL_MINOR" -lt 7 ]); then
            log_warning "MySQL版本较低，建议升级到5.7+，当前版本: $MYSQL_VERSION"
        fi
    fi

    # 检查PHP版本
    if [ -z "$PHP_VERSION" ]; then
        log_info "未检测到PHP，跳过PHP配置"
    else
        PHP_MAJOR=$(echo $PHP_VERSION | cut -d. -f1)
        PHP_MINOR=$(echo $PHP_VERSION | cut -d. -f2)
        
        if [ "$PHP_MAJOR" -lt 8 ] || ([ "$PHP_MAJOR" -eq 8 ] && [ "$PHP_MINOR" -lt 1 ]); then
            log_warning "PHP版本较低，建议升级到8.1+，当前版本: $PHP_VERSION"
        fi
    fi

    log_success "系统依赖检查完成"
}

# 安装缺失的系统组件
install_system_components() {
    log_info "安装缺失的系统组件..."

    # 安装Python虚拟环境包
    log_info "安装Python虚拟环境包..."
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ]; then
        case $PYTHON_MINOR in
            12)
                apt install -y python3.12-venv python3.12-dev python3-pip
                ;;
            11)
                apt install -y python3.11-venv python3.11-dev python3-pip
                ;;
            10)
                apt install -y python3.10-venv python3.10-dev python3-pip
                ;;
            9)
                apt install -y python3.9-venv python3.9-dev python3-pip
                ;;
            8)
                apt install -y python3.8-venv python3.8-dev python3-pip
                ;;
            *)
                apt install -y python3-venv python3-dev python3-pip
                ;;
        esac
    else
        apt install -y python3-venv python3-dev python3-pip
    fi

    # 安装Nginx (如果未安装)
    if [ -z "$NGINX_VERSION" ]; then
        log_info "安装Nginx..."
        apt install -y nginx
        NGINX_VERSION=$(nginx -v 2>&1 | grep -oE 'nginx/[0-9]+\.[0-9]+\.[0-9]+' | cut -d'/' -f2)
        log_success "Nginx安装完成: $NGINX_VERSION"
    fi

    # 安装MySQL (如果未安装)
    if [ -z "$MYSQL_VERSION" ]; then
        log_info "安装MySQL..."
        apt install -y mysql-server mysql-client
        MYSQL_VERSION=$(mysql --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        log_success "MySQL安装完成: $MYSQL_VERSION"
    fi

    # 安装PHP (如果未安装且需要)
    if [ -z "$PHP_VERSION" ] && [ "$PHP_INSTALL" = "true" ]; then
        log_info "安装PHP..."
        apt install -y php8.2 php8.2-fpm php8.2-mysql php8.2-common php8.2-mbstring php8.2-xml php8.2-curl
        PHP_VERSION=$(php --version | grep -oE 'PHP [0-9]+\.[0-9]+\.[0-9]+' | cut -d' ' -f2)
        log_success "PHP安装完成: $PHP_VERSION"
    fi

    log_success "系统组件安装完成"
}

# 设置Python环境
setup_python_environment() {
    log_info "设置Python环境..."

    cd "$PROJECT_ROOT"

    # 确保Python虚拟环境包已安装
    log_info "确保Python虚拟环境包已安装..."
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ]; then
        case $PYTHON_MINOR in
            12)
                apt install -y python3.12-venv python3.12-dev python3-pip
                ;;
            11)
                apt install -y python3.11-venv python3.11-dev python3-pip
                ;;
            10)
                apt install -y python3.10-venv python3.10-dev python3-pip
                ;;
            9)
                apt install -y python3.9-venv python3.9-dev python3-pip
                ;;
            8)
                apt install -y python3.8-venv python3.8-dev python3-pip
                ;;
            *)
                apt install -y python3-venv python3-dev python3-pip
                ;;
        esac
    else
        apt install -y python3-venv python3-dev python3-pip
    fi

    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            log_error "虚拟环境创建失败，尝试使用python3.12..."
            if command -v python3.12 &> /dev/null; then
                python3.12 -m venv venv
            elif command -v python3.11 &> /dev/null; then
                python3.11 -m venv venv
            elif command -v python3.10 &> /dev/null; then
                python3.10 -m venv venv
            else
                log_error "无法创建虚拟环境，请检查Python安装"
                exit 1
            fi
        fi
    fi

    # 激活虚拟环境
    source venv/bin/activate

    # 升级pip
    pip install --upgrade pip

    # 智能选择requirements文件
    if [ -f "backend/requirements_modern.txt" ]; then
        log_info "使用现代系统requirements文件"
        pip install -r backend/requirements_modern.txt
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
# 现代系统版本
# ================================

# 数据库配置
DATABASE_URL=mysql+pymysql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME

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

# Redis配置
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

# 系统信息
SYSTEM_NGINX_VERSION=$NGINX_VERSION
SYSTEM_MYSQL_VERSION=$MYSQL_VERSION
SYSTEM_PHP_VERSION=$PHP_VERSION
SYSTEM_PYTHON_VERSION=$PYTHON_VERSION
EOF

    log_success "环境变量配置完成"
}

# 配置Nginx
configure_nginx() {
    log_info "配置Nginx..."

    # 备份默认配置
    cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

    # 创建XBoard站点配置
    cat > /etc/nginx/sites-available/xboard << EOF
server {
    listen 80;
    server_name _;
    root /var/www/xboard/frontend/dist;
    index index.html;

    # 前端静态文件
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # 上传文件
    location /uploads/ {
        alias /var/www/xboard/uploads/;
    }

    # PHP支持 (如果安装了PHP)
    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.2-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME \$document_root\$fastcgi_script_name;
        include fastcgi_params;
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF

    # 启用站点
    ln -sf /etc/nginx/sites-available/xboard /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    # 创建网站目录
    mkdir -p /var/www/xboard
    chown -R www-data:www-data /var/www/xboard

    # 测试配置
    nginx -t

    # 重启Nginx
    systemctl restart nginx
    systemctl enable nginx

    log_success "Nginx配置完成"
}

# 配置MySQL
configure_mysql() {
    log_info "配置MySQL..."

    # 启动MySQL服务
    systemctl start mysql
    systemctl enable mysql

    # 创建数据库和用户
    mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
    mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
    mysql -e "FLUSH PRIVILEGES;"

    log_success "MySQL配置完成"
}

# 创建systemd服务
create_systemd_service() {
    log_info "创建systemd服务..."

    cat > /etc/systemd/system/xboard.service << EOF
[Unit]
Description=XBoard Modern Backend
After=network.target mysql.service

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

# 复制项目文件
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
    echo "🎉 XBoard Modern 现代系统安装完成！"
    echo "=========================================="
    echo ""
    echo "📊 系统信息："
    echo "   Nginx: $NGINX_VERSION"
    echo "   MySQL: $MYSQL_VERSION"
    echo "   PHP: $PHP_VERSION"
    echo "   Python: $PYTHON_VERSION"
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
    echo "   1. 请修改 .env 文件中的数据库密码和邮件配置"
    echo "   2. 建议配置SSL证书"
    echo "   3. 定期备份数据库"
    echo "   4. 系统已配置安全头和安全设置"
    echo ""
}

# 主安装流程
main() {
    # 检查是否为root
    check_root

    # 检测系统信息
    detect_system_info

    # 智能检测项目路径
    detect_project_path

    # 检查系统依赖
    check_system_dependencies

    # 安装缺失的系统组件
    install_system_components

    # 设置Python环境
    setup_python_environment

    # 构建前端
    build_frontend

    # 配置环境变量
    configure_environment

    # 配置Nginx
    configure_nginx

    # 配置MySQL
    configure_mysql

    # 创建systemd服务
    create_systemd_service

    # 复制项目文件
    copy_project_files

    # 启动服务
    start_services

    # 显示完成信息
    show_completion_info
}

# 运行主函数
main "$@"
