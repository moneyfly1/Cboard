# 软件订阅设备限制功能指南

## 概述

本系统已完全集成设备限制功能到软件订阅端点，支持所有主流订阅软件的设备识别和数量限制。当用户通过订阅软件（如Shadowrocket、Clash等）访问订阅地址时，系统会自动进行设备识别和限制检查。

## 订阅端点

### 1. SSR/V2Ray 订阅
```
GET /api/v1/subscriptions/ssr/{subscription_key}
```

### 2. Clash 订阅
```
GET /api/v1/subscriptions/clash/{subscription_key}
```

## 设备限制流程

### 1. 订阅访问检查流程
```
用户软件请求订阅 → 设备识别 → 设备限制检查 → 返回结果
```

### 2. 详细处理步骤

1. **接收订阅请求**
   - 获取User-Agent（软件标识）
   - 获取IP地址
   - 获取订阅密钥

2. **设备识别**
   - 解析User-Agent识别软件类型
   - 提取设备型号和操作系统信息
   - 生成设备指纹（不依赖IP地址）

3. **设备限制检查**
   - 检查订阅是否过期
   - 检查设备是否已存在
   - 检查设备数量是否超限

4. **返回结果**
   - 允许：返回订阅配置
   - 拒绝：返回HTML错误页面

## 支持的订阅软件

### iOS 软件
- **Shadowrocket** - 最流行的iOS代理客户端
- **Quantumult X** - 功能强大的iOS代理工具
- **Surge** - 专业级iOS网络调试工具
- **Loon** - 简洁的iOS代理客户端
- **Stash** - 现代化的iOS代理工具
- **Sparkle** - 轻量级iOS代理客户端

### Android 软件
- **Clash Meta for Android** - Android上的Clash客户端
- **Clash for Android** - 经典Android Clash客户端
- **V2rayNG** - 流行的Android V2Ray客户端
- **SagerNet** - 多协议Android代理客户端
- **Matsuri** - 高性能Android代理客户端
- **AnXray** - Android Xray客户端
- **Nekobox** - 现代化Android代理客户端

### Windows 软件
- **Clash for Windows** - Windows上的Clash客户端
- **v2rayN** - 流行的Windows V2Ray客户端
- **FlClash** - 轻量级Windows Clash客户端
- **Clash Verge** - 现代化Windows Clash客户端
- **ClashX** - Windows Clash客户端

### macOS 软件
- **ClashX Pro** - macOS上的专业Clash客户端
- **Clash for Mac** - macOS Clash客户端
- **Surge** - macOS专业网络调试工具

### Linux 软件
- **Clash for Linux** - Linux上的Clash客户端

## 设备识别特性

### 1. 精确设备识别
- **iPhone设备**: 识别具体型号（如iPhone 14 Pro Max）
- **iPad设备**: 识别具体型号（如iPad Pro 12.9）
- **Android设备**: 识别品牌和型号（如Samsung Galaxy S23）
- **Windows设备**: 识别操作系统版本
- **macOS设备**: 识别Mac型号和系统版本

### 2. 同设备不同IP处理
- 同一台设备在不同网络环境下订阅，识别为同一设备
- 不依赖IP地址进行设备识别
- 通过设备特征（软件、型号、系统）进行识别

### 3. 多设备同软件处理
- 不同设备使用相同软件，分别识别为不同设备
- 通过设备型号、操作系统版本等特征区分
- 避免误判为同一设备

## 错误处理

### 1. 设备数量限制错误
当设备数量达到限制时，返回HTML错误页面：
- 显示设备信息（软件名称、设备型号、操作系统）
- 提供解决方案建议
- 美观的错误页面设计

### 2. 订阅过期错误
当订阅过期时，返回HTML错误页面：
- 显示过期时间信息
- 提供续费链接
- 计算过期天数

### 3. 其他错误
- 订阅不存在：返回无效配置
- 服务器错误：返回无效配置

## 测试方法

### 1. 使用测试脚本
```bash
python3 test_software_subscription.py
```

### 2. 手动测试
使用curl命令模拟软件订阅：
```bash
# 测试SSR订阅
curl -H "User-Agent: Shadowrocket/2.2.8 (iPhone; iOS 16.6; Scale/3.00)" \
     http://localhost:8000/api/v1/subscriptions/ssr/your_subscription_key

# 测试Clash订阅
curl -H "User-Agent: ClashMetaForAndroid/2.8.12 (Android 13; SM-G991B)" \
     http://localhost:8000/api/v1/subscriptions/clash/your_subscription_key
```

### 3. 真实软件测试
1. 在订阅软件中添加订阅地址
2. 尝试更新订阅
3. 观察是否返回配置或错误页面

## 管理功能

### 1. 设备管理
- 查看所有用户设备
- 删除设备释放额度
- 允许/禁止设备访问

### 2. 访问日志
- 记录所有订阅访问
- 包含设备信息和访问结果
- 支持按时间、用户、设备类型筛选

### 3. 统计信息
- 设备使用统计
- 软件类型分布
- 访问成功率

## 配置说明

### 1. 设备限制配置
在订阅套餐中设置 `device_limit` 字段：
```python
subscription.device_limit = 5  # 允许5个设备
```

### 2. 软件识别规则
系统自动识别24种主流订阅软件，无需额外配置。

### 3. 错误页面模板
- `templates/error_device_limit.html` - 设备限制错误页面
- `templates/error_expired.html` - 订阅过期错误页面

## 部署步骤

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
python3 test_software_subscription.py
```

## 监控和维护

### 1. 日志监控
- 订阅访问日志
- 设备识别日志
- 错误处理日志

### 2. 性能监控
- 设备识别响应时间
- 数据库查询性能
- 错误率统计

### 3. 定期维护
- 清理过期设备记录
- 更新软件识别规则
- 优化设备识别算法

## 故障排除

### 1. 常见问题
- **设备识别不准确**: 检查软件识别规则
- **同设备被重复计算**: 检查设备指纹算法
- **设备删除后仍被限制**: 检查设备状态更新

### 2. 调试方法
- 查看服务器日志
- 使用测试脚本验证
- 检查数据库设备记录

### 3. 解决方案
- 更新软件识别规则
- 优化设备指纹算法
- 清理无效设备记录

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

---

**注意**: 本系统专门为软件订阅设计，不支持浏览器访问。所有订阅请求都应该通过订阅软件发起，系统会根据User-Agent自动识别软件类型并进行相应的设备限制处理。
