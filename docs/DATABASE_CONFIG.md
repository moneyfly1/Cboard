# 数据库配置指南

## 📊 支持的数据库

XBoard Modern 支持以下数据库：

### 1. SQLite (开发环境推荐)
- **优点**: 轻量级，无需安装，适合开发
- **缺点**: 并发性能有限，不适合生产环境
- **适用场景**: 开发、测试、小型部署

### 2. MySQL/MariaDB (生产环境推荐)
- **优点**: 稳定可靠，性能优秀，生态完善
- **缺点**: 需要单独安装和配置
- **适用场景**: 生产环境，中大型部署

### 3. PostgreSQL (企业级推荐)
- **优点**: 功能强大，支持复杂查询，数据完整性好
- **缺点**: 配置相对复杂，学习成本较高
- **适用场景**: 企业级应用，复杂业务场景

## 🔧 数据库配置

### 1. SQLite 配置

#### 环境变量配置
```bash
# .env 文件
DATABASE_URL=sqlite:///./xboard.db
```

#### 特点
- 数据库文件存储在项目根目录
- 无需额外安装数据库服务
- 适合开发和测试环境

### 2. MySQL 配置

#### 安装MySQL
```bash
# CentOS
yum install -y mysql-server mysql-client

# Ubuntu/Debian
apt install -y mysql-server mysql-client

# 启动MySQL服务
systemctl start mysql
systemctl enable mysql
```

#### 创建数据库和用户
```sql
-- 登录MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE xboard_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER 'xboard_user'@'localhost' IDENTIFIED BY 'your_password';

-- 授权
GRANT ALL PRIVILEGES ON xboard_db.* TO 'xboard_user'@'localhost';
FLUSH PRIVILEGES;

-- 退出
EXIT;
```

#### 环境变量配置
```bash
# .env 文件
DATABASE_URL=mysql+pymysql://xboard_user:your_password@localhost:3306/xboard_db
```

#### 安装Python MySQL驱动
```bash
pip install pymysql
```

### 3. PostgreSQL 配置

#### 安装PostgreSQL
```bash
# CentOS
yum install -y postgresql postgresql-server postgresql-contrib

# Ubuntu/Debian
apt install -y postgresql postgresql-contrib

# 初始化数据库
postgresql-setup initdb

# 启动服务
systemctl start postgresql
systemctl enable postgresql
```

#### 创建数据库和用户
```sql
-- 切换到postgres用户
sudo -u postgres psql

-- 创建用户
CREATE USER xboard_user WITH PASSWORD 'your_password';

-- 创建数据库
CREATE DATABASE xboard_db OWNER xboard_user;

-- 授权
GRANT ALL PRIVILEGES ON DATABASE xboard_db TO xboard_user;

-- 退出
\q
```

#### 环境变量配置
```bash
# .env 文件
DATABASE_URL=postgresql://xboard_user:your_password@localhost:5432/xboard_db
```

#### 安装Python PostgreSQL驱动
```bash
pip install psycopg2-binary
```

## 🗄️ 数据库表结构

### 1. 用户相关表

#### users (用户表)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    reset_password_token VARCHAR(255),
    reset_password_expires DATETIME,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### subscriptions (订阅表)
```sql
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    package_id INTEGER NOT NULL,
    status ENUM('active', 'expired', 'cancelled') DEFAULT 'active',
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    traffic_used BIGINT DEFAULT 0,
    traffic_limit BIGINT NOT NULL,
    device_limit INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE
);
```

#### devices (设备表)
```sql
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    subscription_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    device_id VARCHAR(255) UNIQUE NOT NULL,
    device_type VARCHAR(50),
    last_active DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE
);
```

### 2. 订单相关表

#### packages (套餐表)
```sql
CREATE TABLE packages (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    duration_days INTEGER NOT NULL,
    traffic_limit_gb INTEGER NOT NULL,
    device_limit INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### orders (订单表)
```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    package_id INTEGER NOT NULL,
    order_no VARCHAR(100) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'paid', 'cancelled', 'refunded') DEFAULT 'pending',
    payment_method VARCHAR(50),
    payment_time DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE
);
```

### 3. 系统配置表

#### system_configs (系统配置表)
```sql
CREATE TABLE system_configs (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    config_type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### announcements (公告表)
```sql
CREATE TABLE announcements (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    type ENUM('info', 'warning', 'success', 'error') DEFAULT 'info',
    is_active BOOLEAN DEFAULT TRUE,
    is_pinned BOOLEAN DEFAULT FALSE,
    start_time DATETIME,
    end_time DATETIME,
    target_users ENUM('all', 'admin', 'user') DEFAULT 'all',
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);
```

### 4. 支付相关表

#### payment_configs (支付配置表)
```sql
CREATE TABLE payment_configs (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    config JSON NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### payment_transactions (支付交易表)
```sql
CREATE TABLE payment_transactions (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    order_id INTEGER NOT NULL,
    payment_config_id INTEGER NOT NULL,
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    payment_method VARCHAR(50) NOT NULL,
    status ENUM('pending', 'success', 'failed', 'cancelled') DEFAULT 'pending',
    gateway_response JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (payment_config_id) REFERENCES payment_configs(id) ON DELETE CASCADE
);
```

## 🔍 数据库索引优化

### 1. 用户表索引
```sql
-- 邮箱索引
CREATE INDEX idx_users_email ON users(email);

-- 用户名索引
CREATE INDEX idx_users_username ON users(username);

-- 管理员索引
CREATE INDEX idx_users_is_admin ON users(is_admin);

-- 活跃用户索引
CREATE INDEX idx_users_is_active ON users(is_active);
```

### 2. 订阅表索引
```sql
-- 用户ID索引
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);

-- 状态索引
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- 到期时间索引
CREATE INDEX idx_subscriptions_end_date ON subscriptions(end_date);

-- 复合索引
CREATE INDEX idx_subscriptions_user_status ON subscriptions(user_id, status);
```

### 3. 订单表索引
```sql
-- 用户ID索引
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- 订单号索引
CREATE INDEX idx_orders_order_no ON orders(order_no);

-- 状态索引
CREATE INDEX idx_orders_status ON orders(status);

-- 创建时间索引
CREATE INDEX idx_orders_created_at ON orders(created_at);
```

### 4. 设备表索引
```sql
-- 用户ID索引
CREATE INDEX idx_devices_user_id ON devices(user_id);

-- 设备ID索引
CREATE INDEX idx_devices_device_id ON devices(device_id);

-- 订阅ID索引
CREATE INDEX idx_devices_subscription_id ON devices(subscription_id);

-- 活跃设备索引
CREATE INDEX idx_devices_is_active ON devices(is_active);
```

## 🔄 数据库迁移

### 1. 使用Alembic进行迁移

#### 安装Alembic
```bash
pip install alembic
```

#### 初始化迁移
```bash
# 在项目根目录
alembic init migrations
```

#### 配置Alembic
编辑 `alembic.ini`:
```ini
[alembic]
script_location = migrations
sqlalchemy.url = mysql+pymysql://xboard_user:password@localhost/xboard_db
```

#### 创建迁移文件
```bash
alembic revision --autogenerate -m "Initial migration"
```

#### 执行迁移
```bash
alembic upgrade head
```

### 2. 手动迁移

#### 备份数据
```bash
# MySQL
mysqldump -u username -p xboard_db > backup.sql

# PostgreSQL
pg_dump -U username xboard_db > backup.sql
```

#### 执行SQL脚本
```bash
# MySQL
mysql -u username -p xboard_db < migration.sql

# PostgreSQL
psql -U username -d xboard_db -f migration.sql
```

## 📊 数据库监控

### 1. 性能监控

#### MySQL性能监控
```sql
-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';

-- 查看连接数
SHOW STATUS LIKE 'Threads_connected';

-- 查看查询缓存
SHOW STATUS LIKE 'Qcache_hits';
SHOW STATUS LIKE 'Qcache_inserts';
```

#### PostgreSQL性能监控
```sql
-- 查看活跃连接
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- 查看慢查询
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

-- 查看表大小
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 2. 备份策略

#### 自动备份脚本
```bash
#!/bin/bash
# backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/database"
DB_NAME="xboard_db"
DB_USER="xboard_user"
DB_PASS="your_password"

# 创建备份目录
mkdir -p $BACKUP_DIR

# MySQL备份
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME > $BACKUP_DIR/xboard_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/xboard_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "xboard_*.sql.gz" -mtime +7 -delete

echo "Database backup completed: xboard_$DATE.sql.gz"
```

#### 定时备份
```bash
# 添加到crontab
echo "0 2 * * * /path/to/backup_database.sh" | crontab -
```

## 🔧 故障排除

### 1. 连接问题

#### MySQL连接失败
```bash
# 检查MySQL服务状态
systemctl status mysql

# 检查端口监听
netstat -tlnp | grep 3306

# 检查用户权限
mysql -u root -p -e "SHOW GRANTS FOR 'xboard_user'@'localhost';"
```

#### PostgreSQL连接失败
```bash
# 检查PostgreSQL服务状态
systemctl status postgresql

# 检查端口监听
netstat -tlnp | grep 5432

# 检查pg_hba.conf配置
cat /var/lib/pgsql/data/pg_hba.conf
```

### 2. 性能问题

#### 慢查询优化
```sql
-- MySQL慢查询分析
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';

-- PostgreSQL查询分析
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
```

#### 索引优化
```sql
-- 查看表索引
SHOW INDEX FROM users;

-- 分析表
ANALYZE TABLE users;
```

### 3. 数据恢复

#### 从备份恢复
```bash
# MySQL恢复
mysql -u username -p xboard_db < backup.sql

# PostgreSQL恢复
psql -U username -d xboard_db < backup.sql
```

## 📝 最佳实践

### 1. 安全配置
- 使用强密码
- 限制数据库访问IP
- 定期更新数据库版本
- 启用SSL连接

### 2. 性能优化
- 合理使用索引
- 定期分析表
- 配置查询缓存
- 优化慢查询

### 3. 备份策略
- 定期自动备份
- 异地备份
- 测试恢复流程
- 监控备份状态

### 4. 监控告警
- 监控数据库连接数
- 监控磁盘空间
- 监控慢查询
- 设置告警阈值 