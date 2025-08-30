#!/bin/bash

# XBoard Modern 卸载脚本

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

# 检测操作系统
detect_os() {
    OS=$(uname -s)
    case $OS in
        Linux)
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                OS_NAME=$NAME
            else
                OS_NAME="Linux"
            fi
            ;;
        Darwin)
            OS_NAME="macOS"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            OS_NAME="Windows"
            ;;
        *)
            OS_NAME="Unknown"
            ;;
    esac
    
    log_info "操作系统: $OS_NAME"
}

# 获取项目路径
get_project_path() {
    if [ -n "$1" ]; then
        PROJECT_PATH="$1"
    else
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        PROJECT_PATH="$(dirname "$SCRIPT_DIR")"
    fi
    
    if [ ! -d "$PROJECT_PATH" ]; then
        log_error "项目路径不存在: $PROJECT_PATH"
        exit 1
    fi
    
    log_info "项目路径: $PROJECT_PATH"
    cd "$PROJECT_PATH"
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    
    if [ "$OS_NAME" = "Linux" ]; then
        if systemctl is-active --quiet xboard-backend; then
            systemctl stop xboard-backend
            log_success "后端服务已停止"
        fi
        
        if systemctl is-enabled --quiet xboard-backend; then
            systemctl disable xboard-backend
            log_success "后端服务已禁用"
        fi
    else
        log_info "跳过服务停止 (非Linux系统)"
    fi
}

# 删除系统服务
remove_systemd_service() {
    if [ "$OS_NAME" != "Linux" ]; then
        log_info "跳过系统服务删除 (非Linux系统)"
        return
    fi
    
    log_info "删除系统服务..."
    
    if [ -f "/etc/systemd/system/xboard-backend.service" ]; then
        rm -f /etc/systemd/system/xboard-backend.service
        systemctl daemon-reload
        log_success "系统服务已删除"
    fi
}

# 删除Nginx配置
remove_nginx_config() {
    if [ "$OS_NAME" != "Linux" ]; then
        log_info "跳过Nginx配置删除 (非Linux系统)"
        return
    fi
    
    log_info "删除Nginx配置..."
    
    if [ -f "/etc/nginx/sites-enabled/xboard" ]; then
        rm -f /etc/nginx/sites-enabled/xboard
        log_success "Nginx站点配置已删除"
    fi
    
    if [ -f "/etc/nginx/sites-available/xboard" ]; then
        rm -f /etc/nginx/sites-available/xboard
        log_success "Nginx配置文件已删除"
    fi
}

# 删除项目文件
remove_project_files() {
    log_info "删除项目文件..."
    
    # 确认删除
    echo "警告：此操作将删除以下内容："
    echo "- 项目目录: $PROJECT_PATH"
    echo "- 数据库文件 (如果使用SQLite)"
    echo "- 上传的文件"
    echo "- 日志文件"
    echo
    read -p "确定要删除吗？(输入 'yes' 确认): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "取消删除操作"
        return
    fi
    
    # 删除项目目录
    if [ -d "$PROJECT_PATH" ]; then
        rm -rf "$PROJECT_PATH"
        log_success "项目目录已删除"
    fi
}

# 清理数据库
cleanup_database() {
    log_info "清理数据库..."
    
    # 检查是否有数据库文件
    if [ -f "xboard.db" ]; then
        echo "发现SQLite数据库文件"
        read -p "是否删除数据库文件？(y/N): " delete_db
        
        if [[ $delete_db =~ ^[Yy]$ ]]; then
            rm -f xboard.db
            log_success "数据库文件已删除"
        fi
    fi
}

# 清理日志
cleanup_logs() {
    log_info "清理日志..."
    
    if [ -d "logs" ]; then
        rm -rf logs
        log_success "日志目录已删除"
    fi
}

# 清理缓存
cleanup_cache() {
    log_info "清理缓存..."
    
    # 清理Python缓存
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    # 清理Node.js缓存
    if [ -d "frontend/node_modules" ]; then
        rm -rf frontend/node_modules
        log_success "Node.js缓存已清理"
    fi
    
    log_success "缓存清理完成"
}

# 显示卸载结果
show_result() {
    log_success "卸载完成！"
    echo
    echo "=== 卸载内容 ==="
    echo "✓ 系统服务已删除"
    echo "✓ Nginx配置已删除"
    echo "✓ 项目文件已删除"
    echo "✓ 缓存已清理"
    echo
    echo "=== 注意事项 ==="
    echo "1. 如果使用了外部数据库，请手动清理"
    echo "2. 如果配置了域名解析，请手动删除"
    echo "3. 如果修改了防火墙规则，请手动恢复"
    echo
    echo "感谢使用 XBoard Modern！"
}

# 主卸载流程
main() {
    echo "=================================="
    echo "    XBoard Modern 卸载程序"
    echo "=================================="
    echo
    
    # 检测操作系统
    detect_os
    
    # 获取项目路径
    get_project_path "$1"
    
    # 停止服务
    stop_services
    
    # 删除系统服务
    remove_systemd_service
    
    # 删除Nginx配置
    remove_nginx_config
    
    # 清理数据库
    cleanup_database
    
    # 清理日志
    cleanup_logs
    
    # 清理缓存
    cleanup_cache
    
    # 删除项目文件
    remove_project_files
    
    # 显示结果
    show_result
}

# 运行主程序
main "$@" 