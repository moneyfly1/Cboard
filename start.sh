#!/bin/bash

# XBoard Modern 启动脚本

echo "🚀 启动 XBoard Modern..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p uploads
mkdir -p nginx/ssl

# 构建并启动服务
echo "🔨 构建并启动服务..."
docker-compose up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 显示访问信息
echo ""
echo "✅ XBoard Modern 启动完成！"
echo ""
echo "🌐 访问地址："
echo "   前端: http://localhost:3000"
echo "   后端API: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "📊 服务状态："
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "📝 日志查看："
echo "   docker-compose logs -f backend    # 后端日志"
echo "   docker-compose logs -f frontend   # 前端日志"
echo "   docker-compose logs -f nginx      # Nginx日志"
echo ""
echo "🛑 停止服务："
echo "   docker-compose down"
echo "" 