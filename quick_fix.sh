#!/bin/bash

# 快速修复脚本 - 解决前端构建问题

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

# 主函数
main() {
    log_info "开始快速修复..."
    
    # 检查是否在正确的目录
    if [ ! -d "frontend" ]; then
        log_error "未找到frontend目录"
        log_info "请确保在项目根目录中运行此脚本"
        exit 1
    fi
    
    cd frontend
    
    log_info "当前目录: $(pwd)"
    
    # 1. 清理缓存
    log_info "清理缓存..."
    rm -rf node_modules/.cache
    rm -rf dist
    
    # 2. 重新安装依赖
    log_info "重新安装依赖..."
    npm install
    
    # 3. 确保chart.js已安装
    log_info "检查chart.js依赖..."
    if ! npm list chart.js > /dev/null 2>&1; then
        log_info "安装chart.js..."
        npm install chart.js@^4.4.0
    fi
    
    # 4. 检查其他依赖
    log_info "检查其他依赖..."
    local deps=("qrcode" "dayjs" "clipboard")
    for dep in "${deps[@]}"; do
        if ! npm list "$dep" > /dev/null 2>&1; then
            log_info "安装 $dep..."
            npm install "$dep"
        fi
    done
    
    log_success "依赖安装完成"
    
    # 5. 尝试构建
    log_info "开始构建..."
    npm run build
    
    log_success "构建成功！"
    
    # 6. 显示构建结果
    if [ -d "dist" ]; then
        log_info "构建输出:"
        ls -la dist/
    fi
}

# 运行主函数
main "$@" 