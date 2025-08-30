#!/bin/bash

# ================================
# XBoard Modern 宝塔面板安装脚本
# ================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "此脚本需要root权限运行"
        exit 1
    fi
}

# 检查系统
check_system() {
    print_step "检查系统环境..."
    
    # 检查操作系统
    if [[ -f /etc/redhat-release ]]; then
        OS="centos"
        print_message "检测到 CentOS/RHEL 系统"
    elif [[ -f /etc/debian_version ]]; then
        OS="debian"
        print_message "检测到 Debian/Ubuntu 系统"
    else
        print_error "不支持的操作系统"
        exit 1
    fi
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_message "Python版本: $PYTHON_VERSION"
    else
        print_error "未找到Python3，请先安装Python3"
        exit 1
    fi
    
    # 检查Node.js版本
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_message "Node.js版本: $NODE_VERSION"
    else
        print_warning "未找到Node.js，将在后续步骤中安装"
    fi
}

# 安装系统依赖
install_dependencies() {
    print_step "安装系统依赖..."
    
    if [[ $OS == "centos" ]]; then
        yum update -y
        yum install -y epel-release
        yum groupinstall -y "Development Tools"
        yum install -y python3 python3-pip python3-devel
        yum install -y nginx redis
        yum install -y git wget curl
        yum install -y libffi-devel openssl-devel
    else
        apt update -y
        apt install -y build-essential
        apt install -y python3 python3-pip python3-dev
        apt install -y nginx redis-server
        apt install -y git wget curl
        apt install -y libffi-dev libssl-dev
    fi
}

# 安装Node.js
install_nodejs() {
    print_step "安装Node.js..."
    
    if ! command -v node &> /dev/null; then
        # 使用NodeSource安装最新的LTS版本
        curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
        
        if [[ $OS == "centos" ]]; then
            yum install -y nodejs
        else
            apt install -y nodejs
        fi
        
        print_message "Node.js安装完成"
    else
        print_message "Node.js已存在"
    fi
}

# 安装宝塔面板
install_bt_panel() {
    print_step "安装宝塔面板..."
    
    if ! command -v bt &> /dev/null; then
        wget -O install.sh http://download.bt.cn/install/install_6.0.sh
        bash install.sh
        print_message "宝塔面板安装完成"
    else
        print_message "宝塔面板已存在"
    fi
}

# 创建项目目录
create_project_dir() {
    print_step "创建项目目录..."
    
    PROJECT_DIR="/www/wwwroot/xboard-modern"
    
    if [[ ! -d $PROJECT_DIR ]]; then
        mkdir -p $PROJECT_DIR
        print_message "项目目录创建完成: $PROJECT_DIR"
    else
        print_message "项目目录已存在: $PROJECT_DIR"
    fi
}

# 配置Python环境
setup_python_env() {
    print_step "配置Python环境..."
    
    cd /www/wwwroot/xboard-modern
    
    # 创建虚拟环境
    python3 -m venv venv
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装Python依赖
    if [[ -f requirements.txt ]]; then
        pip install -r requirements.txt
        print_message "Python依赖安装完成"
    else
        print_error "未找到requirements.txt文件"
        exit 1
    fi
}

# 配置前端环境
setup_frontend_env() {
    print_step "配置前端环境..."
    
    cd /www/wwwroot/xboard-modern/frontend
    
    # 安装Node.js依赖
    if [[ -f package.json ]]; then
        npm install
        print_message "前端依赖安装完成"
    else
        print_error "未找到package.json文件"
        exit 1
    fi
}

# 构建前端
build_frontend() {
    print_step "构建前端..."
    
    cd /www/wwwroot/xboard-modern/frontend
    
    # 构建生产版本
    npm run build
    
    print_message "前端构建完成"
}

# 配置数据库
setup_database() {
    print_step "配置数据库..."
    
    # 在宝塔面板中创建数据库
    print_message "请在宝塔面板中手动创建数据库:"
    print_message "1. 登录宝塔面板"
    print_message "2. 进入数据库管理"
    print_message "3. 创建MySQL数据库: xboard_db"
    print_message "4. 记录数据库用户名和密码"
}

# 配置环境变量
setup_env() {
    print_step "配置环境变量..."
    
    cd /www/wwwroot/xboard-modern
    
    # 复制环境变量文件
    if [[ -f env.example ]]; then
        cp env.example .env
        print_message "环境变量文件已创建，请编辑 .env 文件配置数据库等信息"
    else
        print_error "未找到env.example文件"
        exit 1
    fi
}

# 创建系统服务
create_systemd_service() {
    print_step "创建系统服务..."
    
    cat > /etc/systemd/system/xboard-backend.service << EOF
[Unit]
Description=XBoard Backend Service
After=network.target

[Service]
Type=simple
User=www
Group=www
WorkingDirectory=/www/wwwroot/xboard-modern
Environment=PATH=/www/wwwroot/xboard-modern/venv/bin
ExecStart=/www/wwwroot/xboard-modern/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载systemd
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable xboard-backend
    
    print_message "后端服务创建完成"
}

# 配置Nginx
setup_nginx() {
    print_step "配置Nginx..."
    
    # 创建Nginx配置文件
    cat > /etc/nginx/conf.d/xboard.conf << EOF
server {
    listen 80;
    server_name yourdomain.com;  # 请修改为您的域名
    
    # 前端静态文件
    location / {
        root /www/wwwroot/xboard-modern/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        index index.html;
    }
    
    # 后端API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # 测试Nginx配置
    nginx -t
    
    # 重启Nginx
    systemctl restart nginx
    
    print_message "Nginx配置完成"
}

# 配置防火墙
setup_firewall() {
    print_step "配置防火墙..."
    
    if command -v firewall-cmd &> /dev/null; then
        # CentOS防火墙
        firewall-cmd --permanent --add-port=80/tcp
        firewall-cmd --permanent --add-port=443/tcp
        firewall-cmd --reload
    elif command -v ufw &> /dev/null; then
        # Ubuntu防火墙
        ufw allow 80/tcp
        ufw allow 443/tcp
    fi
    
    print_message "防火墙配置完成"
}

# 启动服务
start_services() {
    print_step "启动服务..."
    
    # 启动Redis
    systemctl start redis
    systemctl enable redis
    
    # 启动后端服务
    systemctl start xboard-backend
    
    print_message "服务启动完成"
}

# 显示安装信息
show_install_info() {
    print_step "安装完成！"
    echo ""
    echo "=========================================="
    echo "XBoard Modern 安装完成"
    echo "=========================================="
    echo ""
    echo "项目目录: /www/wwwroot/xboard-modern"
    echo "前端地址: http://yourdomain.com"
    echo "后端API: http://yourdomain.com/api"
    echo "宝塔面板: http://yourdomain.com:8888"
    echo ""
    echo "下一步操作:"
    echo "1. 编辑 /www/wwwroot/xboard-modern/.env 文件"
    echo "2. 配置数据库连接信息"
    echo "3. 配置邮件服务器信息"
    echo "4. 在宝塔面板中配置SSL证书"
    echo "5. 访问网站进行初始化设置"
    echo ""
    echo "服务管理命令:"
    echo "启动后端: systemctl start xboard-backend"
    echo "停止后端: systemctl stop xboard-backend"
    echo "重启后端: systemctl restart xboard-backend"
    echo "查看状态: systemctl status xboard-backend"
    echo ""
}

# 主函数
main() {
    echo "=========================================="
    echo "XBoard Modern 宝塔面板安装脚本"
    echo "=========================================="
    echo ""
    
    check_root
    check_system
    install_dependencies
    install_nodejs
    install_bt_panel
    create_project_dir
    setup_python_env
    setup_frontend_env
    build_frontend
    setup_database
    setup_env
    create_systemd_service
    setup_nginx
    setup_firewall
    start_services
    show_install_info
}

# 运行主函数
main "$@" 