#!/bin/bash

# XBoard Modern 修复安装脚本
# 专门处理目录结构问题

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
    log_info "开始修复安装..."
    
    # 智能检测项目路径
    CURRENT_DIR=$(pwd)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    log_info "当前工作目录: $CURRENT_DIR"
    log_info "脚本所在目录: $SCRIPT_DIR"
    
    # 策略1: 检查当前目录是否就是项目根目录
    if [ -d "backend" ] && [ -d "frontend" ] && [ -f "backend/requirements.txt" ]; then
        PROJECT_DIR="$CURRENT_DIR"
        log_info "检测到当前目录为项目根目录"
    # 策略2: 检查当前目录是否包含xboard-modern子目录
    elif [ -d "xboard-modern" ]; then
        PROJECT_DIR="$CURRENT_DIR/xboard-modern"
        log_info "检测到xboard-modern子目录"
    # 策略3: 检查脚本目录是否在项目内
    elif [ -d "$SCRIPT_DIR/backend" ] && [ -d "$SCRIPT_DIR/frontend" ]; then
        PROJECT_DIR="$SCRIPT_DIR"
        log_info "检测到脚本在项目目录内"
    # 策略4: 检查脚本目录的父目录是否包含项目
    elif [ -d "$(dirname "$SCRIPT_DIR")/backend" ] && [ -d "$(dirname "$SCRIPT_DIR")/frontend" ]; then
        PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
        log_info "检测到项目在脚本父目录"
    # 策略5: 递归查找项目目录
    else
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
            PROJECT_DIR="$FOUND_PATH"
            log_info "递归查找到项目目录: $PROJECT_DIR"
        else
            log_error "无法找到项目目录"
            log_info "请确保在以下任一位置运行脚本："
            log_info "1. 项目根目录（包含backend和frontend目录）"
            log_info "2. 包含xboard-modern子目录的目录"
            log_info "3. 项目目录的父目录"
            exit 1
        fi
    fi
    
    # 验证项目路径
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "项目路径不存在: $PROJECT_DIR"
        exit 1
    fi
    
    # 验证项目结构
    if [ ! -d "$PROJECT_DIR/backend" ] || [ ! -d "$PROJECT_DIR/frontend" ] || [ ! -f "$PROJECT_DIR/backend/requirements.txt" ]; then
        log_error "项目结构不完整: $PROJECT_DIR"
        log_info "项目应包含: backend/, frontend/, backend/requirements.txt"
        exit 1
    fi
    
    log_success "项目目录: $PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    # 检查必要文件
    if [ ! -f "backend/requirements.txt" ]; then
        log_error "找不到 backend/requirements.txt 文件"
        log_info "目录内容:"
        ls -la
        if [ -d "backend" ]; then
            log_info "backend目录内容:"
            ls -la backend/
        fi
        exit 1
    fi
    
    log_success "文件检查通过"
    
    # 设置Python环境
    log_info "设置Python环境..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "虚拟环境创建成功"
    else
        log_info "虚拟环境已存在"
    fi
    
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    log_success "Python环境设置完成"
    
    # 安装Python依赖
    log_info "安装Python依赖..."
    
    # 安装依赖
    pip install -r backend/requirements.txt
    
    log_success "Python依赖安装完成"
    
    # 创建必要目录
    log_info "创建必要目录..."
    
    mkdir -p uploads
    mkdir -p logs
    mkdir -p backend/static
    mkdir -p backend/templates
    
    log_success "目录创建完成"
    
    # 复制环境配置文件
    if [ ! -f ".env" ] && [ -f "env.example" ]; then
        log_info "复制环境配置文件..."
        cp env.example .env
        log_success "环境配置文件已创建，请编辑 .env 文件配置数据库等信息"
    fi
    
    log_success "安装完成！"
    log_info "下一步："
    log_info "1. 编辑 .env 文件配置数据库连接"
    log_info "2. 运行 python init_database.py 初始化数据库"
    log_info "3. 运行 python -m uvicorn app.main:app --reload 启动后端服务"
}

# 运行主函数
main "$@" 