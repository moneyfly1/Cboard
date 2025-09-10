# VPS部署问题解决指南

## 🚨 常见部署问题及解决方案

### 1. 系统环境问题

#### 问题1: Python版本不兼容
**症状**: 安装依赖时出现版本错误
```bash
ERROR: Package 'xxx' requires a different Python: 3.6.9 not in '>=3.8'
```

**解决方案**:
```bash
# 检查Python版本
python3 --version

# 如果版本过低，安装Python 3.9
# Ubuntu/Debian
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-dev

# CentOS/RHEL
sudo yum install python39 python39-devel python39-pip
```

#### 问题2: 缺少编译工具
**症状**: 安装某些Python包时出现编译错误
```bash
error: Microsoft Visual C++ 14.0 is required
```

**解决方案**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install build-essential python3-dev libffi-dev libssl-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel libffi-devel openssl-devel
```

### 2. 前端构建问题

#### 问题1: Node.js版本不兼容
**症状**: npm install 或 npm run build 失败
```bash
error: The engine "node" is incompatible with this module
```

**解决方案**:
```bash
# 安装Node.js 16.x
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt-get install -y nodejs

# 或使用nvm管理Node.js版本
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 16
nvm use 16
```

#### 问题2: 内存不足导致构建失败
**症状**: 构建过程中出现内存错误
```bash
FATAL ERROR: Ineffective mark-compacts near heap limit Allocation failed
```

**解决方案**:
```bash
# 增加Node.js内存限制
export NODE_OPTIONS="--max-old-space-size=4096"

# 或在package.json中修改构建脚本
"build": "NODE_OPTIONS='--max-old-space-size=4096' vite build"
```

#### 问题3: 网络问题导致依赖下载失败
**症状**: npm install 超时或失败
```bash
npm ERR! network timeout at: https://registry.npmjs.org/xxx
```

**解决方案**:
```bash
# 使用国内镜像源
npm config set registry https://registry.npmmirror.com

# 或使用cnpm
npm install -g cnpm --registry=https://registry.npmmirror.com
cnpm install
```

#### 问题4: 权限问题
**症状**: 构建时出现权限错误
```bash
EACCES: permission denied, mkdir '/root/.npm'
```

**解决方案**:
```bash
# 修复npm权限
sudo chown -R $(whoami) ~/.npm
sudo chown -R $(whoami) /usr/local/lib/node_modules

# 或使用nvm避免权限问题
```

### 3. 后端构建问题

#### 问题1: 数据库连接问题
**症状**: 启动时数据库连接失败
```bash
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file
```

**解决方案**:
```bash
# 检查数据库文件权限
ls -la xboard.db
chmod 664 xboard.db
chown www:www xboard.db

# 或使用MySQL/PostgreSQL
# 安装MySQL
sudo apt install mysql-server
sudo mysql_secure_installation

# 创建数据库
mysql -u root -p
CREATE DATABASE xboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'xboard'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON xboard.* TO 'xboard'@'localhost';
FLUSH PRIVILEGES;
```

#### 问题2: 端口占用问题
**症状**: 启动时端口被占用
```bash
OSError: [Errno 98] Address already in use
```

**解决方案**:
```bash
# 查看端口占用
netstat -tlnp | grep :8000
lsof -i :8000

# 杀死占用进程
kill -9 PID

# 或修改端口
# 在.env文件中修改PORT=8001
```

#### 问题3: 依赖安装失败
**症状**: pip install 失败
```bash
ERROR: Failed building wheel for xxx
```

**解决方案**:
```bash
# 升级pip
pip install --upgrade pip

# 安装系统依赖
sudo apt install python3-dev libffi-dev libssl-dev

# 使用预编译包
pip install --only-binary=all -r requirements.txt

# 或使用conda
conda install -c conda-forge fastapi uvicorn
```

### 4. 宝塔面板相关问题

#### 问题1: Python项目管理器无法启动
**症状**: 在宝塔面板中启动Python项目失败

**解决方案**:
```bash
# 检查Python路径
which python3
which pip3

# 在宝塔面板中正确配置Python路径
# 项目路径: /www/wwwroot/xboard
# Python版本: 3.9
# 启动方式: uvicorn
# 启动文件: main.py
# 端口: 8000
```

#### 问题2: PM2管理器问题
**症状**: PM2无法管理Node.js项目

**解决方案**:
```bash
# 安装PM2
npm install -g pm2

# 创建PM2配置文件
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'xboard-backend',
    script: 'main.py',
    cwd: '/www/wwwroot/xboard',
    interpreter: '/www/wwwroot/xboard/venv/bin/python',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    }
  }]
};
EOF

# 启动项目
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 5. Nginx配置问题

#### 问题1: 反向代理配置错误
**症状**: 前端无法访问后端API

**解决方案**:
```nginx
# 正确的Nginx配置
server {
    listen 80;
    server_name yourdomain.com;
    root /www/wwwroot/xboard/frontend/dist;
    index index.html;

    # 前端静态文件
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 解决跨域问题
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods 'GET, POST, PUT, DELETE, OPTIONS';
        add_header Access-Control-Allow-Headers 'DNT,X-Mx-ReqToken,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization';
        
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
}
```

#### 问题2: SSL证书问题
**症状**: HTTPS无法正常工作

**解决方案**:
```bash
# 在宝塔面板中申请Let's Encrypt证书
# 或手动配置SSL
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/nginx-selfsigned.key \
    -out /etc/ssl/certs/nginx-selfsigned.crt
```

### 6. 权限问题

#### 问题1: 文件权限错误
**症状**: 无法读取或写入文件

**解决方案**:
```bash
# 设置正确的文件权限
chown -R www:www /www/wwwroot/xboard
chmod -R 755 /www/wwwroot/xboard
chmod 664 /www/wwwroot/xboard/xboard.db
chmod 755 /www/wwwroot/xboard/venv/bin/python
```

#### 问题2: 上传目录权限
**症状**: 无法上传文件

**解决方案**:
```bash
# 设置上传目录权限
chown -R www:www /www/wwwroot/xboard/uploads
chmod -R 755 /www/wwwroot/xboard/uploads
```

### 7. 性能优化问题

#### 问题1: 内存不足
**症状**: 服务运行缓慢或崩溃

**解决方案**:
```bash
# 增加交换空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 优化PM2配置
pm2 start ecosystem.config.js --max-memory-restart 1G
```

#### 问题2: 数据库性能问题
**症状**: 数据库查询缓慢

**解决方案**:
```bash
# 优化SQLite配置
# 在.env文件中添加
DATABASE_URL=sqlite:///./xboard.db?check_same_thread=False&timeout=30

# 或迁移到MySQL/PostgreSQL
```

## 🛠️ 预防措施

### 1. 部署前检查清单
- [ ] 系统版本兼容性
- [ ] Python版本 >= 3.8
- [ ] Node.js版本 >= 16
- [ ] 内存 >= 2GB
- [ ] 磁盘空间 >= 20GB
- [ ] 网络连接正常

### 2. 环境准备脚本
```bash
#!/bin/bash
# 环境检查脚本
echo "检查系统环境..."

# 检查Python
python3 --version
if [ $? -ne 0 ]; then
    echo "Python3未安装"
    exit 1
fi

# 检查Node.js
node --version
if [ $? -ne 0 ]; then
    echo "Node.js未安装"
    exit 1
fi

# 检查内存
free -h
if [ $(free -m | awk 'NR==2{printf "%.0f", $3*100/$2}') -gt 80 ]; then
    echo "内存使用率过高"
    exit 1
fi

echo "环境检查通过"
```

### 3. 自动化部署脚本
```bash
#!/bin/bash
# 自动化部署脚本
set -e

echo "开始部署XBoard项目..."

# 1. 环境检查
echo "检查环境..."
python3 --version
node --version

# 2. 安装依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 3. 构建前端
echo "构建前端..."
cd frontend
npm install
npm run build
cd ..

# 4. 初始化数据库
echo "初始化数据库..."
python -c "from app.core.database import init_database; init_database()"

# 5. 设置权限
echo "设置权限..."
chown -R www:www /www/wwwroot/xboard
chmod -R 755 /www/wwwroot/xboard

# 6. 启动服务
echo "启动服务..."
pm2 start ecosystem.config.js
pm2 save

echo "部署完成！"
```

## 📞 技术支持

如果遇到其他问题，可以：

1. 查看系统日志：`journalctl -u nginx`
2. 查看应用日志：`pm2 logs`
3. 检查错误日志：`tail -f /var/log/nginx/error.log`
4. 联系技术支持

---

**注意**: 请根据实际情况调整配置参数，确保生产环境的安全性。
