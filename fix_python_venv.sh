#!/bin/bash

# ================================
# Python虚拟环境快速修复脚本
# ================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=========================================="
echo "🔧 Python虚拟环境快速修复脚本"
echo "=========================================="
echo ""

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    log_error "请使用root用户运行此脚本"
    exit 1
fi

# 检测Python版本
log_info "检测Python版本..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
    log_success "检测到Python版本: $PYTHON_VERSION"
else
    log_error "未检测到Python3"
    exit 1
fi

# 安装Python虚拟环境包
log_info "安装Python虚拟环境包..."
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -eq 3 ]; then
    case $PYTHON_MINOR in
        12)
            log_info "安装Python 3.12虚拟环境包..."
            apt install -y python3.12-venv python3.12-dev python3-pip
            ;;
        11)
            log_info "安装Python 3.11虚拟环境包..."
            apt install -y python3.11-venv python3.11-dev python3-pip
            ;;
        10)
            log_info "安装Python 3.10虚拟环境包..."
            apt install -y python3.10-venv python3.10-dev python3-pip
            ;;
        9)
            log_info "安装Python 3.9虚拟环境包..."
            apt install -y python3.9-venv python3.9-dev python3-pip
            ;;
        8)
            log_info "安装Python 3.8虚拟环境包..."
            apt install -y python3.8-venv python3.8-dev python3-pip
            ;;
        *)
            log_info "安装通用Python虚拟环境包..."
            apt install -y python3-venv python3-dev python3-pip
            ;;
    esac
else
    log_info "安装通用Python虚拟环境包..."
    apt install -y python3-venv python3-dev python3-pip
fi

log_success "Python虚拟环境包安装完成！"

# 验证安装
log_info "验证虚拟环境创建..."
if python3 -m venv --help &> /dev/null; then
    log_success "虚拟环境模块可用"
else
    log_error "虚拟环境模块不可用"
    exit 1
fi

echo ""
echo "=========================================="
echo "🎉 修复完成！"
echo "=========================================="
echo ""
echo "现在可以继续运行安装脚本了："
echo "  ./install_modern_system.sh"
echo ""
echo "或者手动创建虚拟环境："
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
echo ""
