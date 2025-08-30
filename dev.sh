#!/bin/bash

# XBoard Modern 开发环境启动脚本

echo "🚀 启动 XBoard Modern 开发环境..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装，请先安装 Python 3"
    exit 1
fi

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js"
    exit 1
fi

# 启动后端服务
echo "🐍 启动后端服务..."
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装Python依赖..."
pip install -r requirements.txt

# 启动后端服务
echo "🚀 启动后端API服务..."
python main.py &
BACKEND_PID=$!

cd ..

# 启动前端服务
echo "⚛️ 启动前端服务..."
cd frontend

# 安装依赖
echo "📦 安装Node.js依赖..."
npm install

# 启动前端服务
echo "🚀 启动前端开发服务器..."
npm run dev &
FRONTEND_PID=$!

cd ..

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 显示访问信息
echo ""
echo "✅ XBoard Modern 开发环境启动完成！"
echo ""
echo "🌐 访问地址："
echo "   前端: http://localhost:3000"
echo "   后端API: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "📝 日志查看："
echo "   后端日志: 查看后端终端输出"
echo "   前端日志: 查看前端终端输出"
echo ""
echo "🛑 停止服务："
echo "   按 Ctrl+C 停止所有服务"
echo ""

# 等待用户中断
trap "echo '🛑 停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait 