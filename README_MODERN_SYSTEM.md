# XBoard Modern 现代系统安装指南

## 🚀 系统要求

### 支持的系统版本
- **Nginx**: 1.28+ (推荐)
- **MySQL**: 5.7+ (推荐 8.0+)
- **PHP**: 8.2+ (可选，XBoard项目不需要)
- **Python**: 3.8+ (必需)
- **操作系统**: Ubuntu 20.04+, Debian 11+, CentOS 8+

### 您的系统环境
- ✅ Nginx 1.28
- ✅ MySQL 5.7.44
- ✅ PHP 8.2.28
- ✅ 系统版本较高

## 📋 安装步骤

### 1. 克隆项目
```bash
git clone <your-repo-url> /www/wwwroot/xboard
cd /www/wwwroot/xboard
```

### 2. 运行现代系统安装脚本
```bash
chmod +x install_modern_system.sh
./install_modern_system.sh
```

### 3. 配置数据库密码
安装完成后，需要设置MySQL密码：
```bash
# 设置MySQL root密码
mysql_secure_installation

# 或者直接修改.env文件中的数据库密码
nano .env
```

## 🔧 脚本特性

### 智能检测
- 自动检测已安装的软件版本
- 智能选择兼容的requirements文件
- 自动配置Nginx、MySQL、PHP

### 安全配置
- 自动配置安全头
- MySQL安全设置
- 文件权限管理
- 防火墙配置

### 性能优化
- Nginx反向代理配置
- MySQL性能优化
- Python虚拟环境
- 静态文件缓存

## 📁 文件结构

```
xboard/
├── backend/
│   ├── requirements_modern.txt    # 现代系统依赖
│   ├── requirements_vps.txt       # VPS环境依赖
│   └── requirements.txt           # 标准依赖
├── frontend/                      # Vue.js前端
├── install_modern_system.sh       # 现代系统安装脚本
├── install_optimized.sh           # 优化安装脚本
└── README_MODERN_SYSTEM.md        # 本文件
```

## 🌐 访问地址

安装完成后，您可以通过以下地址访问：

- **前端**: `http://your-server-ip`
- **API文档**: `http://your-server-ip/docs`
- **管理后台**: `http://your-server-ip/admin`

## 🔍 故障排除

### 常见问题

#### 1. Python版本过低
```bash
# 检查Python版本
python3 --version

# 如果版本低于3.8，需要升级
sudo apt update
sudo apt install python3.9 python3.9-venv
```

#### 2. MySQL连接失败
```bash
# 检查MySQL服务状态
systemctl status mysql

# 检查MySQL用户权限
mysql -u root -p
SHOW GRANTS FOR 'xboard'@'localhost';
```

#### 3. Nginx配置错误
```bash
# 测试Nginx配置
nginx -t

# 查看Nginx错误日志
tail -f /var/log/nginx/error.log
```

### 日志查看
```bash
# 查看XBoard服务日志
journalctl -u xboard -f

# 查看Nginx访问日志
tail -f /var/log/nginx/access.log

# 查看MySQL日志
tail -f /var/log/mysql/error.log
```

## 🛠️ 管理命令

### 服务管理
```bash
# 启动服务
systemctl start xboard
systemctl start nginx
systemctl start mysql

# 停止服务
systemctl stop xboard
systemctl stop nginx
systemctl stop mysql

# 重启服务
systemctl restart xboard
systemctl restart nginx
systemctl restart mysql

# 查看状态
systemctl status xboard
systemctl status nginx
systemctl status mysql
```

### 数据库管理
```bash
# 连接MySQL
mysql -u xboard -p

# 备份数据库
mysqldump -u xboard -p xboard > backup.sql

# 恢复数据库
mysql -u xboard -p xboard < backup.sql
```

## 🔒 安全建议

### 1. 配置SSL证书
```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d yourdomain.com
```

### 2. 防火墙配置
```bash
# 启用UFW
ufw enable

# 允许必要端口
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
```

### 3. 定期更新
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 更新Python依赖
source venv/bin/activate
pip install --upgrade -r backend/requirements_modern.txt
```

## 📞 技术支持

如果您遇到问题，请：

1. 查看日志文件
2. 检查系统要求
3. 确认配置文件正确性
4. 联系技术支持

## 📝 更新日志

### v1.0.0 (2025-09-02)
- 支持Nginx 1.28+
- 支持MySQL 5.7+
- 支持PHP 8.2+
- 智能依赖检测
- 安全配置优化
- 性能优化配置
