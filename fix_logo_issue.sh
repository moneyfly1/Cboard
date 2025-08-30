#!/bin/bash

# 修复logo问题的脚本

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
    log_info "开始修复logo问题..."
    
    # 检查是否在正确的目录
    if [ ! -d "frontend" ]; then
        log_error "未找到frontend目录"
        log_info "请确保在项目根目录中运行此脚本"
        exit 1
    fi
    
    cd frontend
    
    log_info "当前目录: $(pwd)"
    
    # 1. 检查public目录
    log_info "检查public目录..."
    if [ ! -d "public" ]; then
        log_info "创建public目录..."
        mkdir -p public
    fi
    
    # 2. 确保vite.svg存在
    if [ ! -f "public/vite.svg" ]; then
        log_info "创建vite.svg文件..."
        cat > public/vite.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class="iconify iconify--logos" width="31.88" height="32" preserveAspectRatio="xMidYMid meet" viewBox="0 0 256 257"><defs><linearGradient id="IconifyId1813088fe1fbc01fb466" x1="-.828%" x2="57.636%" y1="7.652%" y2="78.411%"><stop offset="0%" stop-color="#41D1FF"></stop><stop offset="100%" stop-color="#BD34FE"></stop></linearGradient><linearGradient id="IconifyId1813088fe1fbc01fb467" x1="43.376%" x2="50.316%" y1="2.242%" y2="89.03%"><stop offset="0%" stop-color="#FFEA83"></stop><stop offset="8.333%" stop-color="#FFDD35"></stop><stop offset="100%" stop-color="#FFA800"></stop></linearGradient></defs><path fill="url(#IconifyId1813088fe1fbc01fb466)" d="M255.153 37.938L134.897 252.976c-2.483 4.44-8.862 4.466-11.382.048L.875 37.958c-2.746-4.814 1.371-10.646 6.827-9.67l120.385 21.517a6.537 6.537 0 0 0 2.322-.004l117.867-21.483c5.438-.991 9.574 4.796 6.877 9.62Z"></path><path fill="url(#IconifyId1813088fe1fbc01fb467)" d="M185.432.063L96.44 17.501a3.268 3.268 0 0 0-2.634 3.014l-5.474 92.456a3.268 3.268 0 0 0 3.997 3.378l24.777-5.718c2.318-.535 4.413 1.507 3.936 3.838l-7.361 36.047c-.495 2.426 1.782 4.5 4.151 3.78l15.304-4.649c2.372-.72 4.652 1.36 4.15 3.788l-11.698 56.621c-.732 3.542 3.979 5.473 5.943 2.437l1.313-2.028l72.516-144.72c1.215-2.423-.88-5.186-3.54-4.672l-25.505 4.922c-2.396.462-4.435-1.77-3.759-4.114l16.646-57.705c.677-2.35-1.37-4.583-3.769-4.113Z"></path></svg>
EOF
    fi
    
    # 3. 检查并修复Vue文件中的logo引用
    log_info "检查Vue文件中的logo引用..."
    
    # 修复UserLayout.vue
    if [ -f "src/components/layout/UserLayout.vue" ]; then
        log_info "修复UserLayout.vue..."
        sed -i 's|src="/logo.png"|src="/vite.svg"|g' src/components/layout/UserLayout.vue
    fi
    
    # 修复AdminLayout.vue
    if [ -f "src/components/layout/AdminLayout.vue" ]; then
        log_info "修复AdminLayout.vue..."
        sed -i 's|src="/logo.png"|src="/vite.svg"|g' src/components/layout/AdminLayout.vue
    fi
    
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
    
    log_success "logo问题修复完成！"
    
    # 7. 显示构建结果
    if [ -d "dist" ]; then
        log_info "构建输出:"
        ls -la dist/
    fi
}

# 运行主函数
main "$@" 