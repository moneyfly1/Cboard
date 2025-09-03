#!/bin/bash

# ================================
# 修复当前安装问题的脚本
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
echo "🔧 修复当前安装问题"
echo "=========================================="
echo ""

# 检查当前目录
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    log_error "请在项目根目录运行此脚本"
    exit 1
fi

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
log_info "检测到Python版本: $PYTHON_VERSION"

if [ "$PYTHON_VERSION" != "3.6" ]; then
    log_warning "此脚本专为Python 3.6设计，当前版本: $PYTHON_VERSION"
fi

# 激活虚拟环境
if [ -d "venv" ]; then
    log_info "激活虚拟环境..."
    source venv/bin/activate
else
    log_error "虚拟环境不存在，请先创建"
    exit 1
fi

# 升级pip
log_info "升级pip..."
pip install --upgrade pip

# 安装兼容的依赖
log_info "安装Python 3.6兼容的依赖..."

# 基础依赖 - 兼容Python 3.6
pip install "fastapi<0.84.0"
pip install "uvicorn<0.18.0"
pip install "sqlalchemy<1.5.0"
pip install "alembic<1.8.0"
pip install "python-multipart<0.1.0"
pip install "python-jose[cryptography]==3.3.0"
pip install "passlib[bcrypt]==1.7.4"
pip install "python-dotenv<0.20.0"
pip install "pydantic<2.0.0"
pip install "pydantic-settings<2.0.0"

# 数据库驱动
pip install "mysqlclient<2.2.0"
pip install "pymysql<1.1.0"
pip install "psycopg2-binary<3.0.0"
pip install "aiosqlite<0.18.0"

# 邮件和模板
pip install "jinja2<3.2.0"
pip install "email-validator<2.1.0"

# 异步和队列
pip install "celery<5.3.0"
pip install "redis<4.4.0"

# 工具库
pip install "httpx<0.24.0"
pip install "watchfiles<0.20.0"
pip install "websockets<11.0"

# 开发和测试
pip install "pytest<7.0.0"
pip install "black<22.0.0"
pip install "flake8<5.0.0"
pip install "isort<5.11.0"

# 系统兼容性包
pip install "cryptography<37.0.0"
pip install "pycparser<2.22.0"

# 额外兼容包
pip install "typing-extensions<4.2.0"
pip install "dataclasses<0.7"

log_success "Python 3.6兼容依赖安装完成！"

# 验证安装
log_info "验证安装..."
python -c "import fastapi, uvicorn, sqlalchemy, alembic; print('✅ 核心依赖导入成功')"

echo ""
echo "=========================================="
echo "🎉 修复完成！"
echo "=========================================="
echo ""
echo "现在可以继续运行安装脚本了："
echo "  ./install_vps_fixed_v2.sh"
echo ""
echo "或者直接构建前端："
echo "  cd frontend && npm install && npm run build"
echo ""
