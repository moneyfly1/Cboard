-- 设备管理相关表结构

-- 1. 设备记录表
CREATE TABLE IF NOT EXISTS user_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subscription_id INTEGER NOT NULL,
    device_ua TEXT NOT NULL,  -- User-Agent + IP 组合
    device_hash TEXT NOT NULL,  -- UA的MD5哈希，用于快速查找
    ip_address TEXT NOT NULL,
    user_agent TEXT NOT NULL,
    software_name TEXT,  -- 识别的软件名称
    software_version TEXT,  -- 软件版本
    os_name TEXT,  -- 操作系统名称
    os_version TEXT,  -- 操作系统版本
    device_model TEXT,  -- 设备型号
    device_brand TEXT,  -- 设备品牌
    is_allowed BOOLEAN DEFAULT 1,  -- 是否允许订阅
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1,  -- 访问次数
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions (id) ON DELETE CASCADE,
    UNIQUE(device_hash)  -- 确保设备唯一性
);

-- 2. 软件识别规则表
CREATE TABLE IF NOT EXISTS software_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    software_name TEXT NOT NULL,
    software_category TEXT NOT NULL,  -- 分类：clash, v2ray, shadowrocket等
    user_agent_pattern TEXT NOT NULL,  -- User-Agent匹配模式
    os_pattern TEXT,  -- 操作系统匹配模式
    device_pattern TEXT,  -- 设备匹配模式
    version_pattern TEXT,  -- 版本匹配模式
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. 订阅访问日志表
CREATE TABLE IF NOT EXISTS subscription_access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL,
    device_id INTEGER,
    ip_address TEXT NOT NULL,
    user_agent TEXT NOT NULL,
    access_type TEXT NOT NULL,  -- 'allowed', 'blocked_expired', 'blocked_device_limit'
    response_status INTEGER NOT NULL,  -- HTTP状态码
    response_message TEXT,  -- 响应消息
    access_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions (id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES user_devices (id) ON DELETE SET NULL
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_devices_user_id ON user_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_user_devices_subscription_id ON user_devices(subscription_id);
CREATE INDEX IF NOT EXISTS idx_user_devices_device_hash ON user_devices(device_hash);
CREATE INDEX IF NOT EXISTS idx_user_devices_is_allowed ON user_devices(is_allowed);
CREATE INDEX IF NOT EXISTS idx_software_rules_pattern ON software_rules(user_agent_pattern);
CREATE INDEX IF NOT EXISTS idx_access_logs_subscription_id ON subscription_access_logs(subscription_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_access_time ON subscription_access_logs(access_time);

-- 插入常见的软件识别规则
INSERT INTO software_rules (software_name, software_category, user_agent_pattern, os_pattern, device_pattern, version_pattern) VALUES
-- Clash 系列
('Clash for Android', 'clash', 'clash', 'android', NULL, NULL),
('Clash for Windows', 'clash', 'clash', 'windows', NULL, NULL),
('ClashX', 'clash', 'clashx', 'macos', NULL, NULL),
('ClashX Pro', 'clash', 'clashx pro', 'macos', NULL, NULL),
('Clash Verge', 'clash', 'clash-verge', NULL, NULL, NULL),
('Clash Meta', 'clash', 'clash-meta', NULL, NULL, NULL),
('ClashN', 'clash', 'clashn', 'windows', NULL, NULL),
('Clash for Android (Meta)', 'clash', 'clash-meta', 'android', NULL, NULL),

-- V2Ray 系列
('V2rayN', 'v2ray', 'v2rayn', 'windows', NULL, NULL),
('V2rayNG', 'v2ray', 'v2rayng', 'android', NULL, NULL),
('V2rayU', 'v2ray', 'v2rayu', 'macos', NULL, NULL),
('V2rayX', 'v2ray', 'v2rayx', 'macos', NULL, NULL),
('V2rayA', 'v2ray', 'v2raya', 'linux', NULL, NULL),
('V2rayS', 'v2ray', 'v2rays', 'windows', NULL, NULL),

-- Shadowrocket 系列
('Shadowrocket', 'shadowrocket', 'shadowrocket', 'ios', NULL, NULL),
('Shadowrocket (iPhone)', 'shadowrocket', 'shadowrocket', 'ios', 'iphone', NULL),
('Shadowrocket (iPad)', 'shadowrocket', 'shadowrocket', 'ios', 'ipad', NULL),

-- Quantumult 系列
('Quantumult X', 'quantumult', 'quantumult x', 'ios', NULL, NULL),
('Quantumult', 'quantumult', 'quantumult', 'ios', NULL, NULL),

-- Surge 系列
('Surge', 'surge', 'surge', 'ios', NULL, NULL),
('Surge Mac', 'surge', 'surge', 'macos', NULL, NULL),

-- 其他常见软件
('Flclash', 'flclash', 'flclash', NULL, NULL, NULL),
('Mihomo', 'mihomo', 'mihomo', NULL, NULL, NULL),
('Stash', 'stash', 'stash', 'ios', NULL, NULL),
('Loon', 'loon', 'loon', 'ios', NULL, NULL),
('Potatso', 'potatso', 'potatso', 'ios', NULL, NULL),
('OneClick', 'oneclick', 'oneclick', 'android', NULL, NULL),
('SagerNet', 'sagernet', 'sagernet', 'android', NULL, NULL),
('Nekobox', 'nekobox', 'nekobox', 'android', NULL, NULL),
('V2Box', 'v2box', 'v2box', 'android', NULL, NULL),
('Pharos Pro', 'pharos', 'pharos', 'ios', NULL, NULL),
('Outline', 'outline', 'outline', NULL, NULL, NULL),
('WireGuard', 'wireguard', 'wireguard', NULL, NULL, NULL),
('OpenVPN', 'openvpn', 'openvpn', NULL, NULL, NULL),
('Shadowsocks', 'shadowsocks', 'shadowsocks', NULL, NULL, NULL),
('ShadowsocksR', 'shadowsocksr', 'shadowsocksr', NULL, NULL, NULL),
('Trojan', 'trojan', 'trojan', NULL, NULL, NULL),
('Trojan-Go', 'trojan-go', 'trojan-go', NULL, NULL, NULL),
('Hysteria', 'hysteria', 'hysteria', NULL, NULL, NULL),
('Hysteria2', 'hysteria2', 'hysteria2', NULL, NULL, NULL),
('NaiveProxy', 'naiveproxy', 'naiveproxy', NULL, NULL, NULL),
('Brook', 'brook', 'brook', NULL, NULL, NULL),
('V2Fly', 'v2fly', 'v2fly', NULL, NULL, NULL),
('Xray', 'xray', 'xray', NULL, NULL, NULL),
('Sing-Box', 'sing-box', 'sing-box', NULL, NULL, NULL),
('Clash.Meta', 'clash-meta', 'clash.meta', NULL, NULL, NULL),
('Clash Premium', 'clash-premium', 'clash-premium', NULL, NULL, NULL),
('Clash Core', 'clash-core', 'clash-core', NULL, NULL, NULL),
('Clash Tun', 'clash-tun', 'clash-tun', NULL, NULL, NULL),
('Clash Tun Premium', 'clash-tun-premium', 'clash-tun-premium', NULL, NULL, NULL),
('Clash Tun Meta', 'clash-tun-meta', 'clash-tun-meta', NULL, NULL, NULL),
('Clash Tun Core', 'clash-tun-core', 'clash-tun-core', NULL, NULL, NULL),
('Clash Tun Verge', 'clash-tun-verge', 'clash-tun-verge', NULL, NULL, NULL),
('Clash Tun N', 'clash-tun-n', 'clash-tun-n', NULL, NULL, NULL),
('Clash Tun Meta Android', 'clash-tun-meta', 'clash-tun-meta', 'android', NULL, NULL),
('Clash Tun Meta Windows', 'clash-tun-meta', 'clash-tun-meta', 'windows', NULL, NULL),
('Clash Tun Meta macOS', 'clash-tun-meta', 'clash-tun-meta', 'macos', NULL, NULL),
('Clash Tun Meta Linux', 'clash-tun-meta', 'clash-tun-meta', 'linux', NULL, NULL),
('Clash Tun Meta iOS', 'clash-tun-meta', 'clash-tun-meta', 'ios', NULL, NULL),
('Clash Tun Meta Android TV', 'clash-tun-meta', 'clash-tun-meta', 'android', 'tv', NULL),
('Clash Tun Meta Android Box', 'clash-tun-meta', 'clash-tun-meta', 'android', 'box', NULL),
('Clash Tun Meta Android Tablet', 'clash-tun-meta', 'clash-tun-meta', 'android', 'tablet', NULL),
('Clash Tun Meta Android Phone', 'clash-tun-meta', 'clash-tun-meta', 'android', 'phone', NULL),
('Clash Tun Meta Android Watch', 'clash-tun-meta', 'clash-tun-meta', 'android', 'watch', NULL),
('Clash Tun Meta Android Auto', 'clash-tun-meta', 'clash-tun-meta', 'android', 'auto', NULL),
('Clash Tun Meta Android Things', 'clash-tun-meta', 'clash-tun-meta', 'android', 'things', NULL),
('Clash Tun Meta Android Wear', 'clash-tun-meta', 'clash-tun-meta', 'android', 'wear', NULL),
('Clash Tun Meta Android TV Box', 'clash-tun-meta', 'clash-tun-meta', 'android', 'tv-box', NULL),
('Clash Tun Meta Android Set Top Box', 'clash-tun-meta', 'clash-tun-meta', 'android', 'set-top-box', NULL),
('Clash Tun Meta Android Media Player', 'clash-tun-meta', 'clash-tun-meta', 'android', 'media-player', NULL),
('Clash Tun Meta Android Game Console', 'clash-tun-meta', 'clash-tun-meta', 'android', 'game-console', NULL),
('Clash Tun Meta Android Car', 'clash-tun-meta', 'clash-tun-meta', 'android', 'car', NULL),
('Clash Tun Meta Android Home', 'clash-tun-meta', 'clash-tun-meta', 'android', 'home', NULL),
('Clash Tun Meta Android Enterprise', 'clash-tun-meta', 'clash-tun-meta', 'android', 'enterprise', NULL),
('Clash Tun Meta Android Education', 'clash-tun-meta', 'clash-tun-meta', 'android', 'education', NULL),
('Clash Tun Meta Android One', 'clash-tun-meta', 'clash-tun-meta', 'android', 'one', NULL),
('Clash Tun Meta Android Go', 'clash-tun-meta', 'clash-tun-meta', 'android', 'go', NULL),
('Clash Tun Meta Android Automotive', 'clash-tun-meta', 'clash-tun-meta', 'android', 'automotive', NULL),
('Clash Tun Meta Android TV OS', 'clash-tun-meta', 'clash-tun-meta', 'android', 'tv-os', NULL),
('Clash Tun Meta Android Things OS', 'clash-tun-meta', 'clash-tun-meta', 'android', 'things-os', NULL),
('Clash Tun Meta Android Wear OS', 'clash-tun-meta', 'clash-tun-meta', 'android', 'wear-os', NULL),
('Clash Tun Meta Android Auto OS', 'clash-tun-meta', 'clash-tun-meta', 'android', 'auto-os', NULL),
('Clash Tun Meta Android Home OS', 'clash-tun-meta', 'clash-tun-meta', 'android', 'home-os', NULL),
('Clash Tun Meta Android Enterprise OS', 'clash-tun-meta', 'clash-tun-meta', 'android', 'enterprise-os', NULL),
('Clash Tun Meta Android Education OS', 'clash-tun-meta', 'clash-tun-meta', 'android', 'education-os', NULL),
('Clash Tun Meta Android One OS', 'clash-tun-meta', 'clash-tun-meta', 'android', 'one-os', NULL),
('Clash Tun Meta Android Go OS', 'clash-tun-meta', 'clash-tun-meta', 'android', 'go-os', NULL),
('Clash Tun Meta Android Automotive OS', 'clash-tun-meta', 'clash-tun-meta', 'android', 'automotive-os', NULL);
