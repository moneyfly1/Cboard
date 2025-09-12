# 设备数量限制解决方案

## 概述

本解决方案实现了完整的设备数量限制功能，解决了客户订阅地址的设备数量控制问题。系统能够精确识别订阅软件、设备型号，并实现智能的设备指纹识别。

## 核心功能

### 1. 设备识别与限制

- **订阅地址有效性检查**：基于客户到期时间限制
- **设备数量限制**：基于订阅套餐的设备数量限制
- **智能设备识别**：支持所有主流订阅软件的精确识别
- **设备指纹算法**：解决同设备不同IP的识别问题

### 2. 支持的订阅软件

#### iOS 软件
- Shadowrocket
- Quantumult X
- Surge
- Loon
- Stash
- Sparkle

#### Android 软件
- Clash Meta for Android
- Clash for Android
- V2rayNG
- SagerNet
- Matsuri
- AnXray
- Nekobox

#### Windows 软件
- Clash for Windows
- v2rayN
- FlClash
- Clash Verge
- ClashX

#### macOS 软件
- ClashX Pro
- Clash for Mac

#### Linux 软件
- Clash for Linux

#### 通用软件
- Clash Meta
- V2Ray Core
- Xray Core

### 3. 设备指纹算法

#### 改进的设备识别机制
```python
def generate_device_hash(self, user_agent: str, ip_address: str) -> str:
    """生成设备唯一标识 - 改进版本，解决同设备不同IP问题"""
    # 提取关键设备特征，不依赖IP地址
    device_features = []
    
    # 1. 软件名称和版本
    # 2. 操作系统信息
    # 3. 设备型号和品牌
    # 4. 从User-Agent中提取设备唯一标识符
    # 5. 如果无法提取足够特征，使用原始方法但排除IP
```

#### 设备特征提取
- 软件名称和版本
- 操作系统和版本
- 设备型号和品牌
- iPhone/iPad 设备标识
- Android 设备标识
- 软件版本信息

### 4. 同设备不同IP处理

#### 相似设备查找算法
```python
def _find_similar_device(self, subscription_id: int, device_info: Dict[str, str], user_agent: str):
    """查找相似设备 - 解决同设备不同IP问题"""
    # 1. 通过软件名称查找
    # 2. 通过设备型号查找
    # 3. 通过操作系统和版本查找
    # 4. 通过User-Agent中的关键特征查找
    # 5. 通过软件版本查找
```

### 5. 设备管理功能

#### 管理员功能
- 查看所有设备列表
- 删除设备释放额度
- 允许/禁止设备访问
- 查看设备访问日志
- 设备统计信息

#### API 端点
- `GET /api/v1/admin/devices` - 获取设备列表
- `DELETE /api/v1/admin/devices/{device_id}` - 删除设备
- `POST /api/v1/admin/devices/{device_id}/allow` - 允许设备
- `POST /api/v1/admin/devices/{device_id}/block` - 禁止设备
- `GET /api/v1/admin/access-logs` - 获取访问日志

### 6. 错误响应处理

#### 设备数量限制错误
- 返回 403 状态码
- 显示设备信息
- 提供解决方案建议
- 美观的错误页面

#### 订阅过期错误
- 返回 403 状态码
- 显示过期信息
- 提供续费链接
- 过期天数计算

## 技术实现

### 1. 数据库表结构

#### software_rules 表
```sql
CREATE TABLE software_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    software_name VARCHAR(100) NOT NULL,
    software_category VARCHAR(50) NOT NULL,
    user_agent_pattern VARCHAR(200) NOT NULL,
    os_pattern VARCHAR(100),
    device_pattern VARCHAR(100),
    version_pattern VARCHAR(100),
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### devices 表
```sql
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subscription_id INTEGER NOT NULL,
    device_hash VARCHAR(64) NOT NULL,
    device_fingerprint VARCHAR(64),
    device_name VARCHAR(200),
    device_type VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent TEXT,
    software_name VARCHAR(100),
    software_version VARCHAR(50),
    os_name VARCHAR(50),
    os_version VARCHAR(50),
    device_model VARCHAR(100),
    device_brand VARCHAR(50),
    is_allowed BOOLEAN DEFAULT 1,
    is_active BOOLEAN DEFAULT 1,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_access DATETIME DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2. 核心服务类

#### DeviceManager 类
- `generate_device_hash()` - 生成设备指纹
- `parse_user_agent()` - 解析User-Agent
- `check_subscription_access()` - 检查订阅访问权限
- `_find_similar_device()` - 查找相似设备
- `get_user_devices()` - 获取用户设备列表
- `delete_device()` - 删除设备
- `update_device_status()` - 更新设备状态

### 3. 设备识别流程

1. **接收订阅请求**
   - 获取User-Agent和IP地址
   - 验证订阅地址有效性

2. **设备信息解析**
   - 解析User-Agent获取软件信息
   - 提取设备型号和操作系统信息
   - 生成设备指纹

3. **设备检查**
   - 检查设备是否已存在
   - 如果不存在，查找相似设备
   - 更新设备访问信息

4. **设备数量限制检查**
   - 统计已允许的设备数量
   - 与订阅设备限制比较
   - 决定是否允许新设备

5. **响应处理**
   - 允许访问：返回订阅内容
   - 拒绝访问：返回错误页面

## 部署说明

### 1. 初始化软件规则
```bash
python3 init_software_rules.py
```

### 2. 启动服务
```bash
python3 main.py
```

### 3. 测试功能
```bash
python3 test_device_limits.py
```

## 配置说明

### 1. 设备限制配置
- 在订阅套餐中设置 `device_limit` 字段
- 支持动态调整设备数量限制
- 管理员可以临时增加设备数量

### 2. 软件识别规则
- 支持添加新的软件识别规则
- 支持正则表达式匹配
- 支持软件版本识别

### 3. 错误页面配置
- 自定义错误页面模板
- 支持多语言错误信息
- 支持品牌定制

## 监控和统计

### 1. 设备统计
- 总设备数量
- 允许设备数量
- 被拒绝设备数量
- 设备使用率

### 2. 访问日志
- 记录所有订阅访问
- 包含设备信息和访问结果
- 支持按时间、用户、设备类型筛选

### 3. 性能监控
- 设备识别响应时间
- 数据库查询性能
- 错误率统计

## 安全考虑

### 1. 设备指纹安全
- 使用SHA256哈希算法
- 不依赖IP地址避免误判
- 支持设备指纹更新

### 2. 访问控制
- 管理员权限验证
- API访问频率限制
- 敏感操作日志记录

### 3. 数据保护
- 设备信息加密存储
- 访问日志定期清理
- 用户隐私保护

## 故障排除

### 1. 常见问题
- 设备识别不准确
- 同设备被重复计算
- 设备删除后仍被限制

### 2. 解决方案
- 检查软件识别规则
- 验证设备指纹算法
- 清理无效设备记录

### 3. 调试工具
- 设备识别测试脚本
- 访问日志分析工具
- 设备统计报告

## 未来改进

### 1. 功能增强
- 支持更多订阅软件
- 智能设备分类
- 设备使用行为分析

### 2. 性能优化
- 设备识别缓存
- 数据库查询优化
- 异步处理支持

### 3. 用户体验
- 设备管理界面优化
- 移动端适配
- 实时通知功能
