#!/bin/bash

# XBoard Modern 环境检查脚本
# 检查系统环境、依赖和配置状态

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 检查结果统计
PASS_COUNT=0
WARN_COUNT=0
ERROR_COUNT=0

# 自动检测项目路径
detect_project_path() {
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    if [[ -f "$SCRIPT_DIR/backend/main.py" ]]; then
        PROJECT_PATH="$SCRIPT_DIR"
    else
        COMMON_PATHS=(
            "/www/wwwroot/new.moneyfly.top"
            "/var/www/xboard"
            "/home/$(whoami)/xboard"
            "/opt/xboard"
            "$(pwd)"
        )
        
        for path in "${COMMON_PATHS[@]}"; do
            if [[ -f "$path/backend/main.py" ]]; then
                PROJECT_PATH="$path"
                break
            fi
        done
    fi
    
    if [[ -z "$PROJECT_PATH" ]]; then
        log_error "未找到项目文件"
        return 1
    fi
    
    log_info "项目路径: $PROJECT_PATH"
    return 0
}

# 检查操作系统
check_os() {
    log_info "检查操作系统..."
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        log_success "操作系统: $NAME $VERSION_ID"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        log_warning "无法检测操作系统版本"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
    
    # 检查架构
    ARCH=$(uname -m)
    log_info "系统架构: $ARCH"
    
    # 检查内核版本
    KERNEL=$(uname -r)
    log_info "内核版本: $KERNEL"
}

# 检查Python环境
check_python() {
    log_info "检查Python环境..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python版本: $PYTHON_VERSION"
        
        # 检查版本要求
        if [[ $(echo "$PYTHON_VERSION" | cut -d'.' -f1) -lt 3 ]] || [[ $(echo "$PYTHON_VERSION" | cut -d'.' -f2) -lt 8 ]]; then
            log_error "需要Python 3.8或更高版本"
            ERROR_COUNT=$((ERROR_COUNT + 1))
        else
            PASS_COUNT=$((PASS_COUNT + 1))
        fi
    else
        log_error "未找到Python3"
        ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
    
    # 检查pip
    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version | cut -d' ' -f2)
        log_success "pip版本: $PIP_VERSION"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        log_error "未找到pip3"
        ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
    
    # 检查虚拟环境
    if [[ -d "$PROJECT_PATH/venv" ]]; then
        log_success "虚拟环境存在"
        PASS_COUNT=$((PASS_COUNT + 1))
        
        # 检查虚拟环境中的Python
        if [[ -f "$PROJECT_PATH/venv/bin/python" ]]; then
            VENV_PYTHON_VERSION=$("$PROJECT_PATH/venv/bin/python" --version | cut -d' ' -f2)
            log_success "虚拟环境Python版本: $VENV_PYTHON_VERSION"
            PASS_COUNT=$((PASS_COUNT + 1))
        fi
    else
        log_warning "虚拟环境不存在"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
}

# 检查Node.js环境
check_nodejs() {
    log_info "检查Node.js环境..."
    
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version | cut -d'v' -f2)
        log_success "Node.js版本: $NODE_VERSION"
        
        if [[ $(echo "$NODE_VERSION" | cut -d'.' -f1) -lt 16 ]]; then
            log_error "需要Node.js 16或更高版本"
            ERROR_COUNT=$((ERROR_COUNT + 1))
        else
            PASS_COUNT=$((PASS_COUNT + 1))
        fi
    else
        log_warning "未找到Node.js"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
    
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        log_success "npm版本: $NPM_VERSION"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        log_warning "未找到npm"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
}

# 检查系统服务
check_services() {
    log_info "检查系统服务..."
    
    # 检查Nginx
    if command -v nginx &> /dev/null; then
        NGINX_VERSION=$(nginx -v 2>&1 | cut -d'/' -f2)
        log_success "Nginx版本: $NGINX_VERSION"
        PASS_COUNT=$((PASS_COUNT + 1))
        
        if systemctl is-active --quiet nginx; then
            log_success "Nginx服务运行中"
            PASS_COUNT=$((PASS_COUNT + 1))
        else
            log_warning "Nginx服务未运行"
            WARN_COUNT=$((WARN_COUNT + 1))
        fi
    else
        log_warning "未找到Nginx"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
    
    # 检查Redis
    if command -v redis-server &> /dev/null; then
        REDIS_VERSION=$(redis-server --version | cut -d' ' -f3)
        log_success "Redis版本: $REDIS_VERSION"
        PASS_COUNT=$((PASS_COUNT + 1))
        
        if systemctl is-active --quiet redis; then
            log_success "Redis服务运行中"
            PASS_COUNT=$((PASS_COUNT + 1))
        else
            log_warning "Redis服务未运行"
            WARN_COUNT=$((WARN_COUNT + 1))
        fi
    else
        log_warning "未找到Redis"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
    
    # 检查XBoard服务
    if systemctl list-unit-files | grep -q xboard-backend; then
        log_success "XBoard服务已安装"
        PASS_COUNT=$((PASS_COUNT + 1))
        
        if systemctl is-active --quiet xboard-backend; then
            log_success "XBoard服务运行中"
            PASS_COUNT=$((PASS_COUNT + 1))
        else
            log_warning "XBoard服务未运行"
            WARN_COUNT=$((WARN_COUNT + 1))
        fi
    else
        log_warning "XBoard服务未安装"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
}

# 检查项目文件
check_project_files() {
    log_info "检查项目文件..."
    
    REQUIRED_FILES=(
        "backend/main.py"
        "backend/requirements.txt"
        "frontend/package.json"
        "frontend/vite.config.js"
        ".env"
    )
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [[ -f "$PROJECT_PATH/$file" ]]; then
            log_success "文件存在: $file"
            PASS_COUNT=$((PASS_COUNT + 1))
        else
            log_error "文件缺失: $file"
            ERROR_COUNT=$((ERROR_COUNT + 1))
        fi
    done
    
    # 检查目录结构
    REQUIRED_DIRS=(
        "backend"
        "frontend"
        "uploads"
        "logs"
    )
    
    for dir in "${REQUIRED_DIRS[@]}"; do
        if [[ -d "$PROJECT_PATH/$dir" ]]; then
            log_success "目录存在: $dir"
            PASS_COUNT=$((PASS_COUNT + 1))
        else
            log_warning "目录缺失: $dir"
            WARN_COUNT=$((WARN_COUNT + 1))
        fi
    done
}

# 检查Python依赖
check_python_deps() {
    log_info "检查Python依赖..."
    
    if [[ -d "$PROJECT_PATH/venv" ]]; then
        source "$PROJECT_PATH/venv/bin/activate"
        
        REQUIRED_PACKAGES=(
            "fastapi"
            "uvicorn"
            "sqlalchemy"
            "pymysql"
            "python-jose"
            "passlib"
            "python-multipart"
            "python-dotenv"
            "pydantic"
            "email-validator"
            "redis"
            "aiofiles"
        )
        
        for package in "${REQUIRED_PACKAGES[@]}"; do
            if python -c "import $package" 2>/dev/null; then
                VERSION=$(python -c "import $package; print($package.__version__)" 2>/dev/null || echo "未知版本")
                log_success "$package: $VERSION"
                PASS_COUNT=$((PASS_COUNT + 1))
            else
                log_error "缺少依赖: $package"
                ERROR_COUNT=$((ERROR_COUNT + 1))
            fi
        done
        
        deactivate
    else
        log_warning "虚拟环境不存在，跳过依赖检查"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
}

# 检查前端依赖
check_frontend_deps() {
    log_info "检查前端依赖..."
    
    if [[ -d "$PROJECT_PATH/frontend" ]]; then
        cd "$PROJECT_PATH/frontend"
        
        if [[ -f "package.json" ]]; then
            log_success "package.json存在"
            PASS_COUNT=$((PASS_COUNT + 1))
            
            if [[ -d "node_modules" ]]; then
                log_success "node_modules存在"
                PASS_COUNT=$((PASS_COUNT + 1))
            else
                log_warning "node_modules不存在"
                WARN_COUNT=$((WARN_COUNT + 1))
            fi
            
            if [[ -d "dist" ]]; then
                log_success "dist目录存在（已构建）"
                PASS_COUNT=$((PASS_COUNT + 1))
            else
                log_warning "dist目录不存在（未构建）"
                WARN_COUNT=$((WARN_COUNT + 1))
            fi
        else
            log_error "package.json不存在"
            ERROR_COUNT=$((ERROR_COUNT + 1))
        fi
        
        cd - > /dev/null
    else
        log_warning "前端目录不存在"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
}

# 检查网络连接
check_network() {
    log_info "检查网络连接..."
    
    # 检查本地端口
    if netstat -tlnp 2>/dev/null | grep -q ":8000"; then
        log_success "端口8000正在监听"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        log_warning "端口8000未监听"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
    
    if netstat -tlnp 2>/dev/null | grep -q ":80"; then
        log_success "端口80正在监听"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        log_warning "端口80未监听"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
    
    # 检查外部连接
    if ping -c 1 8.8.8.8 &>/dev/null; then
        log_success "网络连接正常"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        log_error "网络连接异常"
        ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
}

# 检查磁盘空间
check_disk_space() {
    log_info "检查磁盘空间..."
    
    DISK_USAGE=$(df -h "$PROJECT_PATH" | tail -1 | awk '{print $5}' | sed 's/%//')
    DISK_AVAILABLE=$(df -h "$PROJECT_PATH" | tail -1 | awk '{print $4}')
    
    log_info "磁盘使用率: ${DISK_USAGE}%"
    log_info "可用空间: $DISK_AVAILABLE"
    
    if [[ $DISK_USAGE -lt 80 ]]; then
        log_success "磁盘空间充足"
        PASS_COUNT=$((PASS_COUNT + 1))
    elif [[ $DISK_USAGE -lt 90 ]]; then
        log_warning "磁盘空间不足"
        WARN_COUNT=$((WARN_COUNT + 1))
    else
        log_error "磁盘空间严重不足"
        ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
}

# 检查权限
check_permissions() {
    log_info "检查文件权限..."
    
    if [[ -r "$PROJECT_PATH" ]]; then
        log_success "项目目录可读"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        log_error "项目目录不可读"
        ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
    
    if [[ -w "$PROJECT_PATH" ]]; then
        log_success "项目目录可写"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        log_error "项目目录不可写"
        ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
    
    if [[ -x "$PROJECT_PATH" ]]; then
        log_success "项目目录可执行"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        log_error "项目目录不可执行"
        ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
}

# 显示检查结果
show_check_result() {
    echo
    echo "=================================="
    echo "        环境检查结果"
    echo "=================================="
    echo
    
    echo "检查项目: $((PASS_COUNT + WARN_COUNT + ERROR_COUNT))"
    echo "通过: $PASS_COUNT"
    echo "警告: $WARN_COUNT"
    echo "错误: $ERROR_COUNT"
    echo
    
    if [[ $ERROR_COUNT -eq 0 ]]; then
        if [[ $WARN_COUNT -eq 0 ]]; then
            log_success "环境检查完全通过！"
        else
            log_warning "环境检查通过，但有警告需要处理"
        fi
    else
        log_error "环境检查失败，请解决上述错误"
    fi
    
    echo
    echo "=== 建议操作 ==="
    if [[ $ERROR_COUNT -gt 0 ]]; then
        echo "• 解决所有错误项"
    fi
    if [[ $WARN_COUNT -gt 0 ]]; then
        echo "• 处理警告项以优化环境"
    fi
    echo "• 运行 ./install.sh 进行安装"
}

# 主检查流程
main() {
    echo "=================================="
    echo "    XBoard Modern 环境检查"
    echo "=================================="
    echo
    
    if ! detect_project_path; then
        log_error "无法找到项目路径"
        exit 1
    fi
    
    check_os
    check_python
    check_nodejs
    check_services
    check_project_files
    check_python_deps
    check_frontend_deps
    check_network
    check_disk_space
    check_permissions
    
    show_check_result
}

# 运行主函数
main "$@" 