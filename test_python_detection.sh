#!/bin/bash

# ================================
# Python检测测试脚本
# ================================

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=========================================="
echo "🐍 Python环境检测测试"
echo "=========================================="
echo ""

# 检测已安装的Python版本
PYTHON_VERSIONS=()
PYTHON_CMD=""

log_info "开始检测Python环境..."

# 检查python3命令
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
    PYTHON_VERSIONS+=("$PYTHON_VERSION")
    log_success "检测到已安装的Python3: $PYTHON_VERSION"
else
    log_warning "未找到python3命令"
fi

# 检查python命令
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
    if [[ ! " ${PYTHON_VERSIONS[@]} " =~ " ${PYTHON_VERSION} " ]]; then
        PYTHON_VERSIONS+=("$PYTHON_VERSION")
    fi
    log_success "检测到已安装的Python: $PYTHON_VERSION"
else
    log_warning "未找到python命令"
fi

# 检查特定版本
for version in "3.11" "3.10" "3.9" "3.8" "3.7" "3.6"; do
    if command -v "python$version" &> /dev/null; then
        PYTHON_VERSION=$(python$version --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        if [[ ! " ${PYTHON_VERSIONS[@]} " =~ " ${PYTHON_VERSION} " ]]; then
            PYTHON_VERSIONS+=("$PYTHON_VERSION")
        fi
        log_success "检测到已安装的Python$version: $PYTHON_VERSION"
    fi
done

echo ""
log_info "检测结果汇总:"
echo "=========================================="

if [ ${#PYTHON_VERSIONS[@]} -gt 0 ]; then
    # 按版本号排序，选择最高版本
    IFS=$'\n' sorted_versions=($(sort -V -r <<<"${PYTHON_VERSIONS[*]}"))
    unset IFS
    
    BEST_VERSION="${sorted_versions[0]}"
    log_success "最佳Python版本: $BEST_VERSION"
    
    # 设置主要Python命令
    if command -v "python$BEST_VERSION" &> /dev/null; then
        PYTHON_CMD="python$BEST_VERSION"
        log_success "推荐使用命令: $PYTHON_CMD"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        log_success "推荐使用命令: $PYTHON_CMD"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        log_success "推荐使用命令: $PYTHON_CMD"
    fi
    
    echo ""
    log_info "所有检测到的Python版本:"
    for version in "${sorted_versions[@]}"; do
        echo "  - Python $version"
    done
    
    echo ""
    log_info "系统信息:"
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "  操作系统: $PRETTY_NAME"
        echo "  版本: $VERSION_ID"
    fi
    
    ARCH=$(uname -m)
    echo "  架构: $ARCH"
    
else
    log_error "未检测到任何Python版本"
    echo ""
    log_info "建议安装Python 3.6+"
fi

echo ""
echo "=========================================="
echo "测试完成！"
echo "=========================================="
