#!/bin/bash

# ================================
# XBoard Modern 智能安装脚本
# 支持环境检查、自动配置和数据库连通性测试
# ================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 全局变量
PROJECT_NAME="XBoard Modern"
PROJECT_VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT=""

# 检查系统要求
check_system_requirements() {
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
    
    if [ $MEM -lt 2048 ]; then
        log_error "内存不足，需要至少2GB内存，当前: ${MEM}MB"
        exit 1
    fi
    
    # 检查磁盘空间
    if [[ "$OS" == "macOS" ]]; then
    DISK=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    else
        DISK=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    fi
    
    if [ $DISK -lt 20 ]; then
        log_error "磁盘空间不足，需要至少20GB，当前: ${DISK}GB"
        exit 1
    fi
    
    log_success "系统检查通过: $OS $VER, 内存: ${MEM}MB, 磁盘: ${DISK}GB"
}

# 检查环境是否已经安装
check_existing_installation() {
    log_info "检查现有安装..."
    
    # 检查虚拟环境
    if [ -d "venv" ]; then
        log_warning "检测到现有虚拟环境，跳过创建"
        EXISTING_VENV=true
    else
        EXISTING_VENV=false
    fi
    
    # 检查Python依赖
    if [ -d "venv" ] && [ -f "venv/pyvenv.cfg" ]; then
        log_info "检查Python依赖..."
        source venv/bin/activate
        if pip list | grep -q "fastapi"; then
            log_warning "检测到已安装的Python依赖，跳过安装"
            EXISTING_DEPS=true
        else
            EXISTING_DEPS=false
        fi
        deactivate
    else
        EXISTING_DEPS=false
    fi
    
    # 检查前端构建
    if [ -d "frontend/dist" ]; then
        log_warning "检测到已构建的前端，跳过构建"
        EXISTING_FRONTEND=true
    else
        EXISTING_FRONTEND=false
    fi
    
    # 检查环境配置文件
    if [ -f ".env" ]; then
        log_warning "检测到环境配置文件，跳过创建"
        EXISTING_ENV=true
    else
        EXISTING_ENV=false
    fi
    
    # 检查数据库
    if [ -f "xboard.db" ] || [ -f "backend/xboard.db" ]; then
        log_warning "检测到现有数据库，跳过初始化"
        EXISTING_DB=true
    else
        EXISTING_DB=false
    fi
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

# 检查Python环境
check_python_environment() {
    log_info "检查Python环境..."
    
    # 检查Python版本
    if ! command -v python3 &> /dev/null; then
        log_error "Python3未安装"
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
    
    # 检查pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3未安装"
        exit 1
    fi
    
    log_success "pip3检查通过"
}

# 检查Node.js环境
check_node_environment() {
    log_info "检查Node.js环境..."
    
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

# 检查数据库环境
check_database_environment() {
    log_info "检查数据库环境..."
    
    # 检查MySQL
    if command -v mysql &> /dev/null; then
        log_success "检测到MySQL"
        MYSQL_AVAILABLE=true
    else
        log_warning "MySQL未安装，将使用SQLite"
        MYSQL_AVAILABLE=false
    fi
    
    # 检查Redis
    if command -v redis-server &> /dev/null; then
        log_success "检测到Redis"
        REDIS_AVAILABLE=true
    else
        log_warning "Redis未安装，将跳过缓存功能"
        REDIS_AVAILABLE=false
    fi
    
    # 检查SQLite
    if command -v sqlite3 &> /dev/null; then
        log_success "检测到SQLite"
        SQLITE_AVAILABLE=true
    else
        log_warning "SQLite未安装"
        SQLITE_AVAILABLE=false
    fi
}

# 创建虚拟环境
create_virtual_environment() {
    log_info "创建Python虚拟环境..."
    
    if [ "$EXISTING_VENV" = true ]; then
        log_warning "检测到现有虚拟环境，跳过创建"
        return
    fi
    
    python3 -m venv venv
    log_success "虚拟环境创建成功"
}

# 激活虚拟环境
activate_virtual_environment() {
    log_info "激活虚拟环境..."
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        log_success "虚拟环境激活成功"
    else
        log_error "虚拟环境激活失败"
        exit 1
    fi
}

# 安装Python依赖
install_python_dependencies() {
    log_info "安装Python依赖..."
    
    if [ "$EXISTING_DEPS" = true ]; then
        log_warning "检测到已安装的Python依赖，跳过安装"
        return
    fi
    
    if [ ! -f "backend/requirements.txt" ]; then
        log_error "requirements.txt文件不存在"
        exit 1
    fi
    
    pip install --upgrade pip
    pip install -r backend/requirements.txt
    
    log_success "Python依赖安装完成"
}

# 安装前端依赖
install_frontend_dependencies() {
    log_info "安装前端依赖..."
    
    if [ ! -f "frontend/package.json" ]; then
        log_error "package.json文件不存在"
        exit 1
    fi
    
    cd frontend
    npm install
    cd ..
    
    log_success "前端依赖安装完成"
}

# 构建前端
build_frontend() {
    log_info "构建前端..."
    
    if [ "$EXISTING_FRONTEND" = true ]; then
        log_warning "检测到已构建的前端，跳过构建"
        return
    fi
    
    if ! command -v node &> /dev/null; then
        log_warning "Node.js未安装，跳过前端构建"
        return
    fi
    
    cd frontend
    npm run build
    cd ..
    
    log_success "前端构建完成"
}

# 配置环境变量
configure_environment() {
    log_info "配置环境变量..."
    
    if [ "$EXISTING_ENV" = true ]; then
        log_warning "检测到环境配置文件，跳过创建"
        return
    fi
    
    # 创建.env文件
    cat > .env << EOF
# ================================
# XBoard Modern 环境变量配置
# ================================

# 数据库配置
DATABASE_URL=sqlite:///./xboard.db

# 应用配置
DEBUG=True
HOST=0.0.0.0
PORT=8000
WORKERS=4

# 安全配置
SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
REFRESH_TOKEN_EXPIRE_DAYS=7

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

# 支付宝配置
ALIPAY_APP_ID=your-alipay-app-id
ALIPAY_PRIVATE_KEY=your-private-key
ALIPAY_PUBLIC_KEY=alipay-public-key
ALIPAY_NOTIFY_URL=https://yourdomain.com/api/v1/payment/alipay/notify
ALIPAY_RETURN_URL=https://yourdomain.com/api/v1/payment/alipay/return

# 文件上传配置
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760

# 订阅配置
SUBSCRIPTION_URL_PREFIX=https://yourdomain.com/sub
DEVICE_LIMIT_DEFAULT=3
EOF

    log_success "环境变量配置文件创建完成"
}

# 初始化数据库
initialize_database() {
    log_info "初始化数据库..."
    
    if [ "$EXISTING_DB" = true ]; then
        log_warning "检测到现有数据库，跳过初始化"
        return
    fi
    
    cd backend
    
    # 测试数据库连接
    python3 -c "
from app.core.database import test_database_connection, init_database
import logging

logging.basicConfig(level=logging.INFO)

if test_database_connection():
    print('数据库连接测试成功')
    if init_database():
        print('数据库初始化成功')
        else:
        print('数据库初始化失败')
        else:
    print('数据库连接测试失败')
"
    
    cd ..
    
    log_success "数据库初始化完成"
}

# 测试API连通性
test_api_connectivity() {
    log_info "测试API连通性..."
    
    cd backend
    
    # 启动后端服务进行测试
    timeout 30s python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    
    # 等待服务启动
    sleep 5
    
    # 测试API连通性
    if curl -s http://localhost:8000/docs > /dev/null; then
        log_success "API连通性测试成功"
    else
        log_warning "API连通性测试失败"
    fi
    
    # 停止测试服务
    kill $BACKEND_PID 2>/dev/null || true
    
    cd ..
}

# 测试数据库连通性
test_database_connectivity() {
    log_info "测试数据库连通性..."
    
    if [ -f "test_db_connection.py" ]; then
        python3 test_db_connection.py
        if [ $? -eq 0 ]; then
            log_success "数据库连通性测试成功"
        else
            log_warning "数据库连通性测试失败"
        fi
    else
        log_warning "数据库测试脚本不存在，跳过测试"
    fi
}

# 创建启动脚本
create_startup_scripts() {
    log_info "创建启动脚本..."
    
    # 创建start.sh
    cat > start.sh << 'EOF'
#!/bin/bash

# XBoard Modern 启动脚本

cd "$(dirname "$0")"

echo "启动 XBoard Modern..."

# 启动后端
    cd backend
source ../venv/bin/activate
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 启动前端（如果需要）
if [ -d "frontend/dist" ]; then
    cd frontend
    python3 -m http.server 8080 &
    FRONTEND_PID=$!
    cd ..
fi

echo "XBoard Modern 启动完成"
echo "后端地址: http://localhost:8000"
echo "前端地址: http://localhost:8080"
echo "API文档: http://localhost:8000/docs"

# 等待用户中断
trap "echo '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit" INT
wait
EOF
    
    chmod +x start.sh
    
    # 创建stop.sh
    cat > stop.sh << 'EOF'
#!/bin/bash

# XBoard Modern 停止脚本

echo "停止 XBoard Modern..."

# 停止后端
pkill -f "uvicorn app.main:app" || true

# 停止前端
pkill -f "python3 -m http.server" || true

echo "服务已停止"
EOF
    
    chmod +x stop.sh
    
    log_success "启动脚本创建完成"
}

# 显示安装完成信息
show_completion_info() {
    log_success "=========================================="
    log_success "XBoard Modern 安装完成！"
    log_success "=========================================="
    echo ""
    echo "项目路径: $PROJECT_ROOT"
    echo "虚拟环境: $PROJECT_ROOT/venv"
    echo "配置文件: $PROJECT_ROOT/.env"
    echo ""
    echo "启动服务:"
    echo "  ./start.sh          # 启动服务"
    echo "  ./stop.sh           # 停止服务"
    echo ""
    echo "访问地址:"
    echo "  后端API: http://localhost:8000"
    echo "  API文档: http://localhost:8000/docs"
    echo "  前端页面: http://localhost:8080"
    echo ""
    echo "注意事项:"
    echo "  1. 请编辑 .env 文件配置您的邮箱和支付信息"
    echo "  2. 首次启动会自动创建数据库表"
    echo "  3. 默认管理员账户需要手动创建"
    echo ""
    log_success "安装完成！"
}

# 主安装流程
main() {
    echo "=========================================="
    echo "XBoard Modern 智能安装脚本"
    echo "=========================================="
    echo ""
    
    # 检查系统要求
    check_system_requirements
    
    # 检测项目路径
    detect_project_path
    
    # 检查现有安装
    check_existing_installation
    
    # 检查Python环境
    check_python_environment
    
    # 检查Node.js环境
    check_node_environment
    
    # 检查数据库环境
    check_database_environment
    
    # 创建虚拟环境
    create_virtual_environment
    
    # 激活虚拟环境
    activate_virtual_environment
    
    # 安装Python依赖
    install_python_dependencies
    
    # 安装前端依赖
    install_frontend_dependencies
    
    # 构建前端
    build_frontend
    
    # 配置环境变量
    configure_environment
    
    # 初始化数据库
    initialize_database
    
    # 测试API连通性
    test_api_connectivity
    
    # 测试数据库连通性
    test_database_connectivity
    
    # 创建启动脚本
    create_startup_scripts
    
    # 显示完成信息
    show_completion_info
}

# 运行主函数
main "$@"
