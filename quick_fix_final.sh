#!/bin/bash

# 最终快速修复脚本
# 解决SCSS弃用警告和API导出问题

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
    log_info "开始最终快速修复..."
    
    # 检查是否在正确的目录
    if [ ! -d "frontend" ]; then
        log_error "未找到frontend目录"
        log_info "请确保在项目根目录中运行此脚本"
        exit 1
    fi
    
    cd frontend
    
    log_info "当前目录: $(pwd)"
    
    # 1. 修复SCSS弃用警告
    log_info "修复SCSS弃用警告..."
    
    # 更新global.scss中的map函数
    if [ -f "src/styles/global.scss" ]; then
        sed -i 's/map-has-key/map.has-key/g' src/styles/global.scss
        sed -i 's/map-get/map.get/g' src/styles/global.scss
        log_success "global.scss已更新"
    fi
    
    # 更新Vue文件中的@import为@use
    if [ -f "src/components/layout/UserLayout.vue" ]; then
        sed -i 's/@import '\''@\/styles\/global\.scss'\'';/@use '\''@\/styles\/global\.scss'\'' as *;/g' src/components/layout/UserLayout.vue
        log_success "UserLayout.vue已更新"
    fi
    
    if [ -f "src/components/layout/AdminLayout.vue" ]; then
        sed -i 's/@import '\''@\/styles\/global\.scss'\'';/@use '\''@\/styles\/global\.scss'\'' as *;/g' src/components/layout/AdminLayout.vue
        log_success "AdminLayout.vue已更新"
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
    
    log_success "最终修复完成！"
    
    # 5. 显示构建结果
    if [ -d "dist" ]; then
        log_info "构建输出:"
        ls -la dist/
    fi
    
    cd ..
}

# 运行主函数
main "$@" 