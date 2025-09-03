#!/bin/bash

# ================================
# XBoard Modern VPS 安装脚本 (Ubuntu 18.04 修复版)
# 专为Ubuntu 18.04环境优化，自动处理Python版本兼容性和软链接问题
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
PYTHON_VERSION=""
COMPATIBLE_REQUIREMENTS=""
INSTALL_MODE="auto"  # auto: 自动检测跳过, manual: 手动选择

# 显示帮助信息
show_help() {
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --auto      自动模式：检测已安装组件并跳过 (默认)"
    echo "  --manual    手动模式：手动选择安装组件"
    echo "  --help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0              # 自动模式"
    echo "  $0 --manual     # 手动模式"
    echo ""
    echo "自动模式特点:"
    echo "  ✅ 智能检测已安装组件"
    echo "  ✅ 自动跳过重复安装"
    echo "  ✅ 快速修复常见问题"
    echo "  ✅ 节省安装时间"
    echo ""
}

# 解析命令行参数
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --auto)
                INSTALL_MODE="auto"
                shift
                ;;
            --manual)
                INSTALL_MODE="manual"
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
}

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
    
    # 检查是否为Ubuntu 18.04
    if [ "$OS" = "ubuntu" ] && [ "$OS_VERSION" = "18.04" ]; then
        log_info "检测到Ubuntu 18.04，将使用兼容的Python版本"
    fi
}

# 检测已安装的组件
detect_installed_components() {
    log_info "检测已安装的组件..."
    
    # 检测Python
    if command -v python3 &> /dev/null; then
        PYTHON_INSTALLED=true
        PYTHON_VER=$(python3 --version 2>&1)
        log_success "检测到已安装的Python: $PYTHON_VER"
    else
        PYTHON_INSTALLED=false
        log_info "未检测到Python，需要安装"
    fi
    
    # 检测Node.js
    if command -v node &> /dev/null; then
        NODE_INSTALLED=true
        NODE_VER=$(node --version 2>&1)
        log_success "检测到已安装的Node.js: $NODE_VER"
    else
        NODE_INSTALLED=false
        log_info "未检测到Node.js，需要安装"
    fi
    
    # 检测MySQL
    if systemctl is-active --quiet mysql 2>/dev/null || systemctl is-active --quiet mysqld 2>/dev/null; then
        MYSQL_INSTALLED=true
        log_success "检测到已安装的MySQL"
    else
        MYSQL_INSTALLED=false
        log_info "未检测到MySQL，需要安装"
    fi
    
    # 检测Nginx
    if command -v nginx &> /dev/null; then
        NGINX_INSTALLED=true
        NGINX_VER=$(nginx -v 2>&1)
        log_success "检测到已安装的Nginx: $NGINX_VER"
    else
        NGINX_INSTALLED=false
        log_info "未检测到Nginx，需要安装"
    fi
    
    # 检测虚拟环境
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        VENV_INSTALLED=true
        log_success "检测到已创建的虚拟环境"
    else
        VENV_INSTALLED=false
        log_info "未检测到虚拟环境，需要创建"
    fi
    
    # 检测项目依赖
    if [ -d "venv" ] && [ -f "venv/bin/pip" ]; then
        source venv/bin/activate
        if pip list | grep -q "fastapi"; then
            DEPS_INSTALLED=true
            log_success "检测到已安装的项目依赖"
        else
            DEPS_INSTALLED=false
            log_info "项目依赖未完全安装，需要安装"
        fi
        deactivate
    else
        DEPS_INSTALLED=false
    fi
    
    # 检测前端构建
    if [ -d "frontend/dist" ] && [ -f "frontend/dist/index.html" ]; then
        FRONTEND_BUILT=true
        log_success "检测到已构建的前端"
    else
        FRONTEND_BUILT=false
        log_info "前端未构建，需要构建"
    fi
}

# 快速修复常见问题
quick_fix_common_issues() {
    log_info "快速修复常见问题..."
    
    # 修复Python软链接问题
    if [ -L "/usr/bin/python3" ] && [ ! -e "/usr/bin/python3" ]; then
        log_warning "修复损坏的python3软链接..."
        rm -f /usr/bin/python3
        ln -sf /usr/bin/python3.6 /usr/bin/python3
    fi
    
    # 修复pip3问题
    if [ -L "/usr/bin/pip3" ] && [ ! -e "/usr/bin/pip3" ]; then
        log_warning "修复损坏的pip3软链接..."
        rm -f /usr/bin/pip3
        ln -sf /usr/bin/python3 /usr/bin/pip3
    fi
    
    # 修复add-apt-repository
    if [ -f "/usr/bin/add-apt-repository" ] && ! /usr/bin/add-apt-repository --help >/dev/null 2>&1; then
        log_warning "修复add-apt-repository..."
        sed -i '1s|#!/usr/bin/python3|#!/usr/bin/python3.6|' /usr/bin/add-apt-repository 2>/dev/null || true
    fi
    
    log_success "快速修复完成"
}

# 修复npm问题
fix_npm_issues() {
    log_info "检查并修复npm问题..."
    
    # 检查npm是否存在
    if ! command -v npm &> /dev/null; then
        log_warning "npm命令不存在，尝试修复..."
        
        # 检查Node.js安装状态
        if command -v node &> /dev/null || command -v nodejs &> /dev/null; then
            # 尝试创建npm软链接
            if [ -f "/usr/bin/nodejs" ]; then
                ln -sf /usr/bin/nodejs /usr/bin/node 2>/dev/null || true
                ln -sf /usr/bin/nodejs /usr/bin/npm 2>/dev/null || true
                log_info "已创建npm软链接"
            fi
            
            # 如果还是不行，尝试安装npm
            if ! command -v npm &> /dev/null; then
                log_info "尝试安装npm..."
                apt install -y npm 2>/dev/null || true
            fi
        fi
        
        # 最终检查
        if command -v npm &> /dev/null; then
            log_success "npm修复成功: $(npm --version 2>&1)"
        else
            log_warning "npm修复失败，需要重新安装Node.js"
        fi
    else
        log_success "npm工作正常: $(npm --version 2>&1)"
    fi
}

# 手动修复Node.js安装
manual_fix_nodejs() {
    log_info "手动修复Node.js安装..."
    
    # 完全清理
    log_info "完全清理Node.js..."
    apt remove -y nodejs nodejs-doc npm 2>/dev/null || true
    apt autoremove -y
    rm -f /usr/bin/node /usr/bin/nodejs /usr/bin/npm
    
    # 清理apt缓存
    apt clean
    apt update
    
    # 强制添加NodeSource仓库
    log_info "强制添加NodeSource仓库..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - || {
        log_error "无法添加NodeSource仓库，尝试备用方案..."
        
        # 备用方案：手动下载安装
        log_info "使用备用方案安装Node.js..."
        cd /tmp
        
        # 下载Node.js 18.x ARM64版本
        wget https://nodejs.org/dist/v18.19.0/node-v18.19.0-linux-arm64.tar.xz
        
        if [ -f "node-v18.19.0-linux-arm64.tar.xz" ]; then
            # 解压
            tar -xf node-v18.19.0-linux-arm64.tar.xz
            
            # 移动到/usr/local
            mv node-v18.19.0-linux-arm64 /usr/local/node
            
            # 创建软链接
            ln -sf /usr/local/node/bin/node /usr/bin/node
            ln -sf /usr/local/node/bin/npm /usr/bin/npm
            
            # 清理下载文件
            rm -f node-v18.19.0-linux-arm64.tar.xz
            
            log_success "手动安装Node.js完成"
            NODE_INSTALLED=true
        else
            log_error "手动下载Node.js失败"
            return 1
        fi
        
        cd /www/wwwroot/dash.moneyfly.top
    }
    
    # 如果NodeSource仓库添加成功，安装
    if [ "$NODE_INSTALLED" != true ]; then
        log_info "通过NodeSource仓库安装..."
        apt install -y nodejs
        
        # 验证安装
        if command -v node &> /dev/null && command -v npm &> /dev/null; then
            NODE_VER=$(node --version 2>&1)
            NPM_VER=$(npm --version 2>&1)
            NODE_INSTALLED=true
            log_success "Node.js安装完成: $NODE_VER, npm: $NPM_VER"
        else
            log_error "Node.js安装仍然失败"
            return 1
        fi
    fi
}

# 智能安装Python
smart_install_python() {
    if [ "$PYTHON_INSTALLED" = true ]; then
        log_info "Python已安装，跳过安装步骤"
        return 0
    fi
    
    log_info "开始安装Python..."
    
    case $OS in
        "ubuntu")
            if [ "$OS_VERSION" = "18.04" ]; then
                log_info "检测到Ubuntu 18.04，使用兼容的Python版本..."
                
                # 快速修复
                quick_fix_common_issues
                
                # 尝试安装Python 3.9
                log_info "尝试安装Python 3.9..."
                if add-apt-repository ppa:deadsnakes/ppa -y 2>/dev/null; then
                    apt update
                    if apt install -y python3.9 python3.9-venv python3.9-dev python3-pip 2>/dev/null; then
                        log_success "Python 3.9安装成功"
                        PYTHON_VERSION="python3.9"
                    else
                        log_warning "Python 3.9安装失败，使用系统Python 3.6"
                        apt install -y python3 python3-venv python3-dev python3-pip
                        PYTHON_VERSION="python3"
                    fi
                else
                    log_warning "无法添加PPA，使用系统Python 3.6"
                    apt install -y python3 python3-venv python3-dev python3-pip
                    PYTHON_VERSION="python3"
                fi
                
            elif [ "$OS_VERSION" = "20.04" ]; then
                apt install -y python3.9 python3.9-venv python3.9-dev python3-pip
                PYTHON_VERSION="python3.9"
            elif [ "$OS_VERSION" = "22.04" ]; then
                apt install -y python3.10 python3.10-venv python3.10-dev python3-pip
                PYTHON_VERSION="python3.10"
            else
                apt install -y python3 python3-venv python3-dev python3-pip
                PYTHON_VERSION="python3"
            fi
            ;;
        "debian")
            apt install -y python3 python3-venv python3-dev python3-pip
            PYTHON_VERSION="python3"
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                dnf install -y python39 python39-devel python39-pip
                PYTHON_VERSION="python3.9"
            else
                yum install -y python39 python39-devel python39-pip
                PYTHON_VERSION="python3.9"
            fi
            ;;
    esac

    # 快速修复软链接
    rm -f /usr/bin/python3 /usr/bin/pip3
    ln -sf $(which $PYTHON_VERSION || which python3.9 || which python3.10 || which python3.6 || which python3) /usr/bin/python3
    ln -sf /usr/bin/python3 /usr/bin/pip3
    
    PYTHON_INSTALLED=true
    log_success "Python安装完成: $(python3 --version 2>&1)"
}

# 智能安装Node.js
smart_install_nodejs() {
    if [ "$NODE_INSTALLED" = true ] && command -v npm &> /dev/null; then
        log_info "Node.js和npm已安装，跳过安装步骤"
        return 0
    fi
    
    log_info "开始安装Node.js..."
    
    # 如果Node.js已安装但npm有问题，先删除
    if command -v node &> /dev/null || command -v nodejs &> /dev/null; then
        log_warning "检测到旧版本Node.js，正在删除..."
        apt remove -y nodejs nodejs-doc npm 2>/dev/null || true
        apt autoremove -y
    fi
    
    case $OS in
        "ubuntu"|"debian")
            log_info "安装Node.js 18+..."
            curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
            apt install -y nodejs
            
            # 验证安装
            if command -v node &> /dev/null && command -v npm &> /dev/null; then
                NODE_INSTALLED=true
                log_success "Node.js安装完成: $(node --version 2>&1)"
                log_success "npm安装完成: $(npm --version 2>&1)"
            else
                log_error "Node.js安装失败"
                exit 1
            fi
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
            if command -v dnf &> /dev/null; then
                dnf install -y nodejs
            else
                yum install -y nodejs
            fi
            
            # 验证安装
            if command -v node &> /dev/null && command -v npm &> /dev/null; then
                NODE_INSTALLED=true
                log_success "Node.js安装完成: $(node --version 2>&1)"
                log_success "npm安装完成: $(npm --version 2>&1)"
            else
                log_error "Node.js安装失败"
                exit 1
            fi
            ;;
    esac
}

# 智能安装数据库
smart_install_database() {
    if [ "$MYSQL_INSTALLED" = true ]; then
        log_info "MySQL已安装，跳过安装步骤"
        DB_TYPE="mysql"
        return 0
    fi
    
    log_info "选择数据库类型..."
    
    # 自动选择MySQL（因为你的环境已经有MySQL）
    DB_TYPE="mysql"
    log_info "自动选择MySQL（检测到已有数据库环境)"
    
    # 如果MySQL未安装，快速安装
    if ! systemctl is-active --quiet mysql 2>/dev/null && ! systemctl is-active --quiet mysqld 2>/dev/null; then
        log_info "快速安装MySQL..."
        case $OS in
            "ubuntu"|"debian")
                apt install -y mysql-server
                systemctl start mysql
                systemctl enable mysql
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
        MYSQL_INSTALLED=true
    fi
    
    log_success "数据库配置完成"
}

# 智能安装Nginx
smart_install_nginx() {
    if [ "$NGINX_INSTALLED" = true ]; then
        log_info "Nginx已安装，跳过安装步骤"
        return 0
    fi
    
    log_info "开始安装Nginx..."
    
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

    NGINX_INSTALLED=true
    log_success "Nginx安装完成"
}

# 智能安装项目依赖
smart_install_dependencies() {
    if [ "$DEPS_INSTALLED" = true ]; then
        log_info "项目依赖已安装，跳过安装步骤"
        return 0
    fi
    
    log_info "开始安装项目依赖..."
    
    # 检查项目文件
    if [ ! -f "backend/main.py" ]; then
        log_error "未找到项目文件，请确保在正确的目录中运行脚本"
        exit 1
    fi
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
        VENV_INSTALLED=true
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 快速升级pip
    log_info "升级pip..."
    python3 -m pip install --upgrade pip --quiet
    
    # 检测Python版本并安装兼容的依赖
    PYTHON_MAJOR=$(python3 --version 2>&1 | grep -oE '[0-9]+' | head -1)
    PYTHON_MINOR=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1 | cut -d. -f2)
    
    log_info "检测到Python版本: $PYTHON_MAJOR.$PYTHON_MINOR"
    
    # 根据Python版本安装兼容的依赖
    if [ "$PYTHON_MAJOR" = "3" ] && [ "$PYTHON_MINOR" -lt "8" ]; then
        log_info "Python 3.6/3.7兼容模式，安装兼容版本..."
        
        # 创建兼容的requirements文件
        cat > backend/requirements_compatible.txt << 'EOF'
# Python 3.6/3.7 兼容版本
fastapi>=0.68.0,<0.100.0
uvicorn>=0.15.0,<0.20.0
sqlalchemy>=1.4.0,<2.0.0
pymysql>=1.0.0
python-multipart>=0.0.5
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-dotenv>=0.19.0
email-validator>=1.1.3
jinja2>=2.11.0
aiofiles>=0.7.0
EOF
        
        log_info "使用兼容的requirements文件安装依赖..."
        python3 -m pip install -r backend/requirements_compatible.txt --quiet
        
    else
        log_info "使用标准requirements文件安装依赖..."
        if [ -f "backend/requirements_vps.txt" ]; then
            python3 -m pip install -r backend/requirements_vps.txt --quiet
        else
            log_info "安装基础依赖..."
            python3 -m pip install fastapi uvicorn sqlalchemy pymysql python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv email-validator
        fi
    fi
    
    DEPS_INSTALLED=true
    log_success "项目依赖安装完成"
}

# 智能构建前端
smart_build_frontend() {
    if [ "$FRONTEND_BUILT" = true ]; then
        log_info "前端已构建，跳过构建步骤"
        return 0
    fi
    
    log_info "开始构建前端..."
    
    # 验证npm是否可用
    if ! command -v npm &> /dev/null; then
        log_error "npm命令不可用，请先安装Node.js"
        exit 1
    fi
    
    # 检查前端目录
    if [ ! -d "frontend" ]; then
        log_error "前端目录不存在，跳过前端构建"
        return 0
    fi
    
    cd frontend
    
    # 快速安装依赖
    if [ ! -d "node_modules" ]; then
        log_info "安装前端依赖..."
        if npm install --silent; then
            log_success "前端依赖安装成功"
        else
            log_warning "前端依赖安装失败，尝试使用--legacy-peer-deps..."
            npm install --legacy-peer-deps --silent || {
                log_error "前端依赖安装失败，跳过前端构建"
                cd ..
                return 0
            }
        fi
    else
        log_info "前端依赖已存在，跳过安装"
    fi
    
    # 检查package.json中的构建脚本
    if [ -f "package.json" ] && grep -q '"build"' package.json; then
        log_info "构建前端..."
        if npm run build --silent; then
            FRONTEND_BUILT=true
            log_success "前端构建完成"
        else
            log_warning "前端构建失败，可能需要手动构建"
        fi
    else
        log_warning "package.json中未找到build脚本，跳过构建"
    fi
    
    cd ..
}

# 快速配置项目
quick_configure_project() {
    log_info "快速配置项目..."
    
    # 自动设置域名
    if [ -z "$DOMAIN" ]; then
        DOMAIN=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
        log_info "自动检测域名: $DOMAIN"
    fi
    
    # 自动设置管理员信息（如果未设置）
    if [ -z "$ADMIN_EMAIL" ]; then
        ADMIN_EMAIL="admin@$DOMAIN"
        log_info "自动设置管理员邮箱: $ADMIN_EMAIL"
    fi
    
    if [ -z "$ADMIN_PASSWORD" ]; then
        ADMIN_PASSWORD="admin123456"
        log_info "自动设置管理员密码: $ADMIN_PASSWORD"
    fi
    
    # 快速配置环境变量
    if [ -f "env.example" ] && [ ! -f ".env" ]; then
        cp env.example .env
        log_info "已复制环境配置文件模板"
        
        # 自动更新数据库连接
        if [ -f ".env" ]; then
            sed -i "s|DATABASE_URL=.*|DATABASE_URL=mysql://dash_moneyfly_to:BHDW81bQRjNAa41s@localhost/dash_moneyfly_to|g" .env
            sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=[\"http://$DOMAIN\",\"https://$DOMAIN\"]|g" .env
            log_info "已自动配置数据库连接和CORS设置"
        fi
    fi
    
    log_success "项目快速配置完成"
}

# 快速初始化数据库
quick_init_database() {
    log_info "快速初始化数据库..."
    
    cd backend
    source ../venv/bin/activate
    
    # 尝试初始化数据库
    if python -c "from app.core.database import init_database; init_database()" 2>/dev/null; then
        log_success "数据库初始化成功"
    else
        log_warning "数据库初始化失败，可能需要手动配置"
    fi
    
    cd ..
}

# 快速启动服务
quick_start_service() {
    log_info "快速启动服务..."
    
    # 创建启动脚本
    cat > start_backend.sh << 'EOF'
#!/bin/bash
cd /www/wwwroot/dash.moneyfly.top/backend
source ../venv/bin/activate
python main.py
EOF
    
    chmod +x start_backend.sh
    
    # 创建系统服务
    cat > /etc/systemd/system/xboard.service << EOF
[Unit]
Description=XBoard Backend Service
After=network.target mysql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$(pwd)/backend
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable xboard
    
    log_success "服务配置完成，可以使用以下命令启动："
    log_info "启动服务: systemctl start xboard"
    log_info "查看状态: systemctl status xboard"
    log_info "查看日志: journalctl -u xboard -f"
}

# 快速测试所有组件
quick_test_components() {
    log_info "快速测试所有组件..."
    
    echo ""
    echo "🧪 组件测试结果:"
    
    # 测试Python
    if command -v python3 &> /dev/null; then
        PYTHON_VER=$(python3 --version 2>&1)
        echo "   Python: ✅ $PYTHON_VER"
    else
        echo "   Python: ❌ 未安装"
    fi
    
    # 测试Node.js
    if command -v node &> /dev/null; then
        NODE_VER=$(node --version 2>&1)
        echo "   Node.js: ✅ $NODE_VER"
    else
        echo "   Node.js: ❌ 未安装"
    fi
    
    # 测试npm
    if command -v npm &> /dev/null; then
        NPM_VER=$(npm --version 2>&1)
        echo "   npm: ✅ $NPM_VER"
    else
        echo "   npm: ❌ 未安装"
    fi
    
    # 测试MySQL
    if systemctl is-active --quiet mysql 2>/dev/null || systemctl is-active --quiet mysqld 2>/dev/null; then
        echo "   MySQL: ✅ 服务运行中"
    else
        echo "   MySQL: ❌ 服务未运行"
    fi
    
    # 测试Nginx
    if command -v nginx &> /dev/null; then
        NGINX_VER=$(nginx -v 2>&1)
        echo "   Nginx: ✅ $NGINX_VER"
    else
        echo "   Nginx: ❌ 未安装"
    fi
    
    # 测试虚拟环境
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        echo "   虚拟环境: ✅ 已创建"
    else
        echo "   虚拟环境: ❌ 未创建"
    fi
    
    # 测试项目依赖
    if [ -d "venv" ] && [ -f "venv/bin/pip" ]; then
        source venv/bin/activate
        if pip list | grep -q "fastapi"; then
            echo "   项目依赖: ✅ 已安装"
        else
            echo "   项目依赖: ❌ 未安装"
        fi
        deactivate
    else
        echo "   项目依赖: ❌ 未安装"
    fi
    
    # 测试前端构建
    if [ -d "frontend/dist" ] && [ -f "frontend/dist/index.html" ]; then
        echo "   前端构建: ✅ 已构建"
    else
        echo "   前端构建: ❌ 未构建"
    fi
    
    echo ""
}

# 创建兼容的requirements文件
create_compatible_requirements() {
    log_info "创建兼容的requirements文件..."
    
    # 获取Python版本号
    PYTHON_MAJOR=$(python3 --version 2>&1 | grep -oE '[0-9]+' | head -1)
    PYTHON_MINOR=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1 | cut -d. -f2)
    
    log_info "检测到Python版本: $PYTHON_MAJOR.$PYTHON_MINOR"
    
    # 根据Python版本创建兼容的requirements
    if [ "$PYTHON_MAJOR" = "3" ] && [ "$PYTHON_MINOR" -lt "8" ]; then
        log_info "创建Python 3.6/3.7兼容的requirements文件..."
        
        mkdir -p backend
        cat > backend/requirements_compatible.txt << 'EOF'
# Python 3.6/3.7 兼容版本
fastapi>=0.68.0,<0.100.0
uvicorn>=0.15.0,<0.20.0
sqlalchemy>=1.4.0,<2.0.0
pymysql>=1.0.0
python-multipart>=0.0.5
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-dotenv>=0.19.0
email-validator>=1.1.3
jinja2>=2.11.0
aiofiles>=0.7.0
EOF
        
        log_success "已创建兼容的requirements文件: backend/requirements_compatible.txt"
        COMPATIBLE_REQUIREMENTS="requirements_compatible.txt"
    else
        log_info "使用标准requirements文件"
        COMPATIBLE_REQUIREMENTS="requirements_vps.txt"
    fi
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
    
    # 升级pip - 使用python3 -m pip避免pip3问题
    log_info "升级pip..."
    python3 -m pip install --upgrade pip
    
    # 安装依赖 - 智能选择安装方式
    if [ -f "backend/$COMPATIBLE_REQUIREMENTS" ]; then
        log_info "使用兼容的requirements文件: $COMPATIBLE_REQUIREMENTS"
        python3 -m pip install -r "backend/$COMPATIBLE_REQUIREMENTS"
    elif [ -f "backend/requirements_vps.txt" ]; then
        log_info "使用标准requirements文件: requirements_vps.txt"
        python3 -m pip install -r backend/requirements_vps.txt
    else
        log_warning "未找到requirements文件，安装基础依赖..."
        python3 -m pip install fastapi uvicorn sqlalchemy pymysql python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv email-validator
    fi
    
    log_success "项目依赖安装完成"
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

# 安装和配置数据库
install_database() {
    log_info "选择数据库类型..."

    echo "请选择数据库类型:"
    echo "1) SQLite (推荐 - 无需额外配置)"
    echo "2) MySQL/MariaDB"
    echo "3) PostgreSQL"

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
            ;;
    esac

    log_success "MySQL安装完成"
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

    log_success "PostgreSQL安装完成"
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

    log_success "Nginx安装完成"
}

# 配置项目
configure_project() {
    log_info "配置项目..."

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

    # 配置环境变量
    if [ -f "env.example" ]; then
        cp env.example .env
        log_info "已复制环境配置文件模板"
    fi

    log_success "项目配置完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."

    cd backend
    source ../venv/bin/activate

    # 尝试初始化数据库
    if python -c "from app.core.database import init_database; init_database()" 2>/dev/null; then
        log_success "数据库初始化成功"
    else
        log_warning "数据库初始化失败，可能需要手动配置"
    fi

    cd ..
}

# 构建前端
build_frontend() {
    log_info "构建前端..."

    cd frontend
    
    # 安装依赖
    npm install
    
    # 构建生产版本
    npm run build
    
    cd ..
    
    log_success "前端构建完成"
}

# 创建系统服务
create_systemd_service() {
    log_info "创建系统服务..."

    cat > /etc/systemd/system/xboard.service << EOF
[Unit]
Description=XBoard Backend Service
After=network.target mysql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$(pwd)/backend
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载systemd
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable xboard
    
    log_success "系统服务创建完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."

    case $OS in
        "ubuntu"|"debian")
            ufw allow 22
            ufw allow 80
            ufw allow 443
            ufw allow 8000
            ufw --force enable
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                dnf install -y firewalld
                systemctl start firewalld
                systemctl enable firewalld
                firewall-cmd --permanent --add-port=22/tcp
                firewall-cmd --permanent --add-port=80/tcp
                firewall-cmd --permanent --add-port=443/tcp
                firewall-cmd --permanent --add-port=8000/tcp
                firewall-cmd --reload
            else
                yum install -y firewalld
                systemctl start firewalld
                systemctl enable firewalld
                firewall-cmd --permanent --add-port=22/tcp
                firewall-cmd --permanent --add-port=80/tcp
                firewall-cmd --permanent --add-port=443/tcp
                firewall-cmd --permanent --add-port=8000/tcp
                firewall-cmd --reload
            fi
            ;;
    esac

    log_success "防火墙配置完成"
}

# 显示安装完成信息
show_completion_info() {
    echo ""
    echo "=========================================="
    echo "🎉 XBoard Modern 安装完成！"
    echo "=========================================="
    echo ""
    echo "📋 安装信息:"
    echo "   域名: $DOMAIN"
    echo "   管理员邮箱: $ADMIN_EMAIL"
    echo "   数据库类型: $DB_TYPE"
    echo "   Python版本: $PYTHON_VERSION"
    echo ""
    echo "🚀 启动服务:"
    echo "   systemctl start xboard"
    echo "   systemctl status xboard"
    echo ""
    echo "🌐 访问地址:"
    echo "   前端: http://$DOMAIN"
    echo "   API: http://$DOMAIN:8000"
    echo "   健康检查: http://$DOMAIN:8000/health"
    echo ""
    echo "📚 管理命令:"
    echo "   查看日志: journalctl -u xboard -f"
    echo "   重启服务: systemctl restart xboard"
    echo "   停止服务: systemctl stop xboard"
    echo ""
}

# 主安装流程
main() {
    echo "=========================================="
    echo "🚀 XBoard Modern VPS 智能安装脚本 (Ubuntu 18.04 快速版)"
    echo "=========================================="
    echo ""

    # 解析命令行参数
    parse_arguments "$@"

    # 显示安装模式
    if [ "$INSTALL_MODE" = "auto" ]; then
        log_info "安装模式: 自动模式 (智能检测并跳过已安装组件)"
    else
        log_info "安装模式: 手动模式 (手动选择安装组件)"
    fi

    # 检查是否为root
    check_root

    # 检测VPS信息
    detect_vps_info

    # 检测已安装的组件
    detect_installed_components

    # 显示检测结果摘要
    echo ""
    echo "📋 环境检测结果:"
    echo "   Python: $([ "$PYTHON_INSTALLED" = true ] && echo "✅ 已安装" || echo "❌ 需要安装")"
    echo "   Node.js: $([ "$NODE_INSTALLED" = true ] && echo "✅ 已安装" || echo "❌ 需要安装")"
    echo "   MySQL: $([ "$MYSQL_INSTALLED" = true ] && echo "✅ 已安装" || echo "❌ 需要安装")"
    echo "   Nginx: $([ "$NGINX_INSTALLED" = true ] && echo "✅ 已安装" || echo "❌ 需要安装")"
    echo "   虚拟环境: $([ "$VENV_INSTALLED" = true ] && echo "✅ 已创建" || echo "❌ 需要创建")"
    echo "   项目依赖: $([ "$DEPS_INSTALLED" = true ] && echo "✅ 已安装" || echo "❌ 需要安装")"
    echo "   前端构建: $([ "$FRONTEND_BUILT" = true ] && echo "✅ 已构建" || echo "❌ 需要构建")"
    echo ""

    # 快速修复常见问题
    quick_fix_common_issues

    # 智能安装基础软件（跳过已安装的）
    smart_install_python
    smart_install_nodejs

    # 智能安装数据库（跳过已安装的）
    smart_install_database

    # 智能安装Nginx（跳过已安装的）
    smart_install_nginx

    # 快速配置项目
    quick_configure_project

    # 智能安装项目依赖（跳过已安装的）
    smart_install_dependencies

    # 快速初始化数据库
    quick_init_database

    # 智能构建前端（跳过已构建的）
    smart_build_frontend

    # 快速启动服务
    quick_start_service

    # 快速测试所有组件
    quick_test_components

    # 显示完成信息
    show_completion_info
}

# 运行主函数
main "$@"
