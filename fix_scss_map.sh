#!/bin/bash

# 修复SCSS map模块问题

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
    log_info "修复SCSS map模块问题..."
    
    # 检查是否在正确的目录
    if [ ! -d "frontend" ]; then
        log_error "未找到frontend目录"
        log_info "请确保在项目根目录中运行此脚本"
        exit 1
    fi
    
    cd frontend
    
    log_info "当前目录: $(pwd)"
    
    # 1. 修复global.scss文件
    log_info "修复global.scss文件..."
    
    if [ -f "src/styles/global.scss" ]; then
        # 检查是否已经有@use "sass:map"
        if ! grep -q "@use \"sass:map\"" src/styles/global.scss; then
            # 在文件开头添加map模块导入
            sed -i '1i @use "sass:map";' src/styles/global.scss
            log_success "已添加 @use \"sass:map\"; 到global.scss"
        else
            log_info "global.scss已经包含map模块导入"
        fi
        
        # 确保map函数使用正确的语法
        sed -i 's/map-has-key/map.has-key/g' src/styles/global.scss
        sed -i 's/map-get/map.get/g' src/styles/global.scss
        log_success "已更新map函数语法"
    else
        log_error "global.scss文件不存在"
        exit 1
    fi
    
    # 2. 清理缓存
    log_info "清理缓存..."
    rm -rf node_modules/.cache
    rm -rf dist
    
    # 3. 重新安装依赖
    log_info "重新安装依赖..."
    npm install
    
    # 4. 尝试构建
    log_info "开始构建..."
    npm run build
    
    log_success "SCSS map模块问题修复完成！"
    
    # 5. 显示构建结果
    if [ -d "dist" ]; then
        log_info "构建输出:"
        ls -la dist/
    fi
    
    cd ..
}

# 运行主函数
main "$@" 