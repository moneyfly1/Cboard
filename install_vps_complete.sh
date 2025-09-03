#!/bin/bash

# ================================
# XBoard VPS 完整安装脚本
# 自动检测环境并安装所有必需组件
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

# 全局变量
PROJECT_ROOT=""
PYTHON_VERSION=""
PYTHON_CMD=""
NODE_VERSION=""
NGINX_VERSION=""
MYSQL_VERSION=""
PHP_VERSION=""
OS=""
OS_VERSION=""
ARCH=""

echo "=========================================="
echo "🚀 XBoard VPS 完整安装脚本"
echo "=========================================="
echo ""

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    log_error "请使用root用户运行此脚本"
    exit 1
fi

# 检测系统信息
detect_system_info() {
    log_info "检测系统信息..."
    
    # 检测操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$(echo $ID | tr '[:upper:]' '[:lower:]')
        OS_VERSION=$(echo $VERSION_ID | cut -d. -f1,2)
    elif [ -f /etc/redhat-release ]; then
        OS=$(cat /etc/redhat-release | tr '[:upper:]' '[:lower:]' | grep -oE '(centos|rhel|almalinux|rocky)')
        OS_VERSION=$(cat /etc/redhat-release | grep -oE '[0-9]+\.[0-9]+')
    else
        OS="unknown"
        OS_VERSION="unknown"
    fi
    
    # 检测架构
    ARCH=$(uname -m)
    
    log_success "系统信息: $OS $OS_VERSION ($ARCH)"
    
    # 检测Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        PYTHON_CMD="python3"
        PYTHON_INSTALLED=true
        log_success "检测到Python: $PYTHON_VERSION"
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        PYTHON_CMD="python"
        PYTHON_INSTALLED=true
        log_success "检测到Python: $PYTHON_VERSION"
    else
        PYTHON_INSTALLED=false
        log_warning "未检测到Python"
    fi
    
    # 检测Node.js版本
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version 2>&1 | grep -oE 'v[0-9]+' | head -1)
        NODE_MAJOR_VERSION=$(echo $NODE_VERSION | grep -oE '[0-9]+' | head -1)
        if [ -n "$NODE_MAJOR_VERSION" ] && [ "$NODE_MAJOR_VERSION" -ge 16 ]; then
            NODE_INSTALLED=true
            log_success "检测到Node.js: $NODE_VERSION (满足要求)"
        else
            NODE_INSTALLED=false
            log_warning "检测到Node.js: $NODE_VERSION (版本过低，需要升级)"
        fi
    else
        NODE_INSTALLED=false
        log_warning "未检测到Node.js"
    fi
    
    # 检测Nginx版本
    if command -v nginx &> /dev/null; then
        NGINX_VERSION=$(nginx -v 2>&1 | grep -oE 'nginx/[0-9]+\.[0-9]+\.[0-9]+' | cut -d'/' -f2)
        NGINX_INSTALLED=true
        log_success "检测到Nginx: $NGINX_VERSION"
    else
        NGINX_INSTALLED=false
        log_warning "未检测到Nginx"
    fi
    
    # 检测MySQL版本
    if command -v mysql &> /dev/null; then
        MYSQL_VERSION=$(mysql --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        MYSQL_INSTALLED=true
        log_success "检测到MySQL: $MYSQL_VERSION"
    else
        MYSQL_INSTALLED=false
        log_warning "未检测到MySQL"
    fi
    
    # 检测PHP版本
    if command -v php &> /dev/null; then
        PHP_VERSION=$(php --version | grep -oE 'PHP [0-9]+\.[0-9]+\.[0-9]+' | cut -d' ' -f2)
        PHP_INSTALLED=true
        log_success "检测到PHP: $PHP_VERSION"
    else
        PHP_INSTALLED=false
        log_warning "未检测到PHP"
    fi
    
    # 检测系统更新状态
    check_system_updates
}

# 检测系统更新
check_system_updates() {
    log_info "检测系统更新..."
    
    case $OS in
        "ubuntu"|"debian")
            # 检查是否有可用更新
            apt update &>/dev/null
            UPDATES_AVAILABLE=$(apt list --upgradable 2>/dev/null | grep -c upgradable || echo "0")
            if [ "$UPDATES_AVAILABLE" -gt 0 ]; then
                log_warning "检测到 $UPDATES_AVAILABLE 个可用更新"
                SYSTEM_NEEDS_UPDATE=true
            else
                log_success "系统已是最新版本，无需更新"
                SYSTEM_NEEDS_UPDATE=false
            fi
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                UPDATES_AVAILABLE=$(dnf check-update --quiet | wc -l)
            else
                UPDATES_AVAILABLE=$(yum check-update --quiet | wc -l)
            fi
            
            if [ "$UPDATES_AVAILABLE" -gt 0 ]; then
                log_warning "检测到 $UPDATES_AVAILABLE 个可用更新"
                SYSTEM_NEEDS_UPDATE=true
            else
                log_success "系统已是最新版本，无需更新"
                SYSTEM_NEEDS_UPDATE=false
            fi
            ;;
    esac
}

# 系统更新
update_system() {
    # 检查是否需要更新
    if [ "$SYSTEM_NEEDS_UPDATE" = true ]; then
        log_info "开始系统更新..."
        
        case $OS in
            "ubuntu"|"debian")
                apt update && apt upgrade -y
                ;;
            "centos"|"rhel"|"almalinux"|"rocky")
                if command -v dnf &> /dev/null; then
                    dnf update -y
                else
                    yum update -y
                fi
                ;;
        esac
        
        log_success "系统更新完成"
    else
        log_info "系统无需更新，跳过更新步骤"
    fi
}

# 安装Python
install_python() {
    # 检查是否已安装
    if [ "$PYTHON_INSTALLED" = true ]; then
        log_info "Python已安装: $PYTHON_VERSION，跳过安装"
        return 0
    fi
    
    log_info "安装Python环境..."
    
    case $OS in
        "ubuntu")
            if [ "$OS_VERSION" = "18.04" ]; then
                # Ubuntu 18.04 默认有Python 3.6
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
            elif [ "$OS_VERSION" = "24.04" ]; then
                # Ubuntu 24.04 默认有Python 3.12
                apt install -y python3.12-venv python3.12-dev python3-pip
                PYTHON_CMD="python3.12"
            else
                # 其他版本安装Python 3.8
                apt install -y python3.8 python3.8-venv python3.8-dev python3-pip
                PYTHON_CMD="python3.8"
            fi
            ;;
        "debian")
            apt install -y python3-venv python3-dev python3-pip
            PYTHON_CMD="python3"
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                dnf install -y python3 python3-devel python3-pip python3-virtualenv
                PYTHON_CMD="python3"
            else
                yum install -y python3 python3-devel python3-pip python3-virtualenv
                PYTHON_CMD="python3"
            fi
            ;;
    esac
    
    # 验证安装
    if [ -n "$PYTHON_CMD" ] && command -v "$PYTHON_CMD" &> /dev/null; then
        PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        PYTHON_INSTALLED=true
        log_success "Python安装完成: $PYTHON_VERSION"
    else
        log_error "Python安装失败"
        exit 1
    fi
}

# 安装Node.js
install_nodejs() {
    # 检查是否已安装
    if [ "$NODE_INSTALLED" = true ]; then
        log_info "Node.js已安装: $NODE_VERSION，跳过安装"
        return 0
    fi
    
    log_info "安装Node.js环境..."
    
    # 安装Node.js
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
    
    # 验证安装
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version 2>&1 | grep -oE 'v[0-9]+' | head -1)
        NODE_MAJOR_VERSION=$(echo $NODE_VERSION | grep -oE '[0-9]+' | head -1)
        if [ -n "$NODE_MAJOR_VERSION" ] && [ "$NODE_MAJOR_VERSION" -ge 16 ]; then
            NODE_INSTALLED=true
            log_success "Node.js安装完成: $NODE_VERSION"
        else
            log_error "Node.js版本过低，安装失败"
            exit 1
        fi
    else
        log_error "Node.js安装失败"
        exit 1
    fi
}

# 安装Nginx
install_nginx() {
    # 检查是否已安装
    if [ "$NGINX_INSTALLED" = true ]; then
        log_info "Nginx已安装: $NGINX_VERSION，跳过安装"
        return 0
    fi
    
    log_info "安装Nginx..."
    
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
    
    # 启动并启用Nginx
    systemctl start nginx
    systemctl enable nginx
    
    # 验证安装
    if command -v nginx &> /dev/null; then
        NGINX_VERSION=$(nginx -v 2>&1 | grep -oE 'nginx/[0-9]+\.[0-9]+\.[0-9]+' | cut -d'/' -f2)
        NGINX_INSTALLED=true
        log_success "Nginx安装完成: $NGINX_VERSION"
    else
        log_error "Nginx安装失败"
        exit 1
    fi
}

# 安装MySQL
install_mysql() {
    # 检查是否已安装
    if [ "$MYSQL_INSTALLED" = true ]; then
        log_info "MySQL已安装: $MYSQL_VERSION，跳过安装"
        # 确保安装MySQL开发库
        case $OS in
            "ubuntu"|"debian")
                apt install -y libmysqlclient-dev pkg-config
                ;;
            "centos"|"rhel"|"almalinux"|"rocky")
                if command -v dnf &> /dev/null; then
                    dnf install -y mysql-devel pkgconfig
                else
                    yum install -y mysql-devel pkgconfig
                fi
                ;;
        esac
        return 0
    fi
    
    case $OS in
        "ubuntu")
            if [ "$OS_VERSION" = "18.04" ] || [ "$OS_VERSION" = "20.04" ]; then
                # 安装MySQL 5.7
                apt install -y mysql-server mysql-client libmysqlclient-dev pkg-config
            else
                # 安装MySQL 8.0
                apt install -y mysql-server mysql-client libmysqlclient-dev pkg-config
            fi
            ;;
        "debian")
            apt install -y mysql-server mysql-client libmysqlclient-dev pkg-config
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                dnf install -y mysql-server mysql mysql-devel pkgconfig
            else
                yum install -y mysql-server mysql mysql-devel pkgconfig
            fi
            ;;
    esac
    
    # 启动并启用MySQL
    systemctl start mysql
    systemctl enable mysql
    
    # 验证安装
    if command -v mysql &> /dev/null; then
        MYSQL_VERSION=$(mysql --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        log_success "MySQL安装完成: $MYSQL_VERSION"
    else
        log_error "MySQL安装失败"
        exit 1
    fi
}

# 安装PHP
install_php() {
    # 检查是否已安装
    if [ "$PHP_INSTALLED" = true ]; then
        log_info "PHP已安装: $PHP_VERSION，跳过安装"
        return 0
    fi
    
    case $OS in
        "ubuntu")
            if [ "$OS_VERSION" = "18.04" ]; then
                apt install -y php7.4-fpm php7.4-mysql php7.4-common php7.4-mbstring php7.4-xml php7.4-curl
            elif [ "$OS_VERSION" = "20.04" ]; then
                apt install -y php7.4-fpm php7.4-mysql php7.4-common php7.4-mbstring php7.4-xml php7.4-curl
            elif [ "$OS_VERSION" = "22.04" ]; then
                apt install -y php8.1-fpm php8.1-mysql php8.1-common php8.1-mbstring php8.1-xml php8.1-curl
            elif [ "$OS_VERSION" = "24.04" ]; then
                apt install -y php8.2-fpm php8.2-mysql php8.2-common php8.2-mbstring php8.2-xml php8.2-curl
            else
                apt install -y php8.1-fpm php8.1-mysql php8.1-common php8.1-mbstring php8.1-xml php8.1-curl
            fi
            ;;
        "debian")
            apt install -y php8.1-fpm php8.1-mysql php8.1-common php8.1-mbstring php8.1-xml php8.1-curl
            ;;
        "centos"|"rhel"|"almalinux"|"rocky")
            if command -v dnf &> /dev/null; then
                dnf install -y php-fpm php-mysqlnd php-common php-mbstring php-xml php-curl
            else
                yum install -y php-fpm php-mysqlnd php-common php-mbstring php-xml php-curl
            fi
            ;;
    esac
    
    # 启动并启用PHP-FPM
    systemctl start php*-fpm
    systemctl enable php*-fpm
    
    # 验证安装
    if command -v php &> /dev/null; then
        PHP_VERSION=$(php --version | grep -oE 'PHP [0-9]+\.[0-9]+\.[0-9]+' | cut -d' ' -f2)
        log_success "PHP安装完成: $PHP_VERSION"
    else
        log_error "PHP安装失败"
        exit 1
    fi
}

# 检测项目路径
detect_project_path() {
    log_info "检测项目路径..."
    
    # 策略1: 检查当前目录
    if [ -d "backend" ] && [ -d "frontend" ]; then
        PROJECT_ROOT="$(pwd)"
        log_success "检测到当前目录为项目根目录: $PROJECT_ROOT"
        return 0
    fi
    
    # 策略2: 检查脚本所在目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -d "$SCRIPT_DIR/backend" ] && [ -d "$SCRIPT_DIR/frontend" ]; then
        PROJECT_ROOT="$SCRIPT_DIR"
        log_success "检测到脚本目录为项目根目录: $PROJECT_ROOT"
        return 0
    fi
    
    # 策略3: 检查上级目录
    PARENT_DIR="$(dirname "$(pwd)")"
    if [ -d "$PARENT_DIR/backend" ] && [ -d "$PARENT_DIR/frontend" ]; then
        PROJECT_ROOT="$PARENT_DIR"
        log_success "检测到上级目录为项目根目录: $PROJECT_ROOT"
        return 0
    fi
    
    # 策略4: 递归向上查找
    CURRENT_DIR="$(pwd)"
    while [ "$CURRENT_DIR" != "/" ]; do
        if [ -d "$CURRENT_DIR/backend" ] && [ -d "$CURRENT_DIR/frontend" ]; then
            PROJECT_ROOT="$CURRENT_DIR"
            log_success "递归查找到项目根目录: $PROJECT_ROOT"
            return 0
        fi
        CURRENT_DIR="$(dirname "$CURRENT_DIR")"
    done
    
    # 策略5: 检查常见路径
    COMMON_PATHS=("/www/wwwroot" "/var/www" "/home/www" "/root/xboard")
    for path in "${COMMON_PATHS[@]}"; do
        if [ -d "$path" ]; then
            for subdir in "$path"/*; do
                if [ -d "$subdir" ] && [ -d "$subdir/backend" ] && [ -d "$subdir/frontend" ]; then
                    PROJECT_ROOT="$subdir"
                    log_success "在常见路径中找到项目: $PROJECT_ROOT"
                    return 0
                fi
            done
        fi
    done
    
    log_error "无法检测到项目路径，请确保在正确的目录中运行脚本"
    exit 1
}

# 设置Python环境
setup_python_environment() {
    log_info "设置Python环境..."
    
    cd "$PROJECT_ROOT"
    
    # 删除已存在的虚拟环境（如果有问题）
    if [ -d "venv" ]; then
        log_info "删除已存在的虚拟环境..."
        rm -rf venv
    fi
    
    # 尝试创建虚拟环境
    log_info "创建Python虚拟环境..."
    log_info "使用Python命令: $PYTHON_CMD"
    
    # 尝试不同的虚拟环境创建方法
    VENV_CREATED=false
    
    # 方法1: 使用python3 -m venv
    log_info "尝试方法1: $PYTHON_CMD -m venv venv"
    $PYTHON_CMD -m venv venv
    if [ $? -eq 0 ] && [ -f "venv/bin/activate" ]; then
        log_success "方法1成功: 虚拟环境创建完成"
        VENV_CREATED=true
    else
        log_warning "方法1失败，尝试其他方法..."
        rm -rf venv 2>/dev/null || true
    fi
    
    # 方法2: 如果方法1失败，尝试使用python3.12 -m venv
    if [ "$VENV_CREATED" = false ] && command -v python3.12 &> /dev/null; then
        log_info "尝试方法2: python3.12 -m venv venv"
        python3.12 -m venv venv
        if [ $? -eq 0 ] && [ -f "venv/bin/activate" ]; then
            log_success "方法2成功: 使用python3.12创建虚拟环境"
            VENV_CREATED=true
        else
            log_warning "方法2失败..."
            rm -rf venv 2>/dev/null || true
        fi
    fi
    
    # 方法3: 如果方法2失败，尝试使用python3.11 -m venv
    if [ "$VENV_CREATED" = false ] && command -v python3.11 &> /dev/null; then
        log_info "尝试方法3: python3.11 -m venv venv"
        python3.11 -m venv venv
        if [ $? -eq 0 ] && [ -f "venv/bin/activate" ]; then
            log_success "方法3成功: 使用python3.11创建虚拟环境"
            VENV_CREATED=true
        else
            log_warning "方法3失败..."
            rm -rf venv 2>/dev/null || true
        fi
    fi
    
    # 方法4: 如果方法3失败，尝试使用python3.10 -m venv
    if [ "$VENV_CREATED" = false ] && command -v python3.10 &> /dev/null; then
        log_info "尝试方法4: python3.10 -m venv venv"
        python3.10 -m venv venv
        if [ $? -eq 0 ] && [ -f "venv/bin/activate" ]; then
            log_success "方法4成功: 使用python3.10创建虚拟环境"
            VENV_CREATED=true
        else
            log_warning "方法4失败..."
            rm -rf venv 2>/dev/null || true
        fi
    fi
    
    # 方法5: 如果方法4失败，尝试使用python3.9 -m venv
    if [ "$VENV_CREATED" = false ] && command -v python3.9 &> /dev/null; then
        log_info "尝试方法5: python3.9 -m venv venv"
        python3.9 -m venv venv
        if [ $? -eq 0 ] && [ -f "venv/bin/activate" ]; then
            log_success "方法5成功: 使用python3.9创建虚拟环境"
            VENV_CREATED=true
        else
            log_warning "方法5失败..."
            rm -rf venv 2>/dev/null || true
        fi
    fi
    
    # 方法6: 如果方法5失败，尝试使用python3.8 -m venv
    if [ "$VENV_CREATED" = false ] && command -v python3.8 &> /dev/null; then
        log_info "尝试方法6: python3.8 -m venv venv"
        python3.8 -m venv venv
        if [ $? -eq 0 ] && [ -f "venv/bin/activate" ]; then
            log_success "方法6成功: 使用python3.8创建虚拟环境"
            VENV_CREATED=true
        else
            log_warning "方法6失败..."
            rm -rf venv 2>/dev/null || true
        fi
    fi
    
    # 方法7: 如果方法6失败，尝试使用python3 -m venv
    if [ "$VENV_CREATED" = false ] && command -v python3 &> /dev/null; then
        log_info "尝试方法7: python3 -m venv venv"
        python3 -m venv venv
        if [ $? -eq 0 ] && [ -f "venv/bin/activate" ]; then
            log_success "方法7成功: 使用python3创建虚拟环境"
            VENV_CREATED=true
        else
            log_warning "方法7失败..."
            rm -rf venv 2>/dev/null || true
        fi
    fi
    
    # 检查最终结果
    if [ "$VENV_CREATED" = false ]; then
        log_error "所有虚拟环境创建方法都失败了"
        log_error "请检查Python安装和venv模块"
        log_info "尝试手动安装venv模块..."
        
        # 尝试安装venv模块
        case $OS in
            "ubuntu"|"debian")
                apt install -y python3-venv python3-virtualenv
                ;;
            "centos"|"rhel"|"almalinux"|"rocky")
                if command -v dnf &> /dev/null; then
                    dnf install -y python3-virtualenv
                else
                    yum install -y python3-virtualenv
                fi
                ;;
        esac
        
        # 再次尝试创建虚拟环境
        log_info "重新尝试创建虚拟环境..."
        $PYTHON_CMD -m venv venv
        if [ $? -eq 0 ] && [ -f "venv/bin/activate" ]; then
            log_success "重新尝试成功: 虚拟环境创建完成"
            VENV_CREATED=true
        else
            log_error "虚拟环境创建最终失败，请检查系统配置"
            exit 1
        fi
    fi
    
    # 显示虚拟环境信息
    log_info "虚拟环境创建成功，详细信息："
    ls -la venv/bin/
    log_info "Python版本: $($PYTHON_CMD --version)"
    
    # 激活虚拟环境
    log_info "激活虚拟环境..."
    source venv/bin/activate
    
    # 升级pip
    log_info "升级pip..."
    pip install --upgrade pip
    
    # 智能选择requirements文件
    if [ -f "backend/requirements_modern.txt" ]; then
        log_info "使用现代系统requirements文件"
        
        # 先安装基础依赖，避免mysqlclient编译问题
        log_info "先安装基础依赖..."
        pip install fastapi uvicorn sqlalchemy python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv email-validator pydantic pydantic-settings
        
        # 然后安装MySQL相关依赖
        log_info "安装MySQL相关依赖..."
        pip install mysqlclient pymysql
        
        # 最后安装其他依赖
        log_info "安装其他依赖..."
        pip install alembic redis httpx aiofiles python-multipart
        
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
        log_error "未找到package.json文件"
        exit 1
    fi
    
    # 安装依赖
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
    
    cd "$PROJECT_ROOT"
}

# 配置数据库
configure_database() {
    log_info "配置数据库..."
    
    # 询问用户是否跳过数据库配置
    if [ -t 0 ]; then
        echo ""
        echo "=========================================="
        echo "🗄️  数据库配置选项"
        echo "=========================================="
        echo "1) 自动配置数据库（需要MySQL root权限）"
        echo "2) 跳过数据库配置（稍后手动配置）"
        echo ""
        read -p "请选择 (1/2): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[2]$ ]]; then
            log_info "用户选择跳过数据库配置"
            log_info "请稍后在.env文件中手动配置数据库连接信息"
            return 0
        fi
    fi
    
    # 尝试不同的MySQL连接方式
    MYSQL_CMD=""
    
    # 方法1: 尝试无密码连接
    if mysql -u root -e "SELECT 1;" 2>/dev/null; then
        log_info "MySQL root用户无需密码"
        MYSQL_CMD="mysql -u root"
    # 方法2: 尝试使用sudo mysql
    elif sudo mysql -e "SELECT 1;" 2>/dev/null; then
        log_info "使用sudo mysql连接成功"
        MYSQL_CMD="sudo mysql"
    # 方法3: 尝试使用mysql -u root -p（交互式）
    else
        log_info "MySQL root用户需要密码，尝试配置..."
        
        # 检查是否在非交互式环境中
        if [ -t 0 ]; then
            # 交互式环境，询问用户
            log_warning "请手动配置数据库或提供root密码"
            echo ""
            echo "选项1: 手动执行SQL命令"
            echo "mysql -u root -p"
            echo "CREATE DATABASE IF NOT EXISTS xboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            echo "CREATE USER IF NOT EXISTS 'xboard'@'localhost' IDENTIFIED BY 'xboard123';"
            echo "GRANT ALL PRIVILEGES ON xboard.* TO 'xboard'@'localhost';"
            echo "FLUSH PRIVILEGES;"
            echo "EXIT;"
            echo ""
            
            read -p "是否继续安装？(y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "用户选择停止安装"
                exit 0
            fi
            
            log_warning "请确保在继续前手动创建数据库和用户"
            log_info "稍后可以在.env文件中修改数据库连接信息"
            return 0
        else
            # 非交互式环境，跳过数据库配置
            log_warning "非交互式环境，跳过数据库配置"
            log_info "请稍后在.env文件中手动配置数据库连接信息"
            return 0
        fi
    fi
    
    if [ -n "$MYSQL_CMD" ]; then
        # 检查数据库是否已存在
        if $MYSQL_CMD -e "USE xboard;" 2>/dev/null; then
            log_info "数据库 'xboard' 已存在"
        else
            log_info "创建数据库 'xboard'..."
            $MYSQL_CMD -e "CREATE DATABASE IF NOT EXISTS xboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        fi
        
        # 检查用户是否已存在
        if $MYSQL_CMD -e "SELECT User FROM mysql.user WHERE User='xboard';" 2>/dev/null | grep -q "xboard"; then
            log_info "用户 'xboard' 已存在"
        else
            log_info "创建用户 'xboard'..."
            $MYSQL_CMD -e "CREATE USER IF NOT EXISTS 'xboard'@'localhost' IDENTIFIED BY 'xboard123';"
            $MYSQL_CMD -e "GRANT ALL PRIVILEGES ON xboard.* TO 'xboard'@'localhost';"
            $MYSQL_CMD -e "FLUSH PRIVILEGES;"
        fi
        
        log_success "数据库配置完成"
    else
        log_warning "无法配置数据库，请稍后手动配置"
    fi
}

# 配置Nginx
configure_nginx() {
    log_info "配置Nginx..."
    
    # 询问用户是否跳过Nginx配置
    if [ -t 0 ]; then
        echo ""
        echo "=========================================="
        echo "🌐 Nginx配置选项"
        echo "=========================================="
        echo "1) 自动配置Nginx（需要Nginx已安装）"
        echo "2) 跳过Nginx配置（稍后手动配置）"
        echo ""
        read -p "请选择 (1/2): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[2]$ ]]; then
            log_info "用户选择跳过Nginx配置"
            log_info "请稍后手动配置Nginx反向代理"
            return 0
        fi
    fi
    
    # 检查Nginx是否安装
    if ! command -v nginx &> /dev/null; then
        log_error "Nginx未安装，无法配置"
        return 1
    fi
    
    # 创建Nginx配置目录
    mkdir -p /etc/nginx/sites-available
    mkdir -p /etc/nginx/sites-enabled
    
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
    
    # 测试配置
    nginx -t
    
    # 重启Nginx
    systemctl restart nginx
    
    log_success "Nginx配置完成"
}

# 创建环境变量文件
create_env_file() {
    log_info "创建环境变量文件..."
    
    cd "$PROJECT_ROOT"
    
    # 生成密钥
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    
    # 检测数据库配置
    DB_CONFIG=""
    if [ -n "$MYSQL_CMD" ]; then
        # 检查xboard用户是否存在
        if $MYSQL_CMD -e "SELECT User FROM mysql.user WHERE User='xboard';" 2>/dev/null | grep -q "xboard"; then
            DB_CONFIG="mysql+pymysql://xboard:xboard123@localhost:3306/xboard"
            log_info "使用xboard用户连接数据库"
        else
            DB_CONFIG="mysql+pymysql://root@localhost:3306/xboard"
            log_info "使用root用户连接数据库"
        fi
    else
        DB_CONFIG="mysql+pymysql://root@localhost:3306/xboard"
        log_info "使用默认root用户连接数据库"
        log_warning "请根据实际情况修改数据库连接信息"
    fi
    
    # 创建.env文件
    cat > .env << EOF
# ================================
# XBoard 环境变量配置
# ================================

# 数据库配置
# 请根据您的实际数据库配置修改以下信息
DATABASE_URL=$DB_CONFIG

# 如果您的数据库需要密码，请修改为：
# DATABASE_URL=mysql+pymysql://用户名:密码@localhost:3306/xboard

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

    log_success "环境变量文件创建完成"
    
    # 显示数据库配置信息
    echo ""
    echo "=========================================="
    echo "📊 数据库配置信息"
    echo "=========================================="
    echo "当前配置: $DB_CONFIG"
    echo ""
    echo "⚠️  重要提醒:"
    echo "1. 如果数据库需要密码，请修改 .env 文件中的 DATABASE_URL"
    echo "2. 格式: mysql+pymysql://用户名:密码@localhost:3306/xboard"
    echo "3. 例如: mysql+pymysql://root:your_password@localhost:3306/xboard"
    echo ""
}

# 创建systemd服务
create_systemd_service() {
    log_info "创建systemd服务..."
    
    cat > /etc/systemd/system/xboard.service << EOF
[Unit]
Description=XBoard Backend
After=network.target
Wants=mysql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_ROOT/backend
Environment=PATH=$PROJECT_ROOT/venv/bin
ExecStart=$PROJECT_ROOT/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
KillMode=mixed
TimeoutStopSec=30

# 确保服务在后台运行
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$PROJECT_ROOT/backend $PROJECT_ROOT/uploads

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载systemd
    systemctl daemon-reload
    systemctl enable xboard.service
    
    log_success "systemd服务创建完成"
}

# 部署项目文件
deploy_project() {
    log_info "部署项目文件..."
    
    # 创建网站目录
    mkdir -p /var/www/xboard
    mkdir -p /var/www/xboard/frontend
    mkdir -p /var/www/xboard/backend
    mkdir -p /var/www/xboard/uploads
    
    # 复制前端文件
    if [ -d "frontend/dist" ]; then
        cp -r frontend/dist/* /var/www/xboard/frontend/
    fi
    
    # 复制后端文件
    cp -r backend/* /var/www/xboard/backend/
    
    # 复制上传目录
    if [ -d "uploads" ]; then
        cp -r uploads/* /var/www/xboard/uploads/ 2>/dev/null || true
    fi
    
    # 复制环境变量文件
    cp .env /var/www/xboard/
    
    # 设置权限
    chown -R www-data:www-data /var/www/xboard
    chmod -R 755 /var/www/xboard
    
    log_success "项目文件部署完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 启动XBoard服务
    systemctl start xboard.service
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    if systemctl is-active --quiet xboard.service; then
        log_success "XBoard服务启动成功"
        
        # 显示服务状态
        log_info "服务状态:"
        systemctl status xboard.service --no-pager -l
        
        # 显示日志
        log_info "最近的服务日志:"
        journalctl -u xboard.service --no-pager -n 10
        
    else
        log_error "XBoard服务启动失败"
        log_info "服务状态:"
        systemctl status xboard.service --no-pager -l
        log_info "服务日志:"
        journalctl -u xboard.service --no-pager -n 20
        exit 1
    fi
    
    log_success "所有服务启动完成"
    
    # 显示服务管理命令
    echo ""
    echo "=========================================="
    echo "🔧 服务管理命令"
    echo "=========================================="
    echo "查看服务状态: systemctl status xboard"
    echo "启动服务: systemctl start xboard"
    echo "停止服务: systemctl stop xboard"
    echo "重启服务: systemctl restart xboard"
    echo "查看日志: journalctl -u xboard -f"
    echo "启用开机自启: systemctl enable xboard"
    echo "禁用开机自启: systemctl disable xboard"
    echo ""
}

# 显示完成信息
show_completion_info() {
    echo ""
    echo "=========================================="
    echo "🎉 XBoard 安装完成！"
    echo "=========================================="
    echo ""
    echo "📊 系统信息："
    echo "   操作系统: $OS $OS_VERSION ($ARCH)"
    echo "   Python: $PYTHON_VERSION"
    echo "   Node.js: $NODE_VERSION"
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
    echo "   重启Nginx: systemctl restart nginx"
    echo "   重启MySQL: systemctl restart mysql"
    echo ""
    echo "📁 项目位置: $PROJECT_ROOT"
    echo "🌐 网站目录: /var/www/xboard"
    echo ""
    echo "⚠️  重要提醒:"
    echo "   1. 请修改 .env 文件中的数据库密码和邮件配置"
    echo "   2. 建议配置SSL证书"
    echo "   3. 定期备份数据库"
    echo "   4. 默认管理员账号: admin@localhost / admin123"
    echo ""
}

# 主函数
main() {
    log_info "开始安装XBoard..."
    
    # 检测系统信息
    detect_system_info
    
    # 系统更新
    update_system
    
    # 安装必需组件
    install_python
    install_nodejs
    install_nginx
    install_mysql
    install_php
    
    # 检测项目路径
    detect_project_path
    
    # 设置Python环境
    setup_python_environment
    
    # 构建前端
    build_frontend
    
    # 配置数据库
    configure_database
    
    # 配置Nginx
    configure_nginx
    
    # 创建环境变量文件
    create_env_file
    
    # 创建systemd服务
    create_systemd_service
    
    # 部署项目文件
    deploy_project
    
    # 启动服务
    start_services
    
    # 显示完成信息
    show_completion_info
    
    log_success "XBoard安装完成！"
}

# 运行主函数
main "$@"
