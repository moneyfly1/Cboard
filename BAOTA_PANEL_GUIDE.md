# 宝塔面板配置详细指南

## 概述

本指南详细介绍如何在宝塔面板中配置XBoard项目，包括网站创建、SSL证书配置、反向代理设置等。

## 第一步：宝塔面板安装

### 1.1 系统要求

- Ubuntu 18.04+ / CentOS 7+ / Debian 9+
- 内存：至少1GB
- 磁盘：至少10GB可用空间
- 网络：稳定的网络连接

### 1.2 安装命令

```bash
# Ubuntu/Debian系统
wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh

# CentOS系统
yum install -y wget && wget -O install.sh http://download.bt.cn/install/install_6.0.sh && sh install.sh
```

### 1.3 安装完成

安装完成后会显示：
```
安装完成！
面板地址: http://your-server-ip:8888
用户名: admin
密码: xxxxxxxx
```

## 第二步：宝塔面板基础配置

### 2.1 首次登录

1. 访问面板地址：`http://your-server-ip:8888`
2. 输入用户名和密码
3. 同意用户协议

### 2.2 安装推荐软件

在软件商店中安装以下软件：

#### 必需软件
- **Nginx 1.20+**: Web服务器
- **PM2管理器**: Node.js进程管理
- **MySQL 8.0+**: 数据库（可选，本项目使用SQLite）

#### 推荐软件
- **Redis**: 缓存服务
- **phpMyAdmin**: 数据库管理
- **日志分析**: 网站日志分析

### 2.3 安全设置

1. **修改面板端口**
   - 面板设置 → 安全设置
   - 修改面板端口（默认8888）
   - 设置访问IP白名单

2. **设置面板密码**
   - 面板设置 → 面板密码
   - 设置强密码

3. **绑定域名**
   - 面板设置 → 域名绑定
   - 绑定管理域名（可选）

## 第三步：创建网站

### 3.1 添加站点

1. 点击"网站" → "添加站点"
2. 填写站点信息：
   ```
   域名: yourdomain.com
   FTP: 不创建
   数据库: 不创建
   PHP版本: 纯静态
   ```
3. 点击提交

### 3.2 网站目录结构

创建完成后，网站目录结构如下：
```
/www/wwwroot/yourdomain.com/
├── index.html
├── 404.html
└── .user.ini
```

### 3.3 设置网站目录

1. 在网站列表中点击"设置"
2. 选择"网站目录"
3. 设置运行目录为：`/www/wwwroot/xboard/frontend/dist`

## 第四步：SSL证书配置

### 4.1 Let's Encrypt证书

1. 在网站设置中选择"SSL"
2. 选择"Let's Encrypt"
3. 填写信息：
   ```
   域名: yourdomain.com
   邮箱: your-email@example.com
   ```
4. 勾选"www.yourdomain.com"
5. 点击申请

### 4.2 强制HTTPS

1. 证书申请成功后
2. 开启"强制HTTPS"
3. 开启"HSTS"

### 4.3 证书自动续期

1. 开启"自动续期"
2. 设置续期提醒

## 第五步：反向代理配置

### 5.1 添加反向代理

1. 在网站设置中选择"反向代理"
2. 点击"添加反向代理"
3. 填写配置：
   ```
   代理名称: API
   目标URL: http://127.0.0.1:8000
   发送域名: $host
   代理目录: /api/
   ```

### 5.2 高级配置

在反向代理配置中添加以下内容：

```nginx
# 超时设置
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;

# 缓冲设置
proxy_buffering on;
proxy_buffer_size 4k;
proxy_buffers 8 4k;

# 请求头设置
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Host $host;
proxy_set_header X-Forwarded-Port $server_port;
```

## 第六步：伪静态配置

### 6.1 添加伪静态规则

在网站设置中选择"伪静态"，添加以下规则：

```nginx
# 前端路由
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
}

# 静态文件缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# 安全配置
location ~ /\. {
    deny all;
}

location ~ /(\.env|\.git|\.svn|\.htaccess|\.htpasswd) {
    deny all;
}
```

## 第七步：防火墙配置

### 7.1 开放端口

在宝塔面板中：
1. 点击"安全" → "防火墙"
2. 添加规则：
   ```
   端口: 80
   协议: TCP
   策略: 允许
   备注: HTTP
   ```
   ```
   端口: 443
   协议: TCP
   策略: 允许
   备注: HTTPS
   ```

### 7.2 系统防火墙

```bash
# 安装ufw
apt install ufw -y

# 配置防火墙
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8888/tcp  # 宝塔面板端口

# 启用防火墙
ufw enable
```

## 第八步：PM2管理器配置

### 8.1 安装PM2管理器

1. 在软件商店中搜索"PM2管理器"
2. 点击安装

### 8.2 添加项目

1. 打开PM2管理器
2. 点击"添加项目"
3. 填写配置：
   ```
   项目名称: xboard-backend
   项目路径: /www/wwwroot/xboard
   启动文件: main.py
   Python版本: /www/wwwroot/xboard/venv/bin/python
   端口: 8000
   ```

### 8.3 环境变量

在PM2配置中添加环境变量：
```json
{
  "env": {
    "NODE_ENV": "production",
    "PORT": 8000
  }
}
```

## 第九步：数据库配置

### 9.1 SQLite配置

本项目使用SQLite数据库，无需额外配置。

### 9.2 数据库文件权限

```bash
# 设置数据库文件权限
chmod 664 /www/wwwroot/xboard/xboard.db
chown www:www /www/wwwroot/xboard/xboard.db
```

### 9.3 数据库备份

1. 在宝塔面板中设置定时任务
2. 添加备份脚本：
   ```bash
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   cp /www/wwwroot/xboard/xboard.db /backup/xboard_$DATE.db
   ```

## 第十步：日志配置

### 10.1 网站日志

1. 在网站设置中选择"日志"
2. 开启访问日志和错误日志
3. 设置日志保存天数

### 10.2 应用日志

```bash
# 查看PM2日志
pm2 logs xboard-backend

# 查看系统日志
journalctl -u nginx -f
```

### 10.3 日志分析

1. 在软件商店中安装"日志分析"
2. 配置日志分析规则
3. 设置日志告警

## 第十一步：性能优化

### 11.1 Nginx优化

在网站设置中添加以下配置：

```nginx
# 启用gzip压缩
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

# 设置缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# 限制请求大小
client_max_body_size 10M;
```

### 11.2 系统优化

```bash
# 优化系统参数
echo 'net.core.somaxconn = 65535' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog = 65535' >> /etc/sysctl.conf
sysctl -p
```

## 第十二步：监控配置

### 12.1 系统监控

1. 在宝塔面板中查看系统监控
2. 设置监控告警
3. 配置邮件通知

### 12.2 应用监控

```bash
# 使用PM2监控
pm2 monit

# 查看系统资源
htop
```

### 12.3 日志监控

1. 设置日志告警规则
2. 配置异常日志通知
3. 定期检查日志文件

## 第十三步：安全配置

### 13.1 网站安全

1. 在网站设置中选择"安全"
2. 开启"防CC攻击"
3. 设置访问频率限制

### 13.2 系统安全

```bash
# 安装fail2ban
apt install fail2ban -y

# 配置fail2ban
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
EOF

systemctl restart fail2ban
```

### 13.3 文件权限

```bash
# 设置项目文件权限
chown -R www:www /www/wwwroot/xboard
chmod -R 755 /www/wwwroot/xboard
chmod 600 /www/wwwroot/xboard/.env
chmod 664 /www/wwwroot/xboard/xboard.db
```

## 第十四步：备份配置

### 14.1 自动备份

1. 在宝塔面板中设置定时任务
2. 添加备份脚本：
   ```bash
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   BACKUP_DIR="/backup/xboard_$DATE"
   
   mkdir -p $BACKUP_DIR
   
   # 备份数据库
   cp /www/wwwroot/xboard/xboard.db $BACKUP_DIR/
   
   # 备份配置文件
   cp /www/wwwroot/xboard/.env $BACKUP_DIR/
   
   # 备份代码
   tar -czf $BACKUP_DIR/code.tar.gz /www/wwwroot/xboard
   
   # 清理旧备份（保留7天）
   find /backup -name "xboard_*" -type d -mtime +7 -exec rm -rf {} \;
   ```

### 14.2 备份存储

1. 配置云存储备份
2. 设置备份加密
3. 测试备份恢复

## 第十五步：故障排除

### 15.1 常见问题

#### 问题1：网站无法访问
```bash
# 检查Nginx状态
systemctl status nginx

# 检查Nginx配置
nginx -t

# 重启Nginx
systemctl restart nginx
```

#### 问题2：SSL证书问题
```bash
# 检查证书文件
ls -la /www/server/panel/vhost/cert/yourdomain.com/

# 重新申请证书
# 在宝塔面板中重新申请Let's Encrypt证书
```

#### 问题3：PM2进程问题
```bash
# 检查PM2状态
pm2 status

# 重启PM2进程
pm2 restart xboard-backend

# 查看PM2日志
pm2 logs xboard-backend
```

### 15.2 日志分析

```bash
# 查看Nginx错误日志
tail -f /www/wwwlogs/yourdomain.com.error.log

# 查看系统日志
journalctl -u nginx -f

# 查看PM2日志
pm2 logs xboard-backend --lines 100
```

## 第十六步：维护指南

### 16.1 日常维护

1. **每日检查**
   - 检查服务状态
   - 查看错误日志
   - 监控系统资源

2. **每周维护**
   - 清理日志文件
   - 检查磁盘空间
   - 更新系统补丁

3. **每月维护**
   - 备份数据
   - 检查安全设置
   - 性能优化

### 16.2 更新升级

```bash
# 更新项目代码
cd /www/wwwroot/xboard
git pull origin master

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
pm2 restart xboard-backend
```

## 总结

通过本指南，您可以完整配置宝塔面板来运行XBoard项目：

1. ✅ 宝塔面板安装和配置
2. ✅ 网站创建和SSL证书配置
3. ✅ 反向代理和伪静态配置
4. ✅ PM2管理器配置
5. ✅ 安全配置和防火墙设置
6. ✅ 监控和日志配置
7. ✅ 备份和恢复策略
8. ✅ 故障排除和维护

配置完成后，您的XBoard项目将在宝塔面板中稳定运行，具备完整的设备限制功能和管理界面。
