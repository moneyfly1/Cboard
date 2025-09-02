# XBoard Modern VPS 部署指南

## 🚀 快速开始

### 自动安装（推荐）
```bash
# 使用root用户执行
sudo ./install_vps_complete.sh --auto
```

### 手动配置安装
```bash
# 使用root用户执行
sudo ./install_vps_complete.sh
```

### 自定义参数安装
```bash
# 指定域名和管理员信息
sudo ./install_vps_complete.sh --domain=yourdomain.com --email=admin@yourdomain.com --password=yourpassword
```

## 📋 系统要求

- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+ / AlmaLinux 8+ / Rocky Linux 8+
- **内存**: 至少 1GB RAM（推荐 2GB+）
- **磁盘**: 至少 5GB 可用空间
- **架构**: x86_64 或 ARM64
- **权限**: root 用户

## 🛠️ 安装选项

### 自动模式
- 自动检测系统环境
- 自动选择SQLite数据库
- 自动生成管理员账户
- 自动配置Nginx和防火墙
- 自动安装SSL证书（如果有域名）

### 手动模式
- 交互式配置域名
- 选择数据库类型（SQLite/MySQL/PostgreSQL）
- 设置管理员邮箱和密码
- 自定义各项配置

## 📦 安装内容

### 系统组件
- ✅ Python 3.9+ 和虚拟环境
- ✅ Node.js 18+ 和 npm
- ✅ Nginx Web服务器
- ✅ 数据库（SQLite/MySQL/PostgreSQL）
- ✅ systemd 服务管理
- ✅ 防火墙配置

### 项目配置
- ✅ 后端API服务
- ✅ 前端Vue.js应用
- ✅ 数据库初始化
- ✅ 环境变量配置
- ✅ SSL证书（可选）

### 安全特性
- ✅ 防火墙规则
- ✅ 文件权限设置
- ✅ HTTPS加密（Let's Encrypt）
- ✅ 安全头配置

## 🌐 访问方式

安装完成后，您可以通过以下方式访问：

### HTTP访问
```
http://your-server-ip
```

### HTTPS访问（如果配置了域名）
```
https://your-domain.com
```

### API文档
```
http://your-server-ip/docs
```

## 👤 默认管理员账户

### 自动模式
- **邮箱**: `admin@your-server-ip`
- **密码**: 随机生成（安装完成后显示）

### 手动模式
- 使用您在安装过程中设置的邮箱和密码

## 🛠️ 管理命令

### 服务管理
```bash
# 启动服务
sudo systemctl start xboard

# 停止服务
sudo systemctl stop xboard

# 重启服务
sudo systemctl restart xboard

# 查看状态
sudo systemctl status xboard
```

### 查看日志
```bash
# 系统日志
sudo journalctl -u xboard -f

# Nginx日志
sudo tail -f /var/log/nginx/xboard_access.log
sudo tail -f /var/log/nginx/xboard_error.log
```

### 备份数据
```bash
# 执行备份
./backup.sh

# 查看备份文件
ls -la /var/backups/xboard/
```

## 📁 重要文件位置

```
/var/www/xboard/          # 项目根目录
├── backend/             # 后端代码
├── frontend/dist/       # 前端构建文件
├── .env                 # 环境变量配置
├── backup.sh           # 备份脚本
└── venv/               # Python虚拟环境

/etc/nginx/sites-available/xboard  # Nginx配置
/etc/systemd/system/xboard.service # systemd服务配置
/var/log/nginx/                   # Nginx日志
/var/backups/xboard/             # 备份文件
```

## 🔧 配置修改

### 修改环境变量
```bash
# 编辑配置文件
nano .env

# 重启服务使配置生效
sudo systemctl restart xboard
```

### 修改Nginx配置
```bash
# 编辑Nginx配置
sudo nano /etc/nginx/sites-available/xboard

# 测试配置
sudo nginx -t

# 重新加载配置
sudo systemctl reload nginx
```

## 🔍 故障排除

### 服务无法启动
```bash
# 查看详细错误信息
sudo journalctl -u xboard -n 50

# 检查端口占用
sudo netstat -tlnp | grep :8000
```

### 数据库连接问题
```bash
# 测试数据库连接
python3 -c "from app.core.database import test_database_connection; print(test_database_connection())"
```

### 前端无法访问
```bash
# 检查Nginx状态
sudo systemctl status nginx

# 检查防火墙
sudo ufw status
# 或
sudo firewall-cmd --list-all
```

### SSL证书问题
```bash
# 重新获取证书
sudo certbot renew

# 手动获取证书
sudo certbot --nginx -d yourdomain.com
```

## 📞 获取帮助

如果遇到问题，请：

1. 查看系统日志：`sudo journalctl -u xboard -f`
2. 检查Nginx日志：`sudo tail -f /var/log/nginx/xboard_error.log`
3. 验证配置文件语法
4. 确认网络连接和防火墙设置

## 🔄 更新说明

### 项目更新
```bash
# 备份当前配置
cp .env .env.backup

# 拉取最新代码
git pull

# 重新构建前端
cd frontend && npm install && npm run build && cd ..

# 重启服务
sudo systemctl restart xboard
```

### 系统更新
```bash
# 更新系统包
sudo apt update && sudo apt upgrade
# 或
sudo dnf update

# 重启服务器
sudo reboot
```

## 📊 监控和维护

### 性能监控
- 系统资源使用情况
- API响应时间
- 数据库查询性能
- 前端加载速度

### 日志轮转
系统已配置自动日志轮转，避免日志文件过大。

### 定期备份
系统已配置每周自动备份，请定期检查备份完整性。

---

## 🎉 安装完成！

恭喜！XBoard Modern 已经成功安装在您的VPS上。

现在您可以开始配置您的订阅管理系统了！

如有任何问题，请参考本文档的故障排除部分或查看系统日志。
