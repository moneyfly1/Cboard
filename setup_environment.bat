@echo off
REM XBoard 环境设置脚本 (Windows版本)
REM 此脚本将帮助Windows开发者快速设置开发环境

echo 🚀 开始设置 XBoard 开发环境...

REM 检查 Python 版本
echo 📋 检查 Python 版本...
python --version

REM 创建虚拟环境
echo 🔧 创建虚拟环境...
python -m venv venv

REM 激活虚拟环境
echo ✅ 激活虚拟环境...
call venv\Scripts\activate.bat

REM 升级 pip
echo ⬆️ 升级 pip...
python -m pip install --upgrade pip

REM 安装依赖
echo 📦 安装 Python 依赖...
pip install -r requirements.txt

REM 安装前端依赖
echo 🌐 安装前端依赖...
cd frontend
npm install
cd ..

REM 创建环境配置文件
echo ⚙️ 创建环境配置文件...
if not exist .env (
    copy env.example .env
    echo 📝 已创建 .env 文件，请根据你的配置修改其中的值
)

echo.
echo 🎉 环境设置完成！
echo.
echo 📋 接下来的步骤：
echo 1. 修改 .env 文件中的配置（数据库、邮件等）
echo 2. 运行数据库迁移: python -m alembic upgrade head
echo 3. 启动后端服务: python -m uvicorn main:app --reload
echo 4. 启动前端服务: cd frontend ^&^& npm run dev
echo.
echo 🔗 相关文档：
echo - 后端API文档: http://localhost:8000/docs
echo - 前端应用: http://localhost:5173
echo.
echo 💡 提示：每次开发前记得激活虚拟环境: venv\Scripts\activate.bat
pause
