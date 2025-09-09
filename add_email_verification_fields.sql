-- 添加邮箱验证和密码重置字段到用户表
-- 执行此脚本前请备份数据库

-- 添加邮箱验证相关字段
ALTER TABLE users ADD COLUMN verification_token VARCHAR(255) NULL;
ALTER TABLE users ADD COLUMN verification_expires DATETIME NULL;

-- 添加密码重置相关字段
ALTER TABLE users ADD COLUMN reset_token VARCHAR(255) NULL;
ALTER TABLE users ADD COLUMN reset_expires DATETIME NULL;

-- 创建索引以提高查询性能
CREATE INDEX idx_users_verification_token ON users(verification_token);
CREATE INDEX idx_users_reset_token ON users(reset_token);

-- 更新现有用户的验证状态（可选）
-- 如果希望现有用户也需要重新验证，可以执行：
-- UPDATE users SET is_verified = 0 WHERE is_verified = 1;

-- 显示表结构确认
PRAGMA table_info(users);
