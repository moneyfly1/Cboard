#!/bin/bash

# ================================
# XBoard Modern 智能安装脚本
# 自动识别当前目录并适配安装
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

# 获取当前目录
get_current_dir() {
    CURRENT_DIR=$(pwd)
    print_message "当前目录: $CURRENT_DIR"
    
    # 检查是否在正确的项目目录中
    if [[ ! -f "backend/main.py" ]] || [[ ! -f "frontend/package.json" ]]; then
        print_error "当前目录不是有效的XBoard Modern项目目录"
        print_error "请确保您在包含backend/和frontend/文件夹的项目根目录中"
        exit 1
    fi
    
    print_message "项目目录验证通过"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_warning "建议使用root权限运行此脚本"
        print_warning "某些操作可能需要sudo权限"
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
        yum install -y python3 python3-pip python3-devel python3-venv
        yum install -y nginx redis
        yum install -y git wget curl
        yum install -y libffi-devel openssl-devel
    else
        apt update -y
        apt install -y build-essential
        apt install -y python3 python3-pip python3-dev python3-venv
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

# 检查宝塔面板
check_bt_panel() {
    print_step "检查宝塔面板..."
    
    if command -v bt &> /dev/null; then
        print_message "宝塔面板已存在"
    else
        print_warning "未检测到宝塔面板"
        print_message "请手动安装宝塔面板或使用以下命令："
        if [[ $OS == "centos" ]]; then
            print_message "yum install -y wget && wget -O install.sh http://download.bt.cn/install/install_6.0.sh && sh install.sh"
        else
            print_message "wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh"
        fi
    fi
}

# 配置Python环境
setup_python_env() {
    print_step "配置Python环境..."
    
    # 删除可能存在的旧虚拟环境
    if [[ -d "venv" ]]; then
        print_message "删除旧的虚拟环境..."
        rm -rf venv
    fi
    
    # 创建虚拟环境
    print_message "创建Python虚拟环境..."
    python3 -m venv venv
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    print_message "升级pip..."
    pip install --upgrade pip
    
    # 安装Python依赖
    if [[ -f "backend/requirements.txt" ]]; then
        print_message "安装Python依赖..."
        pip install -r backend/requirements.txt
        print_message "Python依赖安装完成"
    else
        print_error "未找到backend/requirements.txt文件"
        exit 1
    fi
}

# 配置前端环境
setup_frontend_env() {
    print_step "配置前端环境..."
    
    if [[ -f "frontend/package.json" ]]; then
        cd frontend
        
        # 安装Node.js依赖
        print_message "安装前端依赖..."
        npm install
        print_message "前端依赖安装完成"
        
        # 构建前端
        print_message "构建前端..."
        npm run build
        print_message "前端构建完成"
        
        cd ..
    else
        print_error "未找到frontend/package.json文件"
        exit 1
    fi
}

# 配置环境变量
setup_env() {
    print_step "配置环境变量..."
    
    # 复制环境变量文件
    if [[ -f "env.example" ]]; then
        cp env.example .env
        print_message "环境变量文件已创建: .env"
        print_message "请编辑 .env 文件配置数据库等信息"
        
        # 自动检测域名
        if [[ -n "$CURRENT_DIR" ]]; then
            # 尝试从目录名提取域名
            DIR_NAME=$(basename "$CURRENT_DIR")
            if [[ "$DIR_NAME" == *"."* ]]; then
                print_message "检测到可能的域名: $DIR_NAME"
                print_message "请在 .env 文件中设置: BT_DOMAIN=$DIR_NAME"
            fi
        fi
    else
        print_error "未找到env.example文件"
        exit 1
    fi
}

# 创建系统服务
create_systemd_service() {
    print_step "创建系统服务..."
    
    # 获取当前目录的绝对路径
    PROJECT_DIR=$(pwd)
    
    cat > /etc/systemd/system/xboard-backend.service << EOF
[Unit]
Description=XBoard Backend Service
After=network.target

[Service]
Type=simple
User=www
Group=www
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
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
    print_message "项目目录: $PROJECT_DIR"
}

# 配置Nginx
setup_nginx() {
    print_step "配置Nginx..."
    
    # 获取当前目录的绝对路径
    PROJECT_DIR=$(pwd)
    
    # 创建Nginx配置文件
    cat > /etc/nginx/conf.d/xboard.conf << EOF
server {
    listen 80;
    server_name _;  # 将匹配所有域名，您可以在宝塔面板中修改
    
    # 前端静态文件
    location / {
        root $PROJECT_DIR/frontend/dist;
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
    print_message "前端目录: $PROJECT_DIR/frontend/dist"
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
    echo "XBoard Modern 智能安装完成"
    echo "=========================================="
    echo ""
    echo "项目目录: $(pwd)"
    echo "前端地址: http://$(hostname -I | awk '{print $1}')"
    echo "后端API: http://$(hostname -I | awk '{print $1}'):8000"
    echo ""
    echo "下一步操作:"
    echo "1. 编辑 .env 文件配置数据库等信息"
    echo "2. 在宝塔面板中创建数据库"
    echo "3. 运行数据库初始化: python3 init_database.py"
    echo "4. 在宝塔面板中配置网站和SSL证书"
    echo "5. 访问网站进行初始化设置"
    echo ""
    echo "服务管理命令:"
    echo "启动后端: systemctl start xboard-backend"
    echo "停止后端: systemctl stop xboard-backend"
    echo "重启后端: systemctl restart xboard-backend"
    echo "查看状态: systemctl status xboard-backend"
    echo "查看日志: journalctl -u xboard-backend -f"
    echo ""
    echo "重要提醒:"
    echo "- 请确保在宝塔面板中正确配置网站域名"
    echo "- 请配置SSL证书以确保安全访问"
    echo "- 请及时修改默认管理员密码"
    echo ""
}

# 主函数
main() {
    echo "=========================================="
    echo "XBoard Modern 智能安装脚本"
    echo "=========================================="
    echo ""
    
    get_current_dir
    check_root
    check_system
    install_dependencies
    install_nodejs
    check_bt_panel
    setup_python_env
    setup_frontend_env
    setup_env
    create_systemd_service
    setup_nginx
    setup_firewall
    start_services
    show_install_info
}

# 运行主函数
main "$@" 