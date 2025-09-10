# XBoard 项目 VPS 部署教程

## 📋 系统要求

### 推荐配置
- **操作系统**: Ubuntu 20.04 LTS 或 CentOS 7/8
- **内存**: 最低 2GB，推荐 4GB 以上
- **存储**: 最低 20GB，推荐 50GB 以上
- **CPU**: 最低 2核，推荐 4核以上
- **网络**: 公网IP，开放80、443端口

### 宝塔面板要求
- **宝塔版本**: 7.7.0 或更高版本
- **Python版本**: 3.8 或更高版本
- **Node.js版本**: 16.x 或更高版本

## 🚀 部署步骤

### 第一步：安装宝塔面板

#### Ubuntu 系统
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装宝塔面板
wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh ed8484bec
```

#### CentOS 系统
```bash
# 更新系统
yum update -y

# 安装宝塔面板
yum install -y wget && wget -O install.sh http://download.bt.cn/install/install_6.0.sh && sh install.sh ed8484bec
```

安装完成后，记录面板地址、用户名和密码。

### 第二步：配置宝塔面板环境

1. **登录宝塔面板**
   - 访问面板地址
   - 使用安装时提供的用户名和密码登录

2. **安装必要软件**
   - 进入"软件商店"
   - 安装以下软件：
     - **Nginx** (1.18+)
     - **Python项目管理器** (2.0+)
     - **PM2管理器** (2.0+)
     - **MySQL** (5.7+) 或 **PostgreSQL** (12+)
     - **Redis** (6.0+)

3. **配置Python环境**
   - 进入"软件商店" → "Python项目管理器"
   - 安装Python 3.9
   - 创建虚拟环境

### 第三步：上传项目文件

#### 方法一：通过宝塔面板上传
1. 进入"文件"管理
2. 导航到 `/www/wwwroot/` 目录
3. 创建项目目录：`mkdir xboard`
4. 上传项目压缩包并解压

#### 方法二：通过Git克隆
```bash
# SSH连接到服务器
ssh root@your-server-ip

# 进入网站目录
cd /www/wwwroot/

# 克隆项目
git clone https://github.com/your-username/xboard.git
cd xboard
```

### 第四步：配置后端服务

1. **创建Python项目**
   - 进入"软件商店" → "Python项目管理器"
   - 点击"添加项目"
   - 配置如下：
     ```
     项目名称: xboard-backend
     项目路径: /www/wwwroot/xboard
     Python版本: 3.9
     启动方式: uvicorn
     启动文件: main.py
     端口: 8000
     ```

2. **安装依赖**
   ```bash
   # 进入项目目录
   cd /www/wwwroot/xboard
   
   # 激活虚拟环境
   source venv/bin/activate
   
   # 安装依赖
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   # 创建环境配置文件
   cp env.example .env
   
   # 编辑配置文件
   nano .env
   ```
   
   配置内容：
   ```env
   # 数据库配置
   DATABASE_URL=sqlite:///./xboard.db
   # 或使用MySQL: DATABASE_URL=mysql://username:password@localhost:3306/xboard
   
   # 安全配置
   SECRET_KEY=your-super-secret-key-here
   
   # 邮件配置
   SMTP_HOST=smtp.qq.com
   SMTP_PORT=587
   SMTP_USER=your-email@qq.com
   SMTP_PASSWORD=your-smtp-password
   EMAILS_FROM_EMAIL=your-email@qq.com
   EMAILS_FROM_NAME=XBoard Modern
   
   # 跨域配置
   BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","https://yourdomain.com"]
   ```

4. **初始化数据库**
   ```bash
   # 运行数据库初始化
   python -c "from app.core.database import init_database; init_database()"
   ```

### 第五步：配置前端服务

1. **安装Node.js依赖**
   ```bash
   # 进入前端目录
   cd /www/wwwroot/xboard/frontend
   
   # 安装依赖
   npm install
   ```

2. **构建前端项目**
   ```bash
   # 构建生产版本
   npm run build
   ```

3. **配置PM2**
   - 进入"软件商店" → "PM2管理器"
   - 添加项目：
     ```
     项目名称: xboard-frontend
     运行目录: /www/wwwroot/xboard/frontend
     启动文件: dist/index.html
     运行方式: 静态文件
     ```

### 第六步：配置Nginx反向代理

1. **创建网站**
   - 进入"网站" → "添加站点"
   - 域名：`yourdomain.com`
   - 根目录：`/www/wwwroot/xboard/frontend/dist`

2. **配置反向代理**
   - 进入网站设置 → "反向代理"
   - 添加反向代理：
     ```
     代理名称: xboard-api
     目标URL: http://127.0.0.1:8000
     发送域名: $host
     代理目录: /api
     ```

3. **配置SSL证书**
   - 进入网站设置 → "SSL"
   - 选择"Let's Encrypt"免费证书
   - 开启"强制HTTPS"

### 第七步：配置防火墙和安全

1. **开放端口**
   - 进入"安全" → "防火墙"
   - 开放端口：80, 443, 22

2. **配置SSH**
   - 修改SSH端口（可选）
   - 禁用root登录（推荐）
   - 配置密钥登录

### 第八步：启动服务

1. **启动后端服务**
   - 进入"软件商店" → "Python项目管理器"
   - 找到xboard-backend项目
   - 点击"启动"

2. **启动前端服务**
   - 进入"软件商店" → "PM2管理器"
   - 找到xboard-frontend项目
   - 点击"启动"

3. **设置开机自启**
   - 在PM2管理器中设置开机自启
   - 在Python项目管理器中设置开机自启

## 🔧 常见问题解决

### 1. 端口占用问题
```bash
# 查看端口占用
netstat -tlnp | grep :8000

# 杀死占用进程
kill -9 PID
```

### 2. 权限问题
```bash
# 设置文件权限
chown -R www:www /www/wwwroot/xboard
chmod -R 755 /www/wwwroot/xboard
```

### 3. 数据库连接问题
- 检查数据库服务是否启动
- 验证数据库连接字符串
- 检查防火墙设置

### 4. 前端构建失败
```bash
# 清理缓存
npm cache clean --force
rm -rf node_modules
npm install
```

## 📊 性能优化

### 1. 数据库优化
- 配置数据库连接池
- 添加数据库索引
- 定期清理日志

### 2. 缓存配置
- 启用Redis缓存
- 配置Nginx缓存
- 使用CDN加速

### 3. 监控配置
- 配置系统监控
- 设置日志轮转
- 配置告警通知

## 🔄 更新部署

### 1. 代码更新
```bash
# 拉取最新代码
cd /www/wwwroot/xboard
git pull origin main

# 更新依赖
pip install -r requirements.txt
npm install

# 重新构建前端
cd frontend
npm run build

# 重启服务
pm2 restart xboard-frontend
# 在Python项目管理器中重启后端服务
```

### 2. 数据库迁移
```bash
# 备份数据库
cp xboard.db xboard.db.backup

# 运行迁移脚本
python -c "from app.core.database import init_database; init_database()"
```

## 📝 维护建议

### 1. 定期备份
- 数据库备份
- 代码备份
- 配置文件备份

### 2. 日志管理
- 定期清理日志文件
- 监控错误日志
- 设置日志轮转

### 3. 安全更新
- 定期更新系统
- 更新依赖包
- 检查安全漏洞

## 🆘 技术支持

如果在部署过程中遇到问题，可以：

1. 查看宝塔面板日志
2. 检查系统资源使用情况
3. 查看应用日志
4. 联系技术支持

---

**注意**: 请根据实际情况调整配置参数，确保生产环境的安全性。
