# XBoard Modern 安装指南

## 📋 目录
- [系统要求](#系统要求)
- [快速安装](#快速安装)
- [详细安装步骤](#详细安装步骤)
- [环境检查](#环境检查)
- [常见问题](#常见问题)
- [卸载指南](#卸载指南)

## 🖥️ 系统要求

### 最低要求
- **操作系统**: Ubuntu 18.04+, CentOS 7+, Debian 9+
- **Python**: 3.8+
- **Node.js**: 16+ (可选，用于前端构建)
- **内存**: 1GB RAM
- **磁盘**: 2GB 可用空间

### 推荐配置
- **操作系统**: Ubuntu 20.04+ 或 CentOS 8+
- **Python**: 3.9+
- **Node.js**: 18+
- **内存**: 2GB+ RAM
- **磁盘**: 5GB+ 可用空间

## 🚀 快速安装

### 方法一：智能安装脚本（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/moneyfly1/xboard.git
cd xboard

# 2. 运行智能安装脚本
chmod +x install.sh
./install.sh
```

### 方法二：Docker 安装

```bash
# 1. 克隆项目
git clone https://github.com/moneyfly1/xboard.git
cd xboard

# 2. 使用 Docker Compose
docker-compose up -d
```

## 📝 详细安装步骤

### 1. 环境检查

在安装前，建议先运行环境检查脚本：

```bash
chmod +x check_env.sh
./check_env.sh
```

检查脚本会显示：
- ✅ 通过的项目
- ⚠️ 警告项目
- ❌ 错误项目

### 2. 自动安装

智能安装脚本会自动执行以下步骤：

1. **检测项目路径** - 自动找到项目文件位置
2. **检查系统环境** - 验证操作系统和依赖
3. **安装系统依赖** - 安装Python、Node.js、Nginx等
4. **创建虚拟环境** - 设置Python虚拟环境
5. **安装Python依赖** - 安装所有必需的Python包
6. **安装前端依赖** - 安装Node.js依赖并构建前端
7. **创建配置文件** - 生成.env配置文件
8. **初始化数据库** - 创建数据库表和初始数据
9. **配置系统服务** - 创建systemd服务
10. **配置Nginx** - 设置反向代理
11. **启动服务** - 启动所有服务

### 3. 手动安装

如果自动安装失败，可以手动执行以下步骤：

#### 3.1 安装系统依赖

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential curl wget git nginx redis-server
```

**CentOS/RHEL:**
```bash
sudo yum update -y
sudo yum install -y python3 python3-pip python3-devel gcc curl wget git nginx redis
```

#### 3.2 设置Python环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装Python依赖
pip install -r backend/requirements.txt
```

#### 3.3 安装前端依赖

```bash
# 安装Node.js (如果未安装)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装前端依赖
cd frontend
npm install
npm run build
cd ..
```

#### 3.4 配置环境变量

```bash
# 复制环境配置文件
cp env.example .env

# 编辑配置文件
nano .env
```

主要配置项：
```env
# 数据库配置
DATABASE_URL=sqlite:///./xboard.db

# 应用配置
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 邮件配置
SMTP_HOST=smtp.qq.com
SMTP_USER=your_email@qq.com
SMTP_PASSWORD=your_email_password

# 支付宝配置
ALIPAY_APP_ID=your_alipay_app_id
ALIPAY_PRIVATE_KEY=your_alipay_private_key
ALIPAY_PUBLIC_KEY=your_alipay_public_key
```

#### 3.5 初始化数据库

```bash
# 激活虚拟环境
source venv/bin/activate

# 初始化数据库
python init_database.py
```

#### 3.6 创建系统服务

```bash
# 创建systemd服务文件
sudo tee /etc/systemd/system/xboard-backend.service > /dev/null <<EOF
[Unit]
Description=XBoard Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable xboard-backend
sudo systemctl start xboard-backend
```

#### 3.7 配置Nginx

```bash
# 创建Nginx配置文件
sudo tee /etc/nginx/sites-available/xboard > /dev/null <<EOF
server {
    listen 80;
    server_name your_domain.com;
    
    # 前端静态文件
    location / {
        root $(pwd)/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }
    
    # 后端API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 静态文件
    location /static/ {
        alias $(pwd)/backend/static/;
    }
    
    # 上传文件
    location /uploads/ {
        alias $(pwd)/uploads/;
    }
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/xboard /etc/nginx/sites-enabled/

# 测试并重启Nginx
sudo nginx -t
sudo systemctl restart nginx
```

## 🔍 环境检查

### 运行检查脚本

```bash
./check_env.sh
```

### 检查项目

检查脚本会验证以下项目：

#### 系统环境
- ✅ 操作系统版本
- ✅ Python版本 (3.8+)
- ✅ Node.js版本 (16+)
- ✅ 系统服务状态

#### 项目文件
- ✅ 必需文件存在性
- ✅ 目录结构完整性
- ✅ 文件权限正确性

#### 依赖包
- ✅ Python依赖包
- ✅ Node.js依赖包
- ✅ 系统服务依赖

#### 网络和存储
- ✅ 网络连接状态
- ✅ 磁盘空间充足
- ✅ 端口监听状态

### 检查结果说明

- **✅ 通过**: 项目正常，无需处理
- **⚠️ 警告**: 项目可用但建议优化
- **❌ 错误**: 必须解决的问题

## ❓ 常见问题

### Q1: 安装脚本提示"未找到项目文件"
**A**: 确保在项目根目录运行脚本，或手动指定项目路径。

### Q2: Python虚拟环境创建失败
**A**: 安装python3-venv包：
```bash
# Ubuntu/Debian
sudo apt install python3-venv

# CentOS/RHEL
sudo yum install python3-venv
```

### Q3: 依赖包安装失败
**A**: 升级pip并安装编译工具：
```bash
pip install --upgrade pip
sudo apt install build-essential python3-dev
```

### Q4: 服务启动失败
**A**: 检查日志：
```bash
sudo journalctl -u xboard-backend -f
```

### Q5: Nginx配置错误
**A**: 检查配置语法：
```bash
sudo nginx -t
```

### Q6: 端口被占用
**A**: 检查端口占用：
```bash
sudo netstat -tlnp | grep :8000
```

## 🗑️ 卸载指南

### 使用卸载脚本

```bash
chmod +x uninstall.sh
./uninstall.sh
```

### 手动卸载

```bash
# 1. 停止服务
sudo systemctl stop xboard-backend
sudo systemctl disable xboard-backend

# 2. 删除服务文件
sudo rm -f /etc/systemd/system/xboard-backend.service
sudo systemctl daemon-reload

# 3. 删除Nginx配置
sudo rm -f /etc/nginx/sites-enabled/xboard
sudo rm -f /etc/nginx/sites-available/xboard
sudo systemctl reload nginx

# 4. 删除项目文件
sudo rm -rf /path/to/xboard

# 5. 清理日志
sudo journalctl --vacuum-time=1d
```

## 📞 技术支持

如果遇到问题，请：

1. 运行 `./check_env.sh` 检查环境
2. 查看服务日志：`sudo journalctl -u xboard-backend -f`
3. 检查Nginx日志：`sudo tail -f /var/log/nginx/error.log`
4. 提交Issue到GitHub仓库

## 🔄 更新指南

```bash
# 1. 备份数据
cp xboard.db xboard.db.backup

# 2. 拉取最新代码
git pull origin main

# 3. 更新依赖
source venv/bin/activate
pip install -r backend/requirements.txt

# 4. 重启服务
sudo systemctl restart xboard-backend
``` 