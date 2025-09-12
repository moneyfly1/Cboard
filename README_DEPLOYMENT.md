# XBoard 项目部署指南

## 项目简介

XBoard是一个功能完整的设备数量限制系统，专门为订阅软件设计，支持24种主流订阅软件的精确识别和管理。

### 核心功能

- ✅ **设备数量限制**: 精确控制客户设备数量
- ✅ **软件识别**: 支持24种主流订阅软件
- ✅ **智能指纹**: 解决同设备不同IP问题
- ✅ **管理界面**: 完整的设备管理功能
- ✅ **错误处理**: 优雅的错误页面和用户引导

## 快速开始

### 方法一：一键安装脚本（推荐）

```bash
# 下载并运行安装脚本
wget https://raw.githubusercontent.com/moneyfly1/Cboard/master/install_xboard.sh
chmod +x install_xboard.sh
./install_xboard.sh
```

### 方法二：快速部署脚本

```bash
# 下载并运行快速部署脚本
wget https://raw.githubusercontent.com/moneyfly1/Cboard/master/quick_deploy.sh
chmod +x quick_deploy.sh
./quick_deploy.sh
```

## 系统要求

### 最低配置
- **CPU**: 1核心
- **内存**: 2GB RAM
- **存储**: 20GB SSD
- **带宽**: 1Mbps
- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+

### 推荐配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 40GB SSD
- **带宽**: 5Mbps
- **操作系统**: Ubuntu 22.04 LTS

## 详细部署文档

### 1. VPS部署指南
📖 [VPS_DEPLOYMENT_GUIDE.md](./VPS_DEPLOYMENT_GUIDE.md)
- 完整的VPS服务器配置
- 宝塔面板安装和配置
- 域名配置和SSL证书
- 项目自动部署
- 服务配置和管理

### 2. 宝塔面板配置
📖 [BAOTA_PANEL_GUIDE.md](./BAOTA_PANEL_GUIDE.md)
- 宝塔面板详细配置
- 网站创建和SSL证书
- 反向代理和伪静态
- PM2管理器配置
- 安全配置和监控

### 3. 设备限制功能
📖 [DEVICE_LIMIT_SOLUTION.md](./DEVICE_LIMIT_SOLUTION.md)
- 设备限制系统详解
- 软件识别规则
- 设备指纹算法
- 管理功能说明

### 4. 软件订阅指南
📖 [SOFTWARE_SUBSCRIPTION_GUIDE.md](./SOFTWARE_SUBSCRIPTION_GUIDE.md)
- 软件订阅功能说明
- 支持的订阅软件列表
- 设备识别特性
- 错误处理机制

## 支持的订阅软件

### iOS 软件 (6种)
- Shadowrocket
- Quantumult X
- Surge
- Loon
- Stash
- Sparkle

### Android 软件 (7种)
- Clash Meta for Android
- Clash for Android
- V2rayNG
- SagerNet
- Matsuri
- AnXray
- Nekobox

### Windows 软件 (5种)
- Clash for Windows
- v2rayN
- FlClash
- Clash Verge
- ClashX

### macOS 软件 (2种)
- ClashX Pro
- Clash for Mac

### Linux 软件 (1种)
- Clash for Linux

## 部署步骤概览

### 第一步：准备VPS服务器
1. 购买VPS服务器
2. 选择操作系统（推荐Ubuntu 22.04）
3. 配置安全组开放端口

### 第二步：安装宝塔面板
```bash
# Ubuntu/Debian系统
wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh

# CentOS系统
yum install -y wget && wget -O install.sh http://download.bt.cn/install/install_6.0.sh && sh install.sh
```

### 第三步：准备域名
1. 购买域名
2. 配置DNS解析
3. 等待解析生效

### 第四步：运行安装脚本
```bash
# 下载安装脚本
wget https://raw.githubusercontent.com/moneyfly1/Cboard/master/install_xboard.sh
chmod +x install_xboard.sh

# 运行安装脚本
./install_xboard.sh
```

### 第五步：宝塔面板配置
1. 创建网站并绑定域名
2. 申请SSL证书
3. 配置反向代理
4. 设置伪静态规则

## 访问地址

部署完成后，您可以通过以下地址访问：

- **前端界面**: `https://yourdomain.com`
- **管理面板**: `https://yourdomain.com/admin`
- **API文档**: `https://yourdomain.com/docs`

## 管理命令

```bash
# 进入项目目录
cd /www/wwwroot/xboard

# 启动服务
./start.sh

# 停止服务
./stop.sh

# 重启服务
./restart.sh

# 查看状态
./status.sh
```

## 重要文件

- **配置文件**: `/www/wwwroot/xboard/.env`
- **数据库**: `/www/wwwroot/xboard/xboard.db`
- **日志文件**: `/www/wwwroot/xboard/logs/`
- **Nginx配置**: `/etc/nginx/sites-available/xboard`

## 故障排除

### 常见问题

1. **服务无法启动**
   ```bash
   # 检查端口占用
   netstat -tlnp | grep 8000
   
   # 查看日志
   pm2 logs xboard-backend
   ```

2. **域名无法访问**
   ```bash
   # 检查Nginx状态
   systemctl status nginx
   
   # 检查Nginx配置
   nginx -t
   ```

3. **SSL证书问题**
   - 在宝塔面板中重新申请Let's Encrypt证书
   - 检查证书文件权限

### 日志查看

```bash
# 查看应用日志
tail -f /www/wwwroot/xboard/logs/combined.log

# 查看Nginx日志
tail -f /www/wwwlogs/yourdomain.com.log

# 查看PM2日志
pm2 logs xboard-backend
```

## 安全配置

### 防火墙设置
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

### 系统安全
```bash
# 安装fail2ban
apt install fail2ban -y

# 更新系统
apt update && apt upgrade -y
```

## 备份策略

### 自动备份脚本
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

echo "备份完成: $BACKUP_DIR"
```

### 定时备份
```bash
# 编辑crontab
crontab -e

# 添加每日备份任务
0 2 * * * /path/to/backup_script.sh
```

## 性能优化

### Nginx优化
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
```

### 系统优化
```bash
# 优化系统参数
echo 'net.core.somaxconn = 65535' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog = 65535' >> /etc/sysctl.conf
sysctl -p
```

## 监控和维护

### 系统监控
```bash
# 查看系统资源
htop

# 查看磁盘使用
df -h

# 查看内存使用
free -h
```

### 应用监控
```bash
# 使用PM2监控
pm2 monit

# 查看PM2状态
pm2 status
```

## 更新升级

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

## 技术支持

如果在部署过程中遇到问题，请：

1. 检查日志文件
2. 查看错误信息
3. 参考故障排除部分
4. 联系技术支持

**项目地址**: https://github.com/moneyfly1/Cboard
**文档地址**: https://github.com/moneyfly1/Cboard/wiki

## 许可证

本项目采用MIT许可证，详情请查看 [LICENSE](LICENSE) 文件。

---

**注意**: 本系统专门为软件订阅设计，不支持浏览器访问。所有订阅请求都应该通过订阅软件发起，系统会根据User-Agent自动识别软件类型并进行相应的设备限制处理。
