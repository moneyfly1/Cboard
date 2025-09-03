#!/bin/bash

# ================================
# XBoard Modern 优化安装脚本
# 包含MySQL、Nginx最佳配置选择
# ================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 全局变量
DB_TYPE="mysql"
DB_VERSION="5.7"
NGINX_VERSION="default"
PHP_INSTALL="false"

echo "=========================================="
echo "🚀 XBoard Modern 优化安装脚本"
echo "=========================================="
echo ""

# 显示安装选项
show_options() {
    echo "请选择安装配置："
    echo ""
    echo "1. 数据库选择："
    echo "   [1] MySQL 5.7 (推荐，兼容性最好)"
    echo "   [2] MySQL 8.0 (性能更好，需要Python 3.8+)"
    echo "   [3] MariaDB 10.6+ (轻量级替代方案)"
    echo "   [4] SQLite (简单配置，适合测试)"
    echo ""
    echo "2. Nginx版本："
    echo "   [1] 系统默认版本 (稳定)"
    echo "   [2] 最新稳定版本 (性能更好)"
    echo ""
    echo "3. PHP安装："
    echo "   [1] 不安装PHP (推荐，XBoard不需要)"
    echo "   [2] 安装PHP 7.4 (兼容性最好)"
    echo "   [3] 安装PHP 8.0 (性能更好)"
    echo ""
}

# 获取用户选择
get_user_choice() {
    echo "请输入选择 (例如: 1,1,1 表示 MySQL 5.7 + 默认Nginx + 不安装PHP):"
    read -p "选择: " choice
    
    # 解析选择
    IFS=',' read -ra choices <<< "$choice"
    
    if [ ${#choices[@]} -eq 3 ]; then
        case "${choices[0]}" in
            1) DB_TYPE="mysql"; DB_VERSION="5.7" ;;
            2) DB_TYPE="mysql"; DB_VERSION="8.0" ;;
            3) DB_TYPE="mariadb"; DB_VERSION="10.6" ;;
            4) DB_TYPE="sqlite" ;;
            *) log_error "无效的数据库选择"; exit 1 ;;
        esac
        
        case "${choices[1]}" in
            1) NGINX_VERSION="default" ;;
            2) NGINX_VERSION="latest" ;;
            *) log_error "无效的Nginx选择"; exit 1 ;;
        esac
        
        case "${choices[2]}" in
            1) PHP_INSTALL="false" ;;
            2) PHP_INSTALL="7.4" ;;
            3) PHP_INSTALL="8.0" ;;
            *) log_error "无效的PHP选择"; exit 1 ;;
        esac
        
        log_success "选择确认："
        log_info "数据库: $DB_TYPE $DB_VERSION"
        log_info "Nginx: $NGINX_VERSION"
        log_info "PHP: $PHP_INSTALL"
        echo ""
    else
        log_error "选择格式错误，请使用逗号分隔的三个数字"
        exit 1
    fi
}

# 安装MySQL
install_mysql() {
    log_info "安装 $DB_TYPE $DB_VERSION..."
    
    case $DB_TYPE in
        "mysql")
            if [ "$DB_VERSION" = "5.7" ]; then
                # MySQL 5.7 (Ubuntu 18.04默认)
                apt install -y mysql-server-5.7 mysql-client-5.7
            elif [ "$DB_VERSION" = "8.0" ]; then
                # MySQL 8.0
                wget https://dev.mysql.com/get/mysql-apt-config_0.8.22-1_all.deb
                dpkg -i mysql-apt-config_0.8.22-1_all.deb
                apt update
                apt install -y mysql-server mysql-client
                rm mysql-apt-config_0.8.22-1_all.deb
            fi
            ;;
        "mariadb")
            # MariaDB
            apt install -y mariadb-server mariadb-client
            ;;
        "sqlite")
            # SQLite
            apt install -y sqlite3
            ;;
    esac
    
    log_success "$DB_TYPE 安装完成"
}

# 安装Nginx
install_nginx() {
    log_info "安装 Nginx..."
    
    if [ "$NGINX_VERSION" = "latest" ]; then
        # 最新稳定版本
        add-apt-repository ppa:nginx/stable -y
        apt update
        apt install -y nginx
    else
        # 系统默认版本
        apt install -y nginx
    fi
    
    log_success "Nginx 安装完成"
}

# 安装PHP (可选)
install_php() {
    if [ "$PHP_INSTALL" != "false" ]; then
        log_info "安装 PHP $PHP_INSTALL..."
        
        if [ "$PHP_INSTALL" = "7.4" ]; then
            # PHP 7.4
            apt install -y php7.4 php7.4-fpm php7.4-mysql php7.4-common php7.4-mbstring php7.4-xml php7.4-curl
        elif [ "$PHP_INSTALL" = "8.0" ]; then
            # PHP 8.0
            add-apt-repository ppa:ondrej/php -y
            apt update
            apt install -y php8.0 php8.0-fpm php8.0-mysql php8.0-common php8.0-mbstring php8.0-xml php8.0-curl
        fi
        
        log_success "PHP $PHP_INSTALL 安装完成"
    else
        log_info "跳过PHP安装 (XBoard项目不需要)"
    fi
}

# 配置MySQL
configure_mysql() {
    if [ "$DB_TYPE" != "sqlite" ]; then
        log_info "配置 $DB_TYPE..."
        
        # 启动服务
        systemctl start $DB_TYPE
        systemctl enable $DB_TYPE
        
        # 安全配置
        if [ "$DB_TYPE" = "mysql" ]; then
            mysql_secure_installation
        elif [ "$DB_TYPE" = "mariadb" ]; then
            mysql_secure_installation
        fi
        
        log_success "$DB_TYPE 配置完成"
    fi
}

# 配置Nginx
configure_nginx() {
    log_info "配置 Nginx..."
    
    # 备份默认配置
    cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
    
    # 创建XBoard站点配置
    cat > /etc/nginx/sites-available/xboard << 'EOF'
server {
    listen 80;
    server_name _;
    root /var/www/xboard/frontend/dist;
    index index.html;

    # 前端静态文件
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 上传文件
    location /uploads/ {
        alias /var/www/xboard/uploads/;
    }

    # PHP支持 (如果安装了PHP)
    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }
}
EOF

    # 启用站点
    ln -sf /etc/nginx/sites-available/xboard /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # 创建网站目录
    mkdir -p /var/www/xboard
    chown -R www-data:www-data /var/www/xboard
    
    # 测试配置
    nginx -t
    
    # 重启Nginx
    systemctl restart nginx
    systemctl enable nginx
    
    log_success "Nginx 配置完成"
}

# 显示配置信息
show_config_info() {
    echo ""
    echo "=========================================="
    echo "🎉 安装配置完成！"
    echo "=========================================="
    echo ""
    echo "📊 安装的组件："
    echo "   数据库: $DB_TYPE $DB_VERSION"
    echo "   Web服务器: Nginx ($NGINX_VERSION)"
    echo "   PHP: $PHP_INSTALL"
    echo ""
    echo "🔧 管理命令："
    if [ "$DB_TYPE" != "sqlite" ]; then
        echo "   数据库状态: systemctl status $DB_TYPE"
        echo "   重启数据库: systemctl restart $DB_TYPE"
    fi
    echo "   Nginx状态: systemctl status nginx"
    echo "   重启Nginx: systemctl restart nginx"
    if [ "$PHP_INSTALL" != "false" ]; then
        echo "   PHP状态: systemctl status php$PHP_INSTALL-fpm"
        echo "   重启PHP: systemctl restart php$PHP_INSTALL-fpm"
    fi
    echo ""
    echo "📁 网站目录: /var/www/xboard"
    echo "🌐 访问地址: http://$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip")"
    echo ""
    echo "⚠️  重要提醒："
    echo "   1. 数据库已配置安全设置"
    echo "   2. Nginx已配置反向代理到后端API"
    echo "   3. 如果安装了PHP，可以运行PHP应用"
    echo "   4. 建议配置SSL证书"
    echo ""
}

# 主函数
main() {
    # 检查root权限
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root用户运行此脚本"
        exit 1
    fi
    
    # 更新系统
    log_info "更新系统..."
    apt update && apt upgrade -y
    
    # 显示选项
    show_options
    
    # 获取用户选择
    get_user_choice
    
    # 安装组件
    install_mysql
    install_nginx
    install_php
    
    # 配置组件
    configure_mysql
    configure_nginx
    
    # 显示配置信息
    show_config_info
}

# 运行主函数
main "$@"
