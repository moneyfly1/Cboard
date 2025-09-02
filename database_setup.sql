-- XBoard Modern 完整数据库结构
-- 支持 MySQL 和 PostgreSQL
-- 创建时间: 2024年

-- =============================================================================
-- 用户表 (Users)
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    avatar VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,

    INDEX idx_users_username (username),
    INDEX idx_users_email (email),
    INDEX idx_users_created_at (created_at)
);

-- =============================================================================
-- 套餐表 (Packages)
-- =============================================================================
CREATE TABLE IF NOT EXISTS packages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    original_price DECIMAL(10,2) NULL,
    duration_days INTEGER NOT NULL, -- 套餐有效期（天）
    device_limit INTEGER DEFAULT 3, -- 设备数量限制
    traffic_limit_gb INTEGER NULL, -- 流量限制（GB），NULL表示不限制
    speed_limit_mbps INTEGER NULL, -- 速度限制（Mbps），NULL表示不限制
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_packages_is_active (is_active),
    INDEX idx_packages_sort_order (sort_order)
);

-- =============================================================================
-- 订阅表 (Subscriptions)
-- =============================================================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    package_id INTEGER NULL,
    subscription_url VARCHAR(500) UNIQUE,
    status ENUM('active', 'expired', 'cancelled', 'pending') DEFAULT 'pending',
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP NULL,
    device_count INTEGER DEFAULT 0,
    max_devices INTEGER DEFAULT 3,
    traffic_used_gb DECIMAL(10,2) DEFAULT 0.00,
    traffic_limit_gb DECIMAL(10,2) NULL,
    last_used TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE SET NULL,
    INDEX idx_subscriptions_user_id (user_id),
    INDEX idx_subscriptions_status (status),
    INDEX idx_subscriptions_end_date (end_date),
    INDEX idx_subscriptions_created_at (created_at)
);

-- =============================================================================
-- 设备表 (Devices)
-- =============================================================================
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    subscription_id INTEGER NOT NULL,
    device_name VARCHAR(100),
    device_type VARCHAR(50), -- android, ios, windows, mac, linux
    device_model VARCHAR(100),
    os_version VARCHAR(50),
    app_version VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent TEXT,
    location VARCHAR(100),
    is_online BOOLEAN DEFAULT FALSE,
    last_seen TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
    INDEX idx_devices_subscription_id (subscription_id),
    INDEX idx_devices_is_online (is_online),
    INDEX idx_devices_last_seen (last_seen),
    INDEX idx_devices_created_at (created_at)
);

-- =============================================================================
-- 订单表 (Orders)
-- =============================================================================
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    package_id INTEGER NOT NULL,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    payment_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    status ENUM('pending', 'paid', 'cancelled', 'refunded') DEFAULT 'pending',
    payment_method VARCHAR(50), -- alipay, wechat, paypal, stripe, bank_transfer, crypto
    payment_config_id INTEGER NULL,
    notes TEXT,
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
    INDEX idx_orders_user_id (user_id),
    INDEX idx_orders_status (status),
    INDEX idx_orders_payment_method (payment_method),
    INDEX idx_orders_created_at (created_at),
    INDEX idx_orders_order_number (order_number)
);

-- =============================================================================
-- 支付交易表 (Payment Transactions)
-- =============================================================================
CREATE TABLE IF NOT EXISTS payment_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    transaction_id VARCHAR(100) UNIQUE,
    external_transaction_id VARCHAR(200), -- 第三方支付平台的交易ID
    payment_method VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    status ENUM('pending', 'success', 'failed', 'cancelled', 'refunded') DEFAULT 'pending',
    payment_data JSON, -- 支付请求数据
    callback_data JSON, -- 回调响应数据
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_payment_transactions_user_id (user_id),
    INDEX idx_payment_transactions_order_id (order_id),
    INDEX idx_payment_transactions_status (status),
    INDEX idx_payment_transactions_created_at (created_at),
    INDEX idx_payment_transactions_transaction_id (transaction_id)
);

-- =============================================================================
-- 支付配置表 (Payment Configs)
-- =============================================================================
CREATE TABLE IF NOT EXISTS payment_configs (
    id SERIAL PRIMARY KEY,
    pay_type VARCHAR(50) NOT NULL, -- alipay, wechat, paypal, stripe, bank_transfer, crypto
    app_id VARCHAR(100),
    merchant_private_key TEXT,
    alipay_public_key TEXT,
    wechat_app_id VARCHAR(100),
    wechat_mch_id VARCHAR(100),
    wechat_api_key VARCHAR(100),
    paypal_client_id VARCHAR(200),
    paypal_secret VARCHAR(200),
    stripe_publishable_key VARCHAR(200),
    stripe_secret_key VARCHAR(200),
    bank_name VARCHAR(100),
    account_name VARCHAR(100),
    account_number VARCHAR(100),
    wallet_address VARCHAR(200), -- 加密货币钱包地址
    status INTEGER DEFAULT 1, -- 1=启用, 0=禁用
    return_url VARCHAR(500),
    notify_url VARCHAR(500),
    sort_order INTEGER DEFAULT 0,
    config_json JSON, -- 扩展配置
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_payment_configs_pay_type (pay_type),
    INDEX idx_payment_configs_status (status),
    INDEX idx_payment_configs_sort_order (sort_order)
);

-- =============================================================================
-- 节点表 (Nodes)
-- =============================================================================
CREATE TABLE IF NOT EXISTS nodes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200),
    description TEXT,
    server_address VARCHAR(200) NOT NULL,
    port INTEGER NOT NULL,
    protocol VARCHAR(50) DEFAULT 'vmess', -- vmess, vless, trojan, shadowsocks
    uuid VARCHAR(100),
    alter_id INTEGER DEFAULT 0,
    security VARCHAR(50) DEFAULT 'auto',
    network VARCHAR(50) DEFAULT 'tcp', -- tcp, kcp, ws, h2, quic
    type VARCHAR(50) DEFAULT 'none',
    host VARCHAR(200),
    path VARCHAR(500),
    tls BOOLEAN DEFAULT FALSE,
    sni VARCHAR(200),
    alpn VARCHAR(100),
    fp VARCHAR(50),
    pbk VARCHAR(100),
    sid VARCHAR(100),
    spx VARCHAR(100),
    flow VARCHAR(50),
    encryption VARCHAR(50),
    password VARCHAR(100),
    method VARCHAR(50) DEFAULT 'aes-256-gcm',
    country VARCHAR(10),
    country_name VARCHAR(100),
    city VARCHAR(100),
    isp VARCHAR(100),
    status BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    traffic_limit_gb DECIMAL(10,2) NULL,
    traffic_used_gb DECIMAL(10,2) DEFAULT 0.00,
    user_limit INTEGER NULL,
    active_users INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_nodes_protocol (protocol),
    INDEX idx_nodes_status (status),
    INDEX idx_nodes_country (country),
    INDEX idx_nodes_sort_order (sort_order),
    INDEX idx_nodes_created_at (created_at)
);

-- =============================================================================
-- 通知表 (Notifications)
-- =============================================================================
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info', -- info, warning, error, success
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_notifications_user_id (user_id),
    INDEX idx_notifications_is_read (is_read),
    INDEX idx_notifications_type (type),
    INDEX idx_notifications_created_at (created_at)
);

-- =============================================================================
-- 邮件模板表 (Email Templates)
-- =============================================================================
CREATE TABLE IF NOT EXISTS email_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    subject VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    variables TEXT, -- JSON格式的变量说明
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_email_templates_name (name),
    INDEX idx_email_templates_is_active (is_active)
);

-- =============================================================================
-- 邮件队列表 (Email Queue)
-- =============================================================================
CREATE TABLE IF NOT EXISTS email_queue (
    id SERIAL PRIMARY KEY,
    to_email VARCHAR(100) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    template_name VARCHAR(100),
    variables JSON,
    priority INTEGER DEFAULT 0, -- 0=普通, 1=高, 2=紧急
    status ENUM('pending', 'sending', 'sent', 'failed') DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    scheduled_at TIMESTAMP NULL,
    sent_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_email_queue_status (status),
    INDEX idx_email_queue_priority (priority),
    INDEX idx_email_queue_scheduled_at (scheduled_at),
    INDEX idx_email_queue_created_at (created_at)
);

-- =============================================================================
-- 系统配置表 (System Configs)
-- =============================================================================
CREATE TABLE IF NOT EXISTS system_configs (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    config_type VARCHAR(50) DEFAULT 'string', -- string, number, boolean, json
    description VARCHAR(500),
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_system_configs_config_key (config_key),
    INDEX idx_system_configs_is_public (is_public)
);

-- =============================================================================
-- 公告表 (Announcements)
-- =============================================================================
CREATE TABLE IF NOT EXISTS announcements (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info', -- info, warning, error, success
    is_active BOOLEAN DEFAULT TRUE,
    start_date TIMESTAMP NULL,
    end_date TIMESTAMP NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_announcements_is_active (is_active),
    INDEX idx_announcements_start_date (start_date),
    INDEX idx_announcements_end_date (end_date),
    INDEX idx_announcements_sort_order (sort_order)
);

-- =============================================================================
-- 主题配置表 (Theme Configs)
-- =============================================================================
CREATE TABLE IF NOT EXISTS theme_configs (
    id SERIAL PRIMARY KEY,
    theme_name VARCHAR(100) NOT NULL UNIQUE,
    theme_config JSON NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_theme_configs_theme_name (theme_name),
    INDEX idx_theme_configs_is_default (is_default),
    INDEX idx_theme_configs_is_active (is_active)
);

-- =============================================================================
-- 用户活动记录表 (User Activities)
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL, -- login, logout, password_change, profile_update, etc.
    description TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    location VARCHAR(100),
    device_info JSON,
    session_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_activities_user_id (user_id),
    INDEX idx_user_activities_action (action),
    INDEX idx_user_activities_created_at (created_at)
);

-- =============================================================================
-- 登录历史表 (Login History)
-- =============================================================================
CREATE TABLE IF NOT EXISTS login_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_time TIMESTAMP NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    location VARCHAR(100),
    device_fingerprint VARCHAR(100),
    session_duration INTEGER NULL, -- 秒
    login_result ENUM('success', 'failed') DEFAULT 'success',
    failure_reason VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_login_history_user_id (user_id),
    INDEX idx_login_history_login_time (login_time),
    INDEX idx_login_history_login_result (login_result)
);

-- =============================================================================
-- 订阅重置记录表 (Subscription Resets)
-- =============================================================================
CREATE TABLE IF NOT EXISTS subscription_resets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    subscription_id INTEGER NOT NULL,
    old_url VARCHAR(500),
    new_url VARCHAR(500),
    reset_reason VARCHAR(200),
    device_count INTEGER DEFAULT 0,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
    INDEX idx_subscription_resets_user_id (user_id),
    INDEX idx_subscription_resets_subscription_id (subscription_id),
    INDEX idx_subscription_resets_created_at (created_at)
);

-- =============================================================================
-- 支付回调表 (Payment Callbacks)
-- =============================================================================
CREATE TABLE IF NOT EXISTS payment_callbacks (
    id SERIAL PRIMARY KEY,
    payment_transaction_id INTEGER NOT NULL,
    callback_type VARCHAR(50) NOT NULL, -- notify, return, webhook
    callback_data JSON NOT NULL,
    raw_request TEXT,
    processed BOOLEAN DEFAULT FALSE,
    processing_result VARCHAR(50), -- success, failed, pending
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (payment_transaction_id) REFERENCES payment_transactions(id) ON DELETE CASCADE,
    INDEX idx_payment_callbacks_payment_transaction_id (payment_transaction_id),
    INDEX idx_payment_callbacks_callback_type (callback_type),
    INDEX idx_payment_callbacks_processed (processed),
    INDEX idx_payment_callbacks_created_at (created_at)
);

-- =============================================================================
-- 初始化默认数据
-- =============================================================================

-- 插入默认系统配置
INSERT IGNORE INTO system_configs (config_key, config_value, config_type, description) VALUES
('site_name', 'XBoard Modern', 'string', '网站名称'),
('site_description', '现代化订阅管理系统', 'string', '网站描述'),
('admin_email', 'admin@xboard.local', 'string', '管理员邮箱'),
('max_devices_per_user', '5', 'number', '每个用户最大设备数'),
('subscription_renewal_reminder_days', '7', 'number', '订阅续费提醒天数'),
('email_verification_required', 'true', 'boolean', '是否需要邮箱验证'),
('registration_enabled', 'true', 'boolean', '是否允许用户注册');

-- 插入默认主题配置
INSERT IGNORE INTO theme_configs (theme_name, theme_config, is_default) VALUES
('default', '{
  "primary_color": "#409eff",
  "secondary_color": "#67c23a",
  "text_color": "#303133",
  "background_color": "#ffffff",
  "sidebar_color": "#f5f5f5"
}', true);

-- 插入默认邮件模板
INSERT IGNORE INTO email_templates (name, subject, content, variables) VALUES
('user_registration', '欢迎注册 XBoard Modern', '<h1>欢迎来到 XBoard Modern</h1><p>您好，{{username}}！</p><p>感谢您注册我们的服务。</p><p>请点击以下链接验证您的邮箱：</p><p><a href="{{verification_url}}">验证邮箱</a></p>', '["username", "verification_url"]'),
('password_reset', '密码重置请求', '<h1>密码重置</h1><p>您好，{{username}}！</p><p>您请求重置密码，请点击以下链接：</p><p><a href="{{reset_url}}">重置密码</a></p><p>如果这不是您本人操作，请忽略此邮件。</p>', '["username", "reset_url"]'),
('subscription_expiring', '订阅即将到期提醒', '<h1>订阅到期提醒</h1><p>您好，{{username}}！</p><p>您的订阅将在 {{days_left}} 天后到期。</p><p>到期时间：{{expiry_date}}</p><p>请及时续费以免影响使用。</p>', '["username", "days_left", "expiry_date"]'),
('order_confirmed', '订单确认通知', '<h1>订单确认</h1><p>您好，{{username}}！</p><p>您的订单已确认：</p><p>订单号：{{order_number}}</p><p>金额：{{amount}} {{currency}}</p><p>套餐：{{package_name}}</p>', '["username", "order_number", "amount", "currency", "package_name"]');

-- 插入默认公告
INSERT IGNORE INTO announcements (title, content, type, is_active) VALUES
('欢迎使用 XBoard Modern', '感谢您选择我们的服务！如果您有任何问题，请随时联系我们。', 'info', true);

-- 插入示例套餐数据
INSERT IGNORE INTO packages (name, description, price, duration_days, device_limit, is_active, sort_order) VALUES
('基础套餐', '适合个人用户的基础订阅套餐', 19.90, 30, 3, true, 1),
('高级套餐', '适合重度用户的完整功能套餐', 39.90, 30, 5, true, 2),
('企业套餐', '适合团队使用的企业级套餐', 99.90, 30, 10, true, 3);

-- 插入默认支付配置
INSERT IGNORE INTO payment_configs (pay_type, app_id, status, return_url, notify_url) VALUES
('alipay', '', 1, '/api/v1/payment/alipay/return', '/api/v1/payment/alipay/notify'),
('wechat', '', 1, '/api/v1/payment/wechat/return', '/api/v1/payment/wechat/notify'),
('paypal', '', 1, '', ''),
('stripe', '', 1, '', ''),
('bank_transfer', '', 1, '', ''),
('crypto', '', 1, '', '');

-- =============================================================================
-- 创建索引优化查询性能
-- =============================================================================

-- 为常用查询创建复合索引
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status ON subscriptions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_end_date ON subscriptions(user_id, end_date);
CREATE INDEX IF NOT EXISTS idx_devices_subscription_online ON devices(subscription_id, is_online);
CREATE INDEX IF NOT EXISTS idx_orders_user_status_date ON orders(user_id, status, created_at);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_order_status ON payment_transactions(order_id, status);
CREATE INDEX IF NOT EXISTS idx_email_queue_status_priority ON email_queue(status, priority, scheduled_at);

COMMIT;
