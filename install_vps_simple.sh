#!/bin/bash

# ================================
# XBoard VPS 简化安装脚本
# 专门解决Python虚拟环境问题
# ================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=========================================="
echo "🚀 XBoard VPS 简化安装脚本"
echo "=========================================="
echo ""

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    log_error "请使用root用户运行此脚本"
    exit 1
fi

# 检测系统信息
log_info "检测系统信息..."

# 检测Python版本
PYTHON_VERSION=""
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
    log_success "检测到Python: $PYTHON_VERSION"
else
    log_error "未检测到Python3，请先安装Python"
    exit 1
fi

# 检测Nginx版本
NGINX_VERSION=""
if command -v nginx &> /dev/null; then
    NGINX_VERSION=$(nginx -v 2>&1 | grep -oE 'nginx/[0-9]+\.[0-9]+\.[0-9]+' | cut -d'/' -f2)
    log_success "检测到Nginx: $NGINX_VERSION"
fi

# 检测MySQL版本
MYSQL_VERSION=""
if command -v mysql &> /dev/null; then
    MYSQL_VERSION=$(mysql --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    log_success "检测到MySQL: $MYSQL_VERSION"
fi

# 检测PHP版本
PHP_VERSION=""
if command -v php &> /dev/null; then
    PHP_VERSION=$(php --version | grep -oE 'PHP [0-9]+\.[0-9]+\.[0-9]+' | cut -d' ' -f2)
    log_success "检测到PHP: $PHP_VERSION"
fi

# 安装Python虚拟环境包
log_info "安装Python虚拟环境包..."
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -eq 3 ]; then
    case $PYTHON_MINOR in
        12)
            log_info "安装Python 3.12虚拟环境包..."
            apt install -y python3.12-venv python3.12-dev python3-pip
            ;;
        11)
            log_info "安装Python 3.11虚拟环境包..."
            apt install -y python3.11-venv python3.11-dev python3-pip
            ;;
        10)
            log_info "安装Python 3.10虚拟环境包..."
            apt install -y python3.10-venv python3.10-dev python3-pip
            ;;
        9)
            log_info "安装Python 3.9虚拟环境包..."
            apt install -y python3.9-venv python3.9-dev python3-pip
            ;;
        8)
            log_info "安装Python 3.8虚拟环境包..."
            apt install -y python3.8-venv python3.8-dev python3-pip
            ;;
        *)
            log_info "安装通用Python虚拟环境包..."
            apt install -y python3-venv python3-dev python3-pip
            ;;
    esac
else
    apt install -y python3-venv python3-dev python3-pip
fi

log_success "Python虚拟环境包安装完成！"

# 检查项目目录
PROJECT_ROOT=""
if [ -d "backend" ] && [ -d "frontend" ]; then
    PROJECT_ROOT="$(pwd)"
    log_success "检测到项目目录: $PROJECT_ROOT"
else
    log_error "请在项目根目录运行此脚本"
    exit 1
fi

# 创建Python虚拟环境
log_info "创建Python虚拟环境..."
if [ -d "venv" ]; then
    log_info "虚拟环境已存在，删除重建..."
    rm -rf venv
fi

# 尝试创建虚拟环境
python3 -m venv venv
if [ $? -ne 0 ]; then
    log_warning "使用python3创建虚拟环境失败，尝试其他版本..."
    
    if command -v python3.12 &> /dev/null; then
        log_info "使用python3.12创建虚拟环境..."
        python3.12 -m venv venv
    elif command -v python3.11 &> /dev/null; then
        log_info "使用python3.11创建虚拟环境..."
        python3.11 -m venv venv
    elif command -v python3.10 &> /dev/null; then
        log_info "使用python3.10创建虚拟环境..."
        python3.10 -m venv venv
    else
        log_error "无法创建虚拟环境，请检查Python安装"
        exit 1
    fi
fi

if [ -d "venv" ]; then
    log_success "虚拟环境创建成功！"
else
    log_error "虚拟环境创建失败"
    exit 1
fi

# 激活虚拟环境
log_info "激活虚拟环境..."
source venv/bin/activate

# 升级pip
log_info "升级pip..."
pip install --upgrade pip

# 安装依赖
log_info "安装Python依赖..."
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

log_success "Python依赖安装完成！"

# 构建前端
log_info "构建前端..."
cd frontend

# 检查Node.js
if ! command -v node &> /dev/null; then
    log_info "安装Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs
fi

# 安装前端依赖
log_info "安装前端依赖..."
npm install --production=false

# 构建前端
if grep -q '"build"' package.json; then
    log_info "执行前端构建..."
    npm run build
    log_success "前端构建完成"
else
    log_warning "package.json中未找到build脚本，跳过构建"
fi

cd ..

# 配置环境变量
log_info "配置环境变量..."
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

cat > .env << EOF
# ================================
# XBoard 环境变量配置
# ================================

# 数据库配置
DATABASE_URL=mysql+pymysql://xboard:your_password@localhost:3306/xboard

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

# 管理员配置
ADMIN_EMAIL=admin@localhost
ADMIN_PASSWORD=admin123

# 系统信息
SYSTEM_NGINX_VERSION=$NGINX_VERSION
SYSTEM_MYSQL_VERSION=$MYSQL_VERSION
SYSTEM_PHP_VERSION=$PHP_VERSION
SYSTEM_PYTHON_VERSION=$PYTHON_VERSION
EOF

log_success "环境变量配置完成！"

# 配置Nginx
log_info "配置Nginx..."
if [ -z "$NGINX_VERSION" ]; then
    log_info "安装Nginx..."
    apt install -y nginx
fi

# 创建Nginx配置
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

# 测试Nginx配置
nginx -t

# 重启Nginx
systemctl restart nginx
systemctl enable nginx

log_success "Nginx配置完成！"

# 创建systemd服务
log_info "创建systemd服务..."
cat > /etc/systemd/system/xboard.service << EOF
[Unit]
Description=XBoard Backend
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

log_success "systemd服务创建完成！"

# 复制项目文件
log_info "复制项目文件到网站目录..."
if [ -d "frontend/dist" ]; then
    cp -r frontend/dist/* /var/www/xboard/frontend/
fi

cp -r backend /var/www/xboard/
cp -r uploads /var/www/xboard/ 2>/dev/null || mkdir -p /var/www/xboard/uploads
cp .env /var/www/xboard/

chown -R www-data:www-data /var/www/xboard
chmod -R 755 /var/www/xboard

log_success "项目文件复制完成！"

# 启动服务
log_info "启动服务..."
systemctl start xboard.service
systemctl status xboard.service

log_success "服务启动完成！"

# 显示完成信息
echo ""
echo "=========================================="
echo "🎉 XBoard 安装完成！"
echo "=========================================="
echo ""
echo "📊 系统信息："
echo "   Python: $PYTHON_VERSION"
echo "   Nginx: $NGINX_VERSION"
echo "   MySQL: $MYSQL_VERSION"
echo "   PHP: $PHP_VERSION"
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
echo ""
