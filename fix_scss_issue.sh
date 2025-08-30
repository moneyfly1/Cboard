#!/bin/bash

# 修复SCSS问题的脚本

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
    log_info "开始修复SCSS问题..."
    
    # 检查是否在正确的目录
    if [ ! -d "frontend" ]; then
        log_error "未找到frontend目录"
        log_info "请确保在项目根目录中运行此脚本"
        exit 1
    fi
    
    cd frontend
    
    log_info "当前目录: $(pwd)"
    
    # 1. 检查并修复Vue文件中的SCSS导入
    log_info "检查Vue文件中的SCSS导入..."
    
    # 修复UserLayout.vue
    if [ -f "src/components/layout/UserLayout.vue" ]; then
        log_info "修复UserLayout.vue..."
        if ! grep -q "@import '@/styles/global.scss';" src/components/layout/UserLayout.vue; then
            sed -i '/<style scoped lang="scss">/a @import '\''@/styles/global.scss'\'';' src/components/layout/UserLayout.vue
        fi
    fi
    
    # 修复AdminLayout.vue
    if [ -f "src/components/layout/AdminLayout.vue" ]; then
        log_info "修复AdminLayout.vue..."
        if ! grep -q "@import '@/styles/global.scss';" src/components/layout/AdminLayout.vue; then
            sed -i '/<style scoped lang="scss">/a @import '\''@/styles/global.scss'\'';' src/components/layout/AdminLayout.vue
        fi
    fi
    
    # 2. 检查global.scss文件
    log_info "检查global.scss文件..."
    if [ ! -f "src/styles/global.scss" ]; then
        log_error "global.scss文件不存在"
        exit 1
    fi
    
    # 3. 更新sass版本以解决deprecation警告
    log_info "更新sass版本..."
    npm install sass@latest
    
    # 4. 清理缓存
    log_info "清理缓存..."
    rm -rf node_modules/.cache
    rm -rf dist
    
    # 5. 重新安装依赖
    log_info "重新安装依赖..."
    npm install
    
    # 6. 尝试构建
    log_info "开始构建..."
    npm run build
    
    log_success "SCSS问题修复完成！"
    
    # 7. 显示构建结果
    if [ -d "dist" ]; then
        log_info "构建输出:"
        ls -la dist/
    fi
}

# 运行主函数
main "$@" 