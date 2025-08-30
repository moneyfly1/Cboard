#!/bin/bash

# 全面语法检查脚本

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
    log_info "开始全面语法检查..."
    
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
    
    # 检查依赖
    log_info "检查依赖..."
    if [ ! -d "node_modules" ]; then
        log_info "安装依赖..."
        npm install
    fi
    
    # 检查package.json中的依赖
    log_info "检查package.json依赖..."
    
    # 检查chart.js依赖
    if ! grep -q "chart.js" package.json; then
        log_warning "缺少chart.js依赖，正在添加..."
        npm install chart.js@^4.4.0
    fi
    
    # 检查其他可能缺少的依赖
    local missing_deps=()
    
    # 检查qrcode
    if ! grep -q "qrcode" package.json; then
        missing_deps+=("qrcode")
    fi
    
    # 检查dayjs
    if ! grep -q "dayjs" package.json; then
        missing_deps+=("dayjs")
    fi
    
    # 检查clipboard
    if ! grep -q "clipboard" package.json; then
        missing_deps+=("clipboard")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_warning "发现缺少的依赖: ${missing_deps[*]}"
        log_info "正在安装..."
        npm install "${missing_deps[@]}"
    fi
    
    log_success "依赖检查完成"
    
    # 检查Vue文件语法
    log_info "检查Vue文件语法..."
    
    # 检查是否有使用保留字作为参数的文件
    local reserved_words=("package" "class" "function" "var" "let" "const" "import" "export" "default" "return" "if" "else" "for" "while" "do" "switch" "case" "break" "continue" "try" "catch" "finally" "throw" "new" "delete" "typeof" "instanceof" "void" "null" "undefined" "true" "false" "this" "super" "with" "debugger" "enum" "interface" "extends" "implements" "public" "private" "protected" "static" "final" "abstract" "native" "synchronized" "transient" "volatile" "goto" "byte" "char" "double" "float" "int" "long" "short" "boolean")
    
    local found_issues=false
    
    for word in "${reserved_words[@]}"; do
        if grep -r "(${word})" src/ --include="*.vue" --include="*.js" > /dev/null 2>&1; then
            log_error "发现保留字问题: ${word} 被用作参数名"
            grep -r "(${word})" src/ --include="*.vue" --include="*.js" || true
            found_issues=true
        fi
    done
    
    if [ "$found_issues" = false ]; then
        log_success "未发现保留字问题"
    fi
    
    # 检查import语句
    log_info "检查import语句..."
    
    # 检查是否有无效的import
    local invalid_imports=()
    
    # 检查chart.js import
    if grep -r "import.*chart" src/ --include="*.vue" > /dev/null 2>&1; then
        if ! grep -q "chart.js" package.json; then
            invalid_imports+=("chart.js")
        fi
    fi
    
    # 检查qrcode import
    if grep -r "import.*qrcode" src/ --include="*.vue" > /dev/null 2>&1; then
        if ! grep -q "qrcode" package.json; then
            invalid_imports+=("qrcode")
        fi
    fi
    
    # 检查dayjs import
    if grep -r "import.*dayjs" src/ --include="*.vue" > /dev/null 2>&1; then
        if ! grep -q "dayjs" package.json; then
            invalid_imports+=("dayjs")
        fi
    fi
    
    if [ ${#invalid_imports[@]} -gt 0 ]; then
        log_error "发现无效的import: ${invalid_imports[*]}"
        log_info "正在安装缺少的依赖..."
        npm install "${invalid_imports[@]}"
    else
        log_success "import语句检查通过"
    fi
    
    # 运行ESLint检查
    log_info "运行ESLint检查..."
    if npm run lint 2>/dev/null; then
        log_success "ESLint检查通过"
    else
        log_warning "ESLint发现一些问题，但继续构建..."
    fi
    
    # 尝试构建
    log_info "尝试构建..."
    if npm run build; then
        log_success "构建成功！"
    else
        log_error "构建失败"
        exit 1
    fi
    
    log_success "全面语法检查完成！"
}

# 运行主函数
main "$@" 