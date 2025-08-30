#!/bin/bash

# 测试目录识别功能

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

# 测试目录识别
test_path_detection() {
    log_info "开始测试目录识别功能..."
    
    CURRENT_DIR=$(pwd)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    log_info "当前工作目录: $CURRENT_DIR"
    log_info "脚本所在目录: $SCRIPT_DIR"
    
    # 策略1: 检查当前目录是否就是项目根目录
    if [ -d "backend" ] && [ -d "frontend" ] && [ -f "backend/requirements.txt" ]; then
        PROJECT_PATH="$CURRENT_DIR"
        log_success "策略1成功: 检测到当前目录为项目根目录"
        return 0
    fi
    
    # 策略2: 检查当前目录是否包含xboard-modern子目录
    if [ -d "xboard-modern" ]; then
        PROJECT_PATH="$CURRENT_DIR/xboard-modern"
        log_success "策略2成功: 检测到xboard-modern子目录"
        return 0
    fi
    
    # 策略3: 检查脚本目录是否在项目内
    if [ -d "$SCRIPT_DIR/backend" ] && [ -d "$SCRIPT_DIR/frontend" ]; then
        PROJECT_PATH="$SCRIPT_DIR"
        log_success "策略3成功: 检测到脚本在项目目录内"
        return 0
    fi
    
    # 策略4: 检查脚本目录的父目录是否包含项目
    if [ -d "$(dirname "$SCRIPT_DIR")/backend" ] && [ -d "$(dirname "$SCRIPT_DIR")/frontend" ]; then
        PROJECT_PATH="$(dirname "$SCRIPT_DIR")"
        log_success "策略4成功: 检测到项目在脚本父目录"
        return 0
    fi
    
    # 策略5: 递归查找项目目录
    log_info "尝试递归查找项目目录..."
    FOUND_PATH=""
    
    # 从当前目录开始向上查找
    SEARCH_DIR="$CURRENT_DIR"
    while [ "$SEARCH_DIR" != "/" ] && [ -n "$SEARCH_DIR" ]; do
        if [ -d "$SEARCH_DIR/backend" ] && [ -d "$SEARCH_DIR/frontend" ] && [ -f "$SEARCH_DIR/backend/requirements.txt" ]; then
            FOUND_PATH="$SEARCH_DIR"
            break
        fi
        SEARCH_DIR=$(dirname "$SEARCH_DIR")
    done
    
    if [ -n "$FOUND_PATH" ]; then
        PROJECT_PATH="$FOUND_PATH"
        log_success "策略5成功: 递归查找到项目目录: $PROJECT_PATH"
        return 0
    fi
    
    log_error "所有策略都失败了"
    log_info "当前目录内容:"
    ls -la
    return 1
}

# 运行测试
if test_path_detection; then
    log_success "目录识别测试成功！"
    log_info "检测到的项目路径: $PROJECT_PATH"
else
    log_error "目录识别测试失败！"
    exit 1
fi 