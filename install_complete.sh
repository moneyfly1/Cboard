#!/bin/bash

# XBoard Modern 完整安装脚本
# 支持自动环境检测和智能安装

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

# 检测操作系统和架构
detect_os_and_arch() {
    log_info "检测操作系统和架构..."
    
    OS=$(uname -s)
    ARCH=$(uname -m)
    
    case $OS in
        Linux)
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                OS_NAME=$NAME
                OS_VERSION=$VERSION_ID
            else
                OS_NAME="Linux"
                OS_VERSION="unknown"
            fi
            ;;
        Darwin)
            OS_NAME="macOS"
            OS_VERSION=$(sw_vers -productVersion)
            ;;
        MINGW*|MSYS*|CYGWIN*)
            OS_NAME="Windows"
            OS_VERSION="unknown"
            ;;
        *)
            OS_NAME="Unknown"
            OS_VERSION="unknown"
            ;;
    esac
    
    log_success "操作系统: $OS_NAME $OS_VERSION"
    log_success "架构: $ARCH"
}

# 获取项目路径
get_project_path() {
    if [ -n "$1" ]; then
        PROJECT_PATH="$1"
    else
        # 智能检测项目路径
        CURRENT_DIR=$(pwd)
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        
        log_info "当前工作目录: $CURRENT_DIR"
        log_info "脚本所在目录: $SCRIPT_DIR"
        
        # 策略1: 检查当前目录是否就是项目根目录（包含backend、frontend等目录）
        if [ -d "backend" ] && [ -d "frontend" ] && [ -f "backend/requirements.txt" ]; then
            PROJECT_PATH="$CURRENT_DIR"
            log_info "检测到当前目录为项目根目录"
        # 策略2: 检查当前目录是否包含xboard-modern子目录
        elif [ -d "xboard-modern" ]; then
            PROJECT_PATH="$CURRENT_DIR/xboard-modern"
            log_info "检测到xboard-modern子目录"
        # 策略3: 检查脚本目录是否在项目内
        elif [ -d "$SCRIPT_DIR/backend" ] && [ -d "$SCRIPT_DIR/frontend" ]; then
            PROJECT_PATH="$SCRIPT_DIR"
            log_info "检测到脚本在项目目录内"
        # 策略4: 检查脚本目录的父目录是否包含项目
        elif [ -d "$(dirname "$SCRIPT_DIR")/backend" ] && [ -d "$(dirname "$SCRIPT_DIR")/frontend" ]; then
            PROJECT_PATH="$(dirname "$SCRIPT_DIR")"
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
                PROJECT_PATH="$FOUND_PATH"
                log_info "递归查找到项目目录: $PROJECT_PATH"
            else
                log_error "无法找到项目目录"
                log_info "请确保在以下任一位置运行脚本："
                log_info "1. 项目根目录（包含backend和frontend目录）"
                log_info "2. 包含xboard-modern子目录的目录"
                log_info "3. 项目目录的父目录"
                exit 1
            fi
        fi
    fi
    
    # 验证项目路径
    if [ ! -d "$PROJECT_PATH" ]; then
        log_error "项目路径不存在: $PROJECT_PATH"
        exit 1
    fi
    
    # 验证项目结构
    if [ ! -d "$PROJECT_PATH/backend" ] || [ ! -d "$PROJECT_PATH/frontend" ] || [ ! -f "$PROJECT_PATH/backend/requirements.txt" ]; then
        log_error "项目结构不完整: $PROJECT_PATH"
        log_info "项目应包含: backend/, frontend/, backend/requirements.txt"
        exit 1
    fi
    
    log_success "项目路径: $PROJECT_PATH"
    cd "$PROJECT_PATH"
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖..."
    
    case $OS_NAME in
        *Ubuntu*|*Debian*)
            apt update
            apt install -y python3 python3-dev python3-venv python3-pip build-essential curl git nginx wget
            log_info "跳过启动现有服务，避免与宝塔面板冲突"
            ;;
        *CentOS*|*Red*Hat*|*Fedora*)
            yum update -y
            yum install -y python3 python3-devel python3-pip gcc curl git nginx wget
            log_info "跳过启动现有服务，避免与宝塔面板冲突"
            ;;
        *Arch*)
            pacman -Syu --noconfirm python python-pip base-devel curl git nginx wget
            log_info "跳过启动现有服务，避免与宝塔面板冲突"
            ;;
        macOS)
            if ! command -v brew &> /dev/null; then
                log_info "安装 Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install python3 node nginx
            ;;
        *)
            log_warning "未知操作系统，请手动安装依赖"
            ;;
    esac
    
    # 安装 Node.js (如果未安装)
    if ! command -v node &> /dev/null; then
        log_info "安装 Node.js..."
        case $OS_NAME in
            *Ubuntu*|*Debian*)
                curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
                apt install -y nodejs
                ;;
            *CentOS*|*Red*Hat*|*Fedora*)
                curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
                yum install -y nodejs
                ;;
            *Arch*)
                pacman -S --noconfirm nodejs npm
                ;;
            macOS)
                brew install node
                ;;
        esac
    fi
    
    log_success "系统依赖安装完成"
}

# 设置Python环境
setup_python_env() {
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
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."
    
    source venv/bin/activate
    
    # 检查requirements.txt文件是否存在
    if [ ! -f "backend/requirements.txt" ]; then
        log_error "找不到 backend/requirements.txt 文件"
        log_info "当前目录: $(pwd)"
        log_info "目录内容:"
        ls -la
        if [ -d "backend" ]; then
            log_info "backend目录内容:"
            ls -la backend/
        fi
        exit 1
    fi
    
    # 安装依赖
    pip install -r backend/requirements.txt
    
    log_success "Python依赖安装完成"
}

# 验证Python依赖
check_python_deps() {
    log_info "验证关键依赖..."
    
    source venv/bin/activate
    
    # 检查关键包
    python -c "import fastapi, uvicorn, sqlalchemy, pydantic" 2>/dev/null || {
        log_error "关键依赖验证失败"
        return 1
    }
    
    log_success "关键依赖验证成功"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    mkdir -p uploads
    mkdir -p logs
    mkdir -p backend/static
    mkdir -p backend/templates
    
    log_success "目录创建完成"
}

# 修复前端文件
fix_frontend_files() {
    log_info "修复前端文件..."
    
    # 确保所有必要的目录存在
    mkdir -p frontend/src/views/admin
    mkdir -p frontend/src/components/layout
    mkdir -p frontend/src/utils
    mkdir -p frontend/src/store
    mkdir -p frontend/src/styles
    
    # 创建缺失的样式文件
    if [ ! -f "frontend/src/styles/main.scss" ]; then
        cat > frontend/src/styles/main.scss << 'EOF'
// 全局样式
@import './global.scss';

// 主题变量
:root {
  --primary-color: #1677ff;
  --success-color: #52c41a;
  --warning-color: #faad14;
  --error-color: #ff4d4f;
  --text-color: #333;
  --text-color-secondary: #666;
  --border-color: #d9d9d9;
  --background-color: #f5f5f5;
}

// 响应式设计
@media (max-width: 768px) {
  .el-card {
    margin-bottom: 15px;
  }
  
  .el-form-item {
    margin-bottom: 15px;
  }
}
EOF
    fi
    
    log_success "前端文件修复完成"
}

# 安装前端依赖
install_frontend_deps() {
    log_info "安装前端依赖..."
    
    cd frontend
    
    # 安装依赖
    npm install
    
    log_success "前端依赖安装完成"
    cd ..
}

# 构建前端
build_frontend() {
    log_info "构建前端..."
    
    cd frontend
    
    # 快速修复依赖问题
    log_info "检查并修复依赖问题..."
    
    # 确保chart.js已安装
    if ! npm list chart.js > /dev/null 2>&1; then
        log_info "安装chart.js..."
        npm install chart.js@^4.4.0
    fi
    
    # 检查其他依赖
    local deps=("qrcode" "dayjs" "clipboard")
    for dep in "${deps[@]}"; do
        if ! npm list "$dep" > /dev/null 2>&1; then
            log_info "安装 $dep..."
            npm install "$dep"
        fi
    done
    
    # 修复logo问题
    log_info "检查并修复logo问题..."
    
    # 确保vite.svg存在
    if [ ! -f "public/vite.svg" ]; then
        log_info "创建vite.svg文件..."
        cat > public/vite.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class="iconify iconify--logos" width="31.88" height="32" preserveAspectRatio="xMidYMid meet" viewBox="0 0 256 257"><defs><linearGradient id="IconifyId1813088fe1fbc01fb466" x1="-.828%" x2="57.636%" y1="7.652%" y2="78.411%"><stop offset="0%" stop-color="#41D1FF"></stop><stop offset="100%" stop-color="#BD34FE"></stop></linearGradient><linearGradient id="IconifyId1813088fe1fbc01fb467" x1="43.376%" x2="50.316%" y1="2.242%" y2="89.03%"><stop offset="0%" stop-color="#FFEA83"></stop><stop offset="8.333%" stop-color="#FFDD35"></stop><stop offset="100%" stop-color="#FFA800"></stop></linearGradient></defs><path fill="url(#IconifyId1813088fe1fbc01fb466)" d="M255.153 37.938L134.897 252.976c-2.483 4.44-8.862 4.466-11.382.048L.875 37.958c-2.746-4.814 1.371-10.646 6.827-9.67l120.385 21.517a6.537 6.537 0 0 0 2.322-.004l117.867-21.483c5.438-.991 9.574 4.796 6.877 9.62Z"></path><path fill="url(#IconifyId1813088fe1fbc01fb467)" d="M185.432.063L96.44 17.501a3.268 3.268 0 0 0-2.634 3.014l-5.474 92.456a3.268 3.268 0 0 0 3.997 3.378l24.777-5.718c2.318-.535 4.413 1.507 3.936 3.838l-7.361 36.047c-.495 2.426 1.782 4.5 4.151 3.78l15.304-4.649c2.372-.72 4.652 1.36 4.15 3.788l-11.698 56.621c-.732 3.542 3.979 5.473 5.943 2.437l1.313-2.028l72.516-144.72c1.215-2.423-.88-5.186-3.54-4.672l-25.505 4.922c-2.396.462-4.435-1.77-3.759-4.114l16.646-57.705c.677-2.35-1.37-4.583-3.769-4.113Z"></path></svg>
EOF
    fi
    
    # 修复Vue文件中的logo引用
    if [ -f "src/components/layout/UserLayout.vue" ]; then
        sed -i 's|src="/logo.png"|src="/vite.svg"|g' src/components/layout/UserLayout.vue
    fi
    
    if [ -f "src/components/layout/AdminLayout.vue" ]; then
        sed -i 's|src="/logo.png"|src="/vite.svg"|g' src/components/layout/AdminLayout.vue
    fi
    
    # 修复SCSS导入和弃用警告问题
    log_info "修复SCSS导入和弃用警告问题..."
    
    # 更新global.scss中的map函数
    if [ -f "src/styles/global.scss" ]; then
        # 添加map模块导入
        if ! grep -q "@use \"sass:map\"" src/styles/global.scss; then
            sed -i '1i @use "sass:map";' src/styles/global.scss
        fi
        
        # 更新map函数语法
        sed -i 's/map-has-key/map.has-key/g' src/styles/global.scss
        sed -i 's/map-get/map.get/g' src/styles/global.scss
    fi
    
    # 修复UserLayout.vue中的SCSS导入
    if [ -f "src/components/layout/UserLayout.vue" ]; then
        if ! grep -q "@use '@/styles/global.scss'" src/components/layout/UserLayout.vue; then
            sed -i 's/@import '\''@\/styles\/global\.scss'\'';/@use '\''@\/styles\/global\.scss'\'' as *;/g' src/components/layout/UserLayout.vue
        fi
    fi
    
    # 修复AdminLayout.vue中的SCSS导入
    if [ -f "src/components/layout/AdminLayout.vue" ]; then
        if ! grep -q "@use '@/styles/global.scss'" src/components/layout/AdminLayout.vue; then
            sed -i 's/@import '\''@\/styles\/global\.scss'\'';/@use '\''@\/styles\/global\.scss'\'' as *;/g' src/components/layout/AdminLayout.vue
        fi
    fi
    
    # 修复useApi导出问题
    log_info "修复useApi导出问题..."
    
    # 确保api.js中导出了useApi函数
    if [ -f "src/utils/api.js" ]; then
        if ! grep -q "export const useApi" src/utils/api.js; then
            # 在api实例定义后添加useApi函数
            sed -i '/export const api = axios.create/a \n// useApi函数 - 用于在Vue组件中获取API实例\nexport const useApi = () => {\n  return api\n}' src/utils/api.js
        fi
    fi
    
    # 修复Pydantic导入问题
    log_info "修复Pydantic导入问题..."
    
    # 确保config.py中正确导入BaseSettings
    if [ -f "../backend/app/core/config.py" ]; then
        if ! grep -q "from pydantic_settings import BaseSettings" ../backend/app/core/config.py; then
            # 修复BaseSettings导入
            sed -i 's/from pydantic import AnyHttpUrl, BaseSettings, validator/from pydantic import AnyHttpUrl, validator\nfrom pydantic_settings import BaseSettings/' ../backend/app/core/config.py
        fi
    fi
    
    # 修复模型导入问题
    log_info "修复模型导入问题..."
    
    # 确保models/__init__.py中正确导入EmailTemplate
    if [ -f "../backend/app/models/__init__.py" ]; then
        if ! grep -q "from .notification import EmailTemplate" ../backend/app/models/__init__.py; then
            # 修复EmailTemplate导入
            sed -i 's/from .email import EmailQueue, EmailTemplate/from .email import EmailQueue\nfrom .notification import EmailTemplate/' ../backend/app/models/__init__.py
        fi
    fi
    
    # 确保schemas/notification.py中有Notification类
    if [ -f "../backend/app/schemas/notification.py" ]; then
        if ! grep -q "class Notification(NotificationInDB)" ../backend/app/schemas/notification.py; then
            # 添加Notification类作为NotificationInDB的别名
            cat >> ../backend/app/schemas/notification.py << 'EOF'

class Notification(NotificationInDB):
    """Notification schema alias for backward compatibility"""
    pass
EOF
        fi
    fi
    
    # 修复auth.py中的Token导入问题
    if [ -f "../backend/app/api/api_v1/endpoints/auth.py" ]; then
        if grep -q "from app.schemas.user import.*Token" ../backend/app/api/api_v1/endpoints/auth.py; then
            # 修复Token导入，从user.py改为common.py
            sed -i 's/from app.schemas.user import UserLogin, UserCreate, User, Token/from app.schemas.user import UserLogin, UserCreate, User/' ../backend/app/api/api_v1/endpoints/auth.py
            sed -i 's/from app.schemas.common import ResponseBase/from app.schemas.common import ResponseBase, Token/' ../backend/app/api/api_v1/endpoints/auth.py
        fi
    fi
    
    # 修复security.py中缺失的认证函数
    if [ -f "../backend/app/utils/security.py" ]; then
        # 检查是否已经添加了必要的导入
        if ! grep -q "from fastapi import Depends, HTTPException, status" ../backend/app/utils/security.py; then
            # 添加必要的导入
            sed -i '1s/^/from fastapi import Depends, HTTPException, status\n/' ../backend/app/utils/security.py
            sed -i '2s/^/from fastapi.security import OAuth2PasswordBearer\n/' ../backend/app/utils/security.py
            sed -i '3s/^/from sqlalchemy.orm import Session\n/' ../backend/app/utils/security.py
            sed -i '5s/^/from app.core.database import get_db\n/' ../backend/app/utils/security.py
            sed -i '6s/^/from app.models.user import User\n/' ../backend/app/utils/security.py
        fi
        
        # 检查是否已经添加了oauth2_scheme
        if ! grep -q "oauth2_scheme = OAuth2PasswordBearer" ../backend/app/utils/security.py; then
            # 在pwd_context定义后添加oauth2_scheme
            sed -i '/pwd_context = CryptContext/a\\n# OAuth2 密码承载者\noauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")' ../backend/app/utils/security.py
        fi
        
        # 检查是否已经添加了get_current_user函数
        if ! grep -q "def get_current_user" ../backend/app/utils/security.py; then
            # 在文件末尾添加get_current_user和get_current_admin_user函数
            cat >> ../backend/app/utils/security.py << 'EOF'

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前管理员用户"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
EOF
        fi
    fi
    
    # 修复email导入错误
    if [ -f "../backend/app/api/api_v1/endpoints/subscriptions.py" ]; then
        # 修复subscriptions.py中的email导入
        if grep -q "from app.utils.email import send_subscription_email" ../backend/app/api/api_v1/endpoints/subscriptions.py; then
            sed -i 's/from app.utils.email import send_subscription_email/from app.services.email import EmailService/' ../backend/app/api/api_v1/endpoints/subscriptions.py
        fi
    fi
    
    if [ -f "../backend/app/api/api_v1/endpoints/admin.py" ]; then
        # 修复admin.py中的email导入
        if grep -q "from app.utils.email import send_subscription_email" ../backend/app/api/api_v1/endpoints/admin.py; then
            sed -i 's/from app.utils.email import send_subscription_email/from app.services.email import EmailService/' ../backend/app/api/api_v1/endpoints/admin.py
        fi
    fi
    
    # 创建缺失的email schemas文件
    if [ ! -f "../backend/app/schemas/email.py" ]; then
        cat > ../backend/app/schemas/email.py << 'EOF'
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class EmailQueueBase(BaseModel):
    to_email: str
    subject: str
    content: str
    content_type: str = "plain"  # plain, html
    email_type: Optional[str] = None  # verification, reset, subscription, etc.
    attachments: Optional[List[Dict[str, Any]]] = None

class EmailQueueCreate(EmailQueueBase):
    pass

class EmailQueueUpdate(BaseModel):
    to_email: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    content_type: Optional[str] = None
    email_type: Optional[str] = None
    status: Optional[str] = None
    retry_count: Optional[int] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None

class EmailQueueInDB(EmailQueueBase):
    id: int
    status: str
    retry_count: int
    max_retries: int
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EmailQueue(EmailQueueInDB):
    pass
EOF
    fi
    
    # 更新schemas/__init__.py以包含email schemas
    if [ -f "../backend/app/schemas/__init__.py" ]; then
        if ! grep -q "from .email import" ../backend/app/schemas/__init__.py; then
            # 在notification导入后添加email导入
            sed -i '/from .notification import/a\\from .email import (\\n    EmailQueue, EmailQueueCreate, EmailQueueUpdate, EmailQueueInDB, EmailQueueBase\\n)' ../backend/app/schemas/__init__.py
        fi
        
        if ! grep -q "EmailQueue" ../backend/app/schemas/__init__.py; then
            # 在__all__列表中添加email schemas
            sed -i '/# Notification schemas/a\\    # Email schemas\\n    "EmailQueue", "EmailQueueCreate", "EmailQueueUpdate", "EmailQueueInDB", "EmailQueueBase",' ../backend/app/schemas/__init__.py
        fi
    fi
    
    # 更新EmailQueue模型以包含缺失的字段
    if [ -f "../backend/app/models/email.py" ]; then
        if ! grep -q "content_type = Column" ../backend/app/models/email.py; then
            # 在content字段后添加缺失的字段
            sed -i '/content = Column(Text, nullable=False)/a\\    content_type = Column(String(20), default="plain")  # plain, html\\n    email_type = Column(String(50), nullable=True)  # verification, reset, subscription, etc.\\n    attachments = Column(Text, nullable=True)  # JSON string for attachments' ../backend/app/models/email.py
        fi
    fi
    
    # 确保所有__init__.py文件存在
    echo "📁 确保__init__.py文件存在..."
    for dir in "../backend/app" "../backend/app/api" "../backend/app/api/api_v1" "../backend/app/api/api_v1/endpoints" "../backend/app/core" "../backend/app/models" "../backend/app/schemas" "../backend/app/services" "../backend/app/utils"; do
        if [ ! -f "$dir/__init__.py" ]; then
            echo "# Auto-generated __init__.py" > "$dir/__init__.py"
        fi
    done
    
    # 更新models/__init__.py
    if [ -f "../backend/app/models/__init__.py" ]; then
        if ! grep -q "from .email import EmailQueue" ../backend/app/models/__init__.py; then
            # 在notification导入后添加email导入
            sed -i '/from .notification import/a\\from .email import EmailQueue' ../backend/app/models/__init__.py
        fi
        
        if ! grep -q '"EmailQueue"' ../backend/app/models/__init__.py; then
            # 在__all__列表中添加EmailQueue
            sed -i 's/\]$/, "EmailQueue"]/' ../backend/app/models/__init__.py
        fi
    fi
    
    # 检查并修复其他可能的导入问题
    echo "🔍 检查其他可能的导入问题..."
    
    # 检查是否有缺失的依赖
    if ! grep -q "user-agents" ../backend/requirements.txt; then
        echo "user-agents" >> ../backend/requirements.txt
    fi
    
    # 检查是否有缺失的pydantic-settings
    if ! grep -q "pydantic-settings" ../backend/requirements.txt; then
        echo "pydantic-settings" >> ../backend/requirements.txt
    fi
    
    # 修复所有可能的依赖问题
    log_info "修复依赖问题..."
    
    # 确保backend requirements.txt包含所有必要的依赖
    if [ -f "../backend/requirements.txt" ]; then
        # 检查并添加缺失的依赖
        if ! grep -q "pydantic-settings" ../backend/requirements.txt; then
            echo "pydantic-settings" >> ../backend/requirements.txt
        fi
        
        if ! grep -q "user-agents" ../backend/requirements.txt; then
            echo "user-agents" >> ../backend/requirements.txt
        fi
    fi
    
    # 更新sass版本
    log_info "更新sass版本..."
    npm install sass@latest
    
    # 清理缓存
    log_info "清理缓存..."
    rm -rf node_modules/.cache
    rm -rf dist
    
    # 检查语法错误
    log_info "检查语法错误..."
    if npm run lint 2>/dev/null; then
        log_success "语法检查通过"
    else
        log_warning "发现语法问题，但继续构建..."
    fi
    
    # 构建
    log_info "开始构建..."
    npm run build
    
    log_success "前端构建完成"
    cd ..
}

# 配置数据库
configure_database() {
    log_info "配置数据库..."
    
    echo "请选择数据库类型:"
    echo "1) SQLite (推荐用于开发)"
    echo "2) MySQL"
    echo "3) PostgreSQL"
    read -p "请输入选择 (1-3): " db_choice
    
    case $db_choice in
        1)
            DATABASE_TYPE="sqlite"
            DATABASE_URL="sqlite:///./xboard.db"
            ;;
        2)
            DATABASE_TYPE="mysql"
            read -p "请输入MySQL主机 (默认: localhost): " mysql_host
            mysql_host=${mysql_host:-localhost}
            read -p "请输入MySQL端口 (默认: 3306): " mysql_port
            mysql_port=${mysql_port:-3306}
            read -p "请输入MySQL数据库名: " mysql_db
            read -p "请输入MySQL用户名: " mysql_user
            read -s -p "请输入MySQL密码: " mysql_password
            echo
            DATABASE_URL="mysql+pymysql://$mysql_user:$mysql_password@$mysql_host:$mysql_port/$mysql_db"
            ;;
        3)
            DATABASE_TYPE="postgresql"
            read -p "请输入PostgreSQL主机 (默认: localhost): " pg_host
            pg_host=${pg_host:-localhost}
            read -p "请输入PostgreSQL端口 (默认: 5432): " pg_port
            pg_port=${pg_port:-5432}
            read -p "请输入PostgreSQL数据库名: " pg_db
            read -p "请输入PostgreSQL用户名: " pg_user
            read -s -p "请输入PostgreSQL密码: " pg_password
            echo
            DATABASE_URL="postgresql://$pg_user:$pg_password@$pg_host:$pg_port/$pg_db"
            ;;
        *)
            log_error "无效选择"
            exit 1
            ;;
    esac
    
    log_success "数据库配置完成"
}

# 配置管理员账户
configure_admin() {
    log_info "配置管理员账户..."
    
    read -p "请输入管理员邮箱 (QQ邮箱): " admin_email
    read -s -p "请输入管理员密码: " admin_password
    echo
    read -s -p "请确认管理员密码: " admin_password_confirm
    echo
    
    if [ "$admin_password" != "$admin_password_confirm" ]; then
        log_error "密码不匹配"
        exit 1
    fi
    
    ADMIN_EMAIL=$admin_email
    ADMIN_PASSWORD=$admin_password
    
    log_success "管理员账户配置完成"
}

# 配置邮件服务（跳过）
configure_email() {
    log_info "跳过邮件服务配置..."
    
    # 使用默认值
    SMTP_HOST="smtp.qq.com"
    SMTP_PORT="587"
    EMAIL_USERNAME="your-email@qq.com"
    EMAIL_PASSWORD="your-smtp-password"
    SENDER_NAME="XBoard Modern"
    
    log_success "邮件服务配置完成（使用默认值）"
}

# 生成环境配置文件
generate_env_file() {
    log_info "生成环境配置文件..."
    
    cat > .env << EOF
# 数据库配置
DATABASE_TYPE=$DATABASE_TYPE
DATABASE_URL=$DATABASE_URL

# 应用配置
APP_NAME=XBoard Modern
APP_VERSION=1.0.0
DEBUG=false
SECRET_KEY=$(openssl rand -hex 32)

# 管理员配置
ADMIN_EMAIL=$ADMIN_EMAIL
ADMIN_PASSWORD=$ADMIN_PASSWORD

# 邮件配置
SMTP_HOST=$SMTP_HOST
SMTP_PORT=$SMTP_PORT
EMAIL_USERNAME=$EMAIL_USERNAME
EMAIL_PASSWORD=$EMAIL_PASSWORD
SENDER_NAME=$SENDER_NAME

# 缓存配置
CACHE_TYPE=memory
CACHE_DEFAULT_TIMEOUT=300

# 安全配置
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 文件上传配置
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/xboard.log

# 支付配置
ALIPAY_APP_ID=
ALIPAY_PRIVATE_KEY=
ALIPAY_PUBLIC_KEY=
WECHAT_APP_ID=
WECHAT_MCH_ID=
WECHAT_KEY=
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=

# 主题配置
DEFAULT_THEME=default
THEME_DIR=themes

# 通知配置
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_PUSH_NOTIFICATIONS=false

# 性能配置
WORKERS=4
MAX_CONNECTIONS=1000
EOF
    
    log_success "环境配置文件生成完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    source venv/bin/activate
    
    cd backend
    python -c "
from app.core.database import engine, Base
from app.models import User, Subscription, Device, Order, Package
Base.metadata.create_all(bind=engine)
print('数据库初始化完成')
"
    cd ..
    
    log_success "数据库初始化完成"
}

# 创建系统服务 (仅Linux)
create_systemd_service() {
    if [ "$OS_NAME" != "Linux" ]; then
        log_info "跳过系统服务创建 (非Linux系统)"
        return
    fi
    
    log_info "创建系统服务..."
    
    cat > /etc/systemd/system/xboard-backend.service << EOF
[Unit]
Description=XBoard Backend Service
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_PATH
Environment=PATH=$PROJECT_PATH/venv/bin
ExecStart=$PROJECT_PATH/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable xboard-backend
    
    log_success "系统服务创建完成"
}

# 配置Nginx (仅Linux)
configure_nginx() {
    if [ "$OS_NAME" != "Linux" ]; then
        log_info "跳过Nginx配置 (非Linux系统)"
        return
    fi
    
    log_info "配置Nginx..."
    
    cat > /etc/nginx/sites-available/xboard << EOF
server {
    listen 80;
    server_name _;
    
    # 前端静态文件
    location / {
        root $PROJECT_PATH/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 静态文件
    location /static/ {
        alias $PROJECT_PATH/backend/static/;
    }
    
    # 上传文件
    location /uploads/ {
        alias $PROJECT_PATH/uploads/;
    }
}
EOF
    
    # 启用站点
    ln -sf /etc/nginx/sites-available/xboard /etc/nginx/sites-enabled/
    
    # 验证配置
    nginx -t
    
    log_success "Nginx配置完成"
}

# 启动服务 (仅Linux)
start_services() {
    if [ "$OS_NAME" != "Linux" ]; then
        log_info "跳过服务启动 (非Linux系统)"
        return
    fi
    
    log_info "启动服务..."
    
    systemctl start xboard-backend
    
    log_success "服务启动完成"
}

# 显示安装结果
show_result() {
    log_success "安装完成！"
    echo
    echo "=== 安装信息 ==="
    echo "项目路径: $PROJECT_PATH"
    echo "数据库类型: $DATABASE_TYPE"
    echo "管理员邮箱: $ADMIN_EMAIL"
    echo
    echo "=== 访问地址 ==="
    echo "前端: http://localhost"
    echo "API文档: http://localhost/api/docs"
    echo
    echo "=== 管理命令 ==="
    echo "启动后端: systemctl start xboard-backend"
    echo "停止后端: systemctl stop xboard-backend"
    echo "查看状态: systemctl status xboard-backend"
    echo "查看日志: journalctl -u xboard-backend -f"
    echo
    echo "=== 宝塔面板用户注意 ==="
    echo "1. 请确保Nginx配置正确"
    echo "2. 如需重启Nginx，请在宝塔面板中操作"
    echo "3. 后端服务已设置为开机自启"
    echo
    echo "=== 开发模式启动 ==="
    echo "cd $PROJECT_PATH"
    echo "source venv/bin/activate"
    echo "cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
}

# 主安装流程
main() {
    echo "=================================="
    echo "    XBoard Modern 安装程序"
    echo "=================================="
    echo
    
    # 获取项目路径
    get_project_path "$1"
    
    # 检测环境
    detect_os_and_arch
    
    # 安装系统依赖
    install_system_deps
    
    # 设置Python环境
    setup_python_env
    
    # 安装Python依赖
    install_python_deps
    
    # 验证依赖
    check_python_deps
    
    # 创建目录
    create_directories
    
    # 修复前端文件
    fix_frontend_files
    
    # 安装前端依赖
    install_frontend_deps
    
    # 构建前端
    build_frontend
    
    # 配置数据库
    configure_database
    
    # 配置管理员
    configure_admin
    
    # 配置邮件
    configure_email
    
    # 生成环境文件
    generate_env_file
    
    # 初始化数据库
    init_database
    
    # 创建系统服务
    create_systemd_service
    
    # 配置Nginx
    configure_nginx
    
    # 启动服务
    start_services
    
    # 显示结果
    show_result
}

# 运行主程序
main "$@" 