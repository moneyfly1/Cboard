#!/bin/bash

# XBoard 完整安装脚本
# 适用于 macOS 和 Linux 系统

set -e

echo "🚀 开始安装 XBoard 系统..."

# 检查系统要求
check_requirements() {
    echo "📋 检查系统要求..."
    
    # 检查 Python 版本
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 未安装，请先安装 Python3.8+"
        exit 1
    fi
    
    # 检查 Node.js 版本
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js 未安装，请先安装 Node.js 16+"
        exit 1
    fi
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        echo "❌ npm 未安装，请先安装 npm"
        exit 1
    fi
    
    echo "✅ 系统要求检查通过"
}

# 创建虚拟环境
setup_python_env() {
    echo "🐍 设置 Python 虚拟环境..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Python 虚拟环境创建成功"
    else
        echo "✅ Python 虚拟环境已存在"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ Python 依赖安装完成"
}

# 设置前端环境
setup_frontend() {
    echo "⚛️ 设置前端环境..."
    
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        npm install
        echo "✅ 前端依赖安装完成"
    else
        echo "✅ 前端依赖已存在"
    fi
    
    cd ..
}

# 设置数据库
setup_database() {
    echo "🗄️ 设置数据库..."
    
    if [ ! -f "xboard.db" ]; then
        echo "📝 创建数据库..."
        sqlite3 xboard.db < database_setup.sql
        
        # 插入测试数据
        echo "📊 插入测试数据..."
        sqlite3 xboard.db "
        INSERT INTO packages (name, price, duration_days, device_limit, description, is_active, sort_order) VALUES 
        ('基础套餐', 19.9, 30, 3, '适合个人用户的基础订阅套餐', 1, 1),
        ('高级套餐', 39.9, 30, 5, '适合重度用户的完整功能套餐', 1, 2),
        ('企业套餐', 99.9, 30, 10, '适合团队使用的企业级套餐', 1, 3);
        
        INSERT INTO users (username, email, hashed_password, is_active, is_verified, is_admin) VALUES 
        ('admin', 'admin@example.com', '1223e85719a0244c4b316e41c8215ac0:9afd583e7908b3c47bb5c45dd8efb2607e17aefbf77482dcf58705cb2c6d3358', 1, 1, 1),
        ('user1', 'user1@example.com', '86217f432b178833c65d05da10b8a253:1f163c48b56f5a617c8a1ef28963bb7d3fd62cd737621bf046d98e449663f0fd', 1, 1, 0),
        ('user2', 'user2@example.com', '86217f432b178833c65d05da10b8a253:1f163c48b56f5a617c8a1ef28963bb7d3fd62cd737621bf046d98e449663f0fd', 1, 1, 0),
        ('user3', 'user3@example.com', '86217f432b178833c65d05da10b8a253:1f163c48b56f5a617c8a1ef28963bb7d3fd62cd737621bf046d98e449663f0fd', 1, 1, 0);
        
        ALTER TABLE subscriptions ADD COLUMN package_id INTEGER;
        ALTER TABLE packages ADD COLUMN bandwidth_limit INTEGER NULL;
        ALTER TABLE packages ADD COLUMN sort_order INTEGER DEFAULT 1;
        
        INSERT INTO subscriptions (user_id, package_id, status, start_date, end_date) VALUES 
        (2, 1, 'active', datetime('now'), datetime('now', '+30 days')),
        (3, 2, 'active', datetime('now'), datetime('now', '+30 days')),
        (4, 3, 'active', datetime('now'), datetime('now', '+30 days'));
        
        INSERT INTO orders (user_id, package_id, order_no, amount, status, payment_method_name, payment_time) VALUES 
        (2, 1, 'ORD001', 19.9, 'paid', '支付宝', datetime('now')),
        (3, 2, 'ORD002', 39.9, 'paid', '微信支付', datetime('now')),
        (4, 3, 'ORD003', 99.9, 'paid', '支付宝', datetime('now'));
        "
        echo "✅ 数据库和测试数据设置完成"
    else
        echo "✅ 数据库已存在"
    fi
}

# 创建启动脚本
create_startup_scripts() {
    echo "📜 创建启动脚本..."
    
    # 启动后端脚本
    cat > start_backend.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m uvicorn main:app --host 127.0.0.1 --port 8000
EOF
    
    # 启动前端脚本
    cat > start_frontend.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/frontend"
npm run dev
EOF
    
    # 启动全部脚本
    cat > start_all.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

echo "🚀 启动 XBoard 系统..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 ./install.sh"
    exit 1
fi

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ 前端依赖不存在，请先运行 ./install.sh"
    exit 1
fi

# 启动后端
echo "🔧 启动后端服务..."
source venv/bin/activate
nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
echo $! > .backend.pid

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 5

# 检查后端健康状态
if curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
    exit 1
fi

# 启动前端
echo "🎨 启动前端服务..."
cd frontend
nohup npm run dev > ../frontend.log 2>&1 &
echo $! > ../.frontend.pid
cd ..

echo "🎉 XBoard 系统启动完成！"
echo "📱 前端地址: http://localhost:5173"
echo "🔧 后端地址: http://127.0.0.1:8000"
echo "📊 后端日志: backend.log"
echo "🎨 前端日志: frontend.log"
echo ""
echo "💡 使用 ./stop_all.sh 停止所有服务"
EOF
    
    # 停止全部脚本
    cat > stop_all.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

echo "🛑 停止 XBoard 系统..."

# 停止后端
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo "✅ 后端服务已停止"
    fi
    rm -f .backend.pid
fi

# 停止前端
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo "✅ 前端服务已停止"
    fi
    rm -f .frontend.pid
fi

# 清理进程
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true

echo "🎉 所有服务已停止"
EOF
    
    chmod +x start_backend.sh start_frontend.sh start_all.sh stop_all.sh
    echo "✅ 启动脚本创建完成"
}

# 显示安装完成信息
show_completion_info() {
    echo ""
    echo "🎉 XBoard 系统安装完成！"
    echo ""
    echo "📋 安装内容："
    echo "   ✅ Python 虚拟环境和依赖"
    echo "   ✅ 前端依赖"
    echo "   ✅ 数据库和测试数据"
    echo "   ✅ 启动脚本"
    echo ""
    echo "🚀 启动系统："
    echo "   ./start_all.sh          # 启动所有服务"
    echo "   ./start_backend.sh      # 仅启动后端"
    echo "   ./start_frontend.sh     # 仅启动前端"
    echo ""
    echo "🛑 停止系统："
    echo "   ./stop_all.sh           # 停止所有服务"
    echo ""
    echo "📱 访问地址："
    echo "   前端: http://localhost:5173"
    echo "   后端: http://127.0.0.1:8000"
    echo ""
    echo "🔐 测试账户："
    echo "   管理员: admin / 123456"
    echo "   普通用户: user1 / 123456"
    echo ""
    echo "📚 更多信息请查看 README.md"
}

# 主安装流程
main() {
    check_requirements
    setup_python_env
    setup_frontend
    setup_database
    create_startup_scripts
    show_completion_info
}

# 运行安装
main
