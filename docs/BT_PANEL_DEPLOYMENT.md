# 宝塔面板部署指南

## 📋 部署前准备

### 1. 服务器要求
- **操作系统**: CentOS 7+ / Ubuntu 18+ / Debian 9+
- **内存**: 最少 2GB，推荐 4GB+
- **硬盘**: 最少 20GB 可用空间
- **网络**: 公网IP，开放80/443端口
- **域名**: 已解析到服务器IP（可选，但推荐）

### 2. 软件要求
- **Python**: 3.8+
- **Node.js**: 16+
- **MySQL**: 5.7+ 或 MariaDB 10.3+
- **Redis**: 5.0+
- **Nginx**: 1.18+

## 🚀 自动安装（推荐）

### 1. 下载项目
```bash
# 进入服务器
ssh root@your-server-ip

# 下载项目
cd /www/wwwroot
git clone https://github.com/your-repo/xboard-modern.git
cd xboard-modern
```

### 2. 运行安装脚本
```bash
# 给脚本执行权限
chmod +x install_bt.sh

# 运行安装脚本
./install_bt.sh
```

### 3. 配置环境变量
```bash
# 编辑环境变量文件
nano .env

# 主要配置项：
# DATABASE_URL=mysql+pymysql://username:password@localhost:3306/xboard_db
# SMTP_USERNAME=your-email@qq.com
# SMTP_PASSWORD=your-email-password
# SECRET_KEY=your-super-secret-jwt-key
```

### 4. 初始化数据库
```bash
# 运行数据库初始化脚本
python3 init_database.py
```

## 🔧 手动安装

### 1. 安装宝塔面板
```bash
# CentOS
yum install -y wget && wget -O install.sh http://download.bt.cn/install/install_6.0.sh && sh install.sh

# Ubuntu/Debian
wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh
```

### 2. 安装LNMP环境
在宝塔面板中安装：
- **Nginx**: 1.18+
- **MySQL**: 5.7+
- **PHP**: 7.4+（可选）
- **Redis**: 5.0+

### 3. 安装Python环境
```bash
# 安装Python3
yum install -y python3 python3-pip python3-devel

# 或 Ubuntu/Debian
apt install -y python3 python3-pip python3-dev
```

### 4. 安装Node.js
```bash
# 使用NodeSource安装LTS版本
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
yum install -y nodejs  # CentOS
# 或
apt install -y nodejs  # Ubuntu/Debian
```

### 5. 部署项目
```bash
# 创建项目目录
mkdir -p /www/wwwroot/xboard-modern
cd /www/wwwroot/xboard-modern

# 上传项目文件（使用FTP或Git）
# 或直接克隆
git clone https://github.com/your-repo/xboard-modern.git .

# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install -r backend/requirements.txt

# 安装前端依赖
cd frontend
npm install
npm run build
cd ..
```

### 6. 配置数据库
在宝塔面板中：
1. 进入 **数据库** 管理
2. 创建MySQL数据库：`xboard_db`
3. 记录数据库用户名和密码
4. 配置环境变量中的数据库连接

### 7. 配置环境变量
```bash
# 复制环境变量文件
cp env.example .env

# 编辑配置文件
nano .env

# 主要配置：
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/xboard_db
SMTP_USERNAME=your-email@qq.com
SMTP_PASSWORD=your-email-password
SECRET_KEY=your-super-secret-jwt-key-change-this
```

### 8. 初始化数据库
```bash
# 激活虚拟环境
source venv/bin/activate

# 运行初始化脚本
python3 init_database.py
```

### 9. 创建系统服务
```bash
# 创建服务文件
cat > /etc/systemd/system/xboard-backend.service << EOF
[Unit]
Description=XBoard Backend Service
After=network.target

[Service]
Type=simple
User=www
Group=www
WorkingDirectory=/www/wwwroot/xboard-modern
Environment=PATH=/www/wwwroot/xboard-modern/venv/bin
ExecStart=/www/wwwroot/xboard-modern/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
systemctl daemon-reload
systemctl enable xboard-backend
systemctl start xboard-backend
```

### 10. 配置Nginx
在宝塔面板中：
1. 进入 **网站** 管理
2. 添加站点：`yourdomain.com`
3. 配置反向代理：
   - 前端：`/` → `/www/wwwroot/xboard-modern/frontend/dist`
   - 后端：`/api/` → `http://127.0.0.1:8000`

或手动配置：
```bash
# 创建Nginx配置
cat > /etc/nginx/conf.d/xboard.conf << EOF
server {
    listen 80;
    server_name yourdomain.com;
    
    # 前端静态文件
    location / {
        root /www/wwwroot/xboard-modern/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        index index.html;
    }
    
    # 后端API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 重启Nginx
systemctl restart nginx
```

## 🔐 SSL证书配置

### 1. 在宝塔面板中配置SSL
1. 进入 **网站** 管理
2. 选择您的站点
3. 点击 **SSL** 标签
4. 选择 **Let's Encrypt** 免费证书
5. 点击 **申请**

### 2. 手动配置SSL
```bash
# 安装certbot
yum install -y certbot python3-certbot-nginx

# 申请证书
certbot --nginx -d yourdomain.com

# 自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

## 🛠️ 服务管理

### 1. 后端服务管理
```bash
# 启动服务
systemctl start xboard-backend

# 停止服务
systemctl stop xboard-backend

# 重启服务
systemctl restart xboard-backend

# 查看状态
systemctl status xboard-backend

# 查看日志
journalctl -u xboard-backend -f
```

### 2. 前端更新
```bash
cd /www/wwwroot/xboard-modern/frontend

# 拉取最新代码
git pull

# 安装依赖
npm install

# 构建
npm run build
```

### 3. 后端更新
```bash
cd /www/wwwroot/xboard-modern

# 拉取最新代码
git pull

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt

# 重启服务
systemctl restart xboard-backend
```

## 📊 监控和维护

### 1. 日志查看
```bash
# 后端日志
tail -f /www/wwwroot/xboard-modern/logs/xboard.log

# Nginx日志
tail -f /www/wwwlogs/yourdomain.com.log

# 系统日志
journalctl -u xboard-backend -f
```

### 2. 性能监控
```bash
# 查看进程
ps aux | grep uvicorn

# 查看端口占用
netstat -tlnp | grep :8000

# 查看内存使用
free -h

# 查看磁盘使用
df -h
```

### 3. 数据库备份
```bash
# 创建备份脚本
cat > /root/backup_xboard.sh << EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
mysqldump -u username -p'password' xboard_db > /backup/xboard_\$DATE.sql
find /backup -name "xboard_*.sql" -mtime +7 -delete
EOF

chmod +x /root/backup_xboard.sh

# 添加到定时任务
echo "0 2 * * * /root/backup_xboard.sh" | crontab -
```

## 🔧 故障排除

### 1. 常见问题

#### 后端服务无法启动
```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 检查日志
journalctl -u xboard-backend -n 50

# 检查环境变量
cat .env
```

#### 数据库连接失败
```bash
# 测试数据库连接
mysql -u username -p -h localhost xboard_db

# 检查MySQL服务
systemctl status mysql
```

#### 前端无法访问
```bash
# 检查Nginx配置
nginx -t

# 检查文件权限
ls -la /www/wwwroot/xboard-modern/frontend/dist

# 检查Nginx日志
tail -f /www/wwwlogs/error.log
```

### 2. 性能优化

#### 启用Gzip压缩
在Nginx配置中添加：
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
```

#### 启用缓存
```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

#### 优化数据库
```sql
-- 添加索引
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_subscription_user_id ON subscriptions(user_id);
CREATE INDEX idx_order_user_id ON orders(user_id);
```

## 📞 技术支持

如果遇到问题，请：

1. 查看日志文件
2. 检查配置文件
3. 确认服务状态
4. 提交Issue到GitHub

## 📝 更新日志

- **v1.0.0**: 初始版本发布
- 支持宝塔面板自动安装
- 完整的部署文档
- 故障排除指南 