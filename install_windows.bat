@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==================================
echo    XBoard Modern 安装程序 (Windows)
echo ==================================
echo.

:: 设置项目路径
set "PROJECT_PATH=%~dp0.."
cd /d "%PROJECT_PATH%"

echo [INFO] 项目路径: %PROJECT_PATH%

:: 检查Python
echo [INFO] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

:: 检查Node.js
echo [INFO] 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到Node.js，请先安装Node.js 16+
    pause
    exit /b 1
)

:: 创建虚拟环境
echo [INFO] 创建Python虚拟环境...
if not exist "venv" (
    python -m venv venv
    echo [✓] 虚拟环境创建成功
) else (
    echo [INFO] 虚拟环境已存在
)

:: 激活虚拟环境
echo [INFO] 激活虚拟环境...
call venv\Scripts\activate.bat

:: 升级pip
echo [INFO] 升级pip...
python -m pip install --upgrade pip

:: 安装Python依赖
echo [INFO] 安装Python依赖...
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo [ERROR] Python依赖安装失败
    pause
    exit /b 1
)
echo [✓] Python依赖安装完成

:: 创建必要目录
echo [INFO] 创建必要目录...
if not exist "uploads" mkdir uploads
if not exist "logs" mkdir logs
if not exist "backend\static" mkdir backend\static
if not exist "backend\templates" mkdir backend\templates
echo [✓] 目录创建完成

:: 安装前端依赖
echo [INFO] 安装前端依赖...
cd frontend
npm install
if errorlevel 1 (
    echo [ERROR] 前端依赖安装失败
    pause
    exit /b 1
)
echo [✓] 前端依赖安装完成

:: 构建前端
echo [INFO] 构建前端...
npm run build
if errorlevel 1 (
    echo [ERROR] 前端构建失败
    pause
    exit /b 1
)
echo [✓] 前端构建完成

cd ..

:: 配置数据库
echo [INFO] 配置数据库...
set /p "db_choice=请选择数据库类型 (1:SQLite 2:MySQL 3:PostgreSQL): "
if "%db_choice%"=="1" (
    set "DATABASE_TYPE=sqlite"
    set "DATABASE_URL=sqlite:///./xboard.db"
) else if "%db_choice%"=="2" (
    set "DATABASE_TYPE=mysql"
    set /p "mysql_host=请输入MySQL主机 (默认: localhost): "
    if "!mysql_host!"=="" set "mysql_host=localhost"
    set /p "mysql_port=请输入MySQL端口 (默认: 3306): "
    if "!mysql_port!"=="" set "mysql_port=3306"
    set /p "mysql_db=请输入MySQL数据库名: "
    set /p "mysql_user=请输入MySQL用户名: "
    set /p "mysql_password=请输入MySQL密码: "
    set "DATABASE_URL=mysql+pymysql://!mysql_user!:!mysql_password!@!mysql_host!:!mysql_port!/!mysql_db!"
) else if "%db_choice%"=="3" (
    set "DATABASE_TYPE=postgresql"
    set /p "pg_host=请输入PostgreSQL主机 (默认: localhost): "
    if "!pg_host!"=="" set "pg_host=localhost"
    set /p "pg_port=请输入PostgreSQL端口 (默认: 5432): "
    if "!pg_port!"=="" set "pg_port=5432"
    set /p "pg_db=请输入PostgreSQL数据库名: "
    set /p "pg_user=请输入PostgreSQL用户名: "
    set /p "pg_password=请输入PostgreSQL密码: "
    set "DATABASE_URL=postgresql://!pg_user!:!pg_password!@!pg_host!:!pg_port!/!pg_db!"
) else (
    echo [ERROR] 无效选择
    pause
    exit /b 1
)

:: 配置管理员账户
echo [INFO] 配置管理员账户...
set /p "admin_email=请输入管理员邮箱 (QQ邮箱): "
set /p "admin_password=请输入管理员密码: "
set /p "admin_password_confirm=请确认管理员密码: "
if not "%admin_password%"=="%admin_password_confirm%" (
    echo [ERROR] 密码不匹配
    pause
    exit /b 1
)

:: 配置邮件服务
echo [INFO] 配置邮件服务...
set /p "smtp_host=请输入SMTP服务器 (例如: smtp.qq.com): "
set /p "smtp_port=请输入SMTP端口 (默认: 587): "
if "!smtp_port!"=="" set "smtp_port=587"
set /p "email_username=请输入邮箱地址: "
set /p "email_password=请输入邮箱密码/授权码: "
set /p "sender_name=请输入发件人名称: "

:: 生成环境配置文件
echo [INFO] 生成环境配置文件...
(
echo # 数据库配置
echo DATABASE_TYPE=%DATABASE_TYPE%
echo DATABASE_URL=%DATABASE_URL%
echo.
echo # 应用配置
echo APP_NAME=XBoard Modern
echo APP_VERSION=1.0.0
echo DEBUG=false
echo SECRET_KEY=your-secret-key-here
echo.
echo # 管理员配置
echo ADMIN_EMAIL=%admin_email%
echo ADMIN_PASSWORD=%admin_password%
echo.
echo # 邮件配置
echo SMTP_HOST=%smtp_host%
echo SMTP_PORT=%smtp_port%
echo EMAIL_USERNAME=%email_username%
echo EMAIL_PASSWORD=%email_password%
echo SENDER_NAME=%sender_name%
echo.
echo # 缓存配置
echo CACHE_TYPE=memory
echo CACHE_DEFAULT_TIMEOUT=300
echo.
echo # 安全配置
echo CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
echo JWT_SECRET_KEY=your-jwt-secret-key-here
echo JWT_ALGORITHM=HS256
echo ACCESS_TOKEN_EXPIRE_MINUTES=30
echo REFRESH_TOKEN_EXPIRE_DAYS=7
echo.
echo # 文件上传配置
echo UPLOAD_DIR=uploads
echo MAX_FILE_SIZE=10485760
echo.
echo # 日志配置
echo LOG_LEVEL=INFO
echo LOG_FILE=logs/xboard.log
echo.
echo # 支付配置
echo ALIPAY_APP_ID=
echo ALIPAY_PRIVATE_KEY=
echo ALIPAY_PUBLIC_KEY=
echo WECHAT_APP_ID=
echo WECHAT_MCH_ID=
echo WECHAT_KEY=
echo PAYPAL_CLIENT_ID=
echo PAYPAL_CLIENT_SECRET=
echo.
echo # 主题配置
echo DEFAULT_THEME=default
echo THEME_DIR=themes
echo.
echo # 通知配置
echo ENABLE_EMAIL_NOTIFICATIONS=true
echo ENABLE_PUSH_NOTIFICATIONS=false
echo.
echo # 性能配置
echo WORKERS=4
echo MAX_CONNECTIONS=1000
) > .env

echo [✓] 环境配置文件生成完成

:: 初始化数据库
echo [INFO] 初始化数据库...
cd backend
python -c "from app.core.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine); print('数据库初始化完成')"
if errorlevel 1 (
    echo [ERROR] 数据库初始化失败
    pause
    exit /b 1
)
cd ..
echo [✓] 数据库初始化完成

:: 显示安装结果
echo.
echo [✓] 安装完成！
echo.
echo === 安装信息 ===
echo 项目路径: %PROJECT_PATH%
echo 数据库类型: %DATABASE_TYPE%
echo 管理员邮箱: %admin_email%
echo.
echo === 启动命令 ===
echo 开发模式启动:
echo cd %PROJECT_PATH%
echo venv\Scripts\activate.bat
echo cd backend
echo python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
echo.
echo === 访问地址 ===
echo 前端: http://localhost:3000
echo API文档: http://localhost:8000/docs
echo.
echo === 注意事项 ===
echo 1. 请确保防火墙允许端口8000和3000
echo 2. 生产环境建议使用Nginx反向代理
echo 3. 请及时修改默认密码和密钥
echo.
pause 