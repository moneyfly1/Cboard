#!/bin/bash

# 修复前端构建问题脚本

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
    log_info "开始修复前端构建问题..."
    
    # 检查是否在正确的目录
    if [ ! -d "frontend" ]; then
        log_error "未找到frontend目录"
        log_info "请确保在项目根目录中运行此脚本"
        exit 1
    fi
    
    cd frontend
    
    log_info "检查Node.js环境..."
    if ! command -v node &> /dev/null; then
        log_error "Node.js未安装"
        exit 1
    fi
    
    log_info "Node.js版本: $(node --version)"
    log_info "npm版本: $(npm --version)"
    
    log_info "清理node_modules..."
    if [ -d "node_modules" ]; then
        rm -rf node_modules
        log_success "node_modules已清理"
    fi
    
    log_info "清理package-lock.json..."
    if [ -f "package-lock.json" ]; then
        rm package-lock.json
        log_success "package-lock.json已清理"
    fi
    
    log_info "重新安装依赖..."
    npm install
    
    log_success "依赖安装完成"
    
    log_info "检查语法错误..."
    npm run lint 2>/dev/null || {
        log_warning "发现代码风格问题，但继续构建..."
    }
    
    log_info "开始构建..."
    npm run build
    
    log_success "前端构建完成！"
    
    log_info "构建输出目录: dist/"
    if [ -d "dist" ]; then
        log_info "构建文件列表:"
        ls -la dist/
    fi
}

# 运行主函数
main "$@" 