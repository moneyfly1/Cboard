# XBoard 后端稳定性解决方案

## 问题分析

后端服务容易停止和端口冲突的主要原因：

1. **进程管理不当** - 没有正确的进程监控和重启机制
2. **端口清理不彻底** - 进程异常退出时端口未正确释放
3. **资源竞争** - 多个进程同时尝试使用同一端口
4. **缺乏健康检查** - 无法及时发现服务异常

## 解决方案

### 1. 使用启动脚本管理服务

#### 基本使用
```bash
# 启动服务
./start_backend.sh start

# 停止服务
./start_backend.sh stop

# 重启服务
./start_backend.sh restart

# 检查状态
./start_backend.sh status

# 清理所有进程
./start_backend.sh clean
```

#### 特性
- ✅ 自动端口清理
- ✅ 进程PID管理
- ✅ 健康检查
- ✅ 日志记录
- ✅ 优雅关闭

### 2. 使用监控脚本

#### 启动监控
```bash
# 后台运行监控
nohup ./monitor_backend.sh > monitor.log 2>&1 &

# 查看监控日志
tail -f monitor.log
```

#### 监控特性
- ✅ 自动健康检查
- ✅ 自动重启失败服务
- ✅ 重启次数限制
- ✅ 冷却时间机制
- ✅ 详细日志记录

### 3. 使用Docker部署（推荐）

#### 构建和运行
```bash
# 构建镜像
docker build -t xboard-backend .

# 运行容器
docker run -d \
  --name xboard-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/xboard.db:/app/xboard.db \
  xboard-backend

# 使用Docker Compose
docker-compose up -d
```

#### Docker优势
- ✅ 进程隔离
- ✅ 自动重启
- ✅ 健康检查
- ✅ 资源限制
- ✅ 版本管理

### 4. 使用系统服务（Linux/macOS）

#### 安装系统服务
```bash
# 复制服务文件
sudo cp xboard-backend.service /etc/systemd/system/

# 重新加载systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable xboard-backend

# 启动服务
sudo systemctl start xboard-backend

# 查看状态
sudo systemctl status xboard-backend
```

## 最佳实践

### 1. 开发环境
```bash
# 使用启动脚本
./start_backend.sh start

# 开发时使用监控
./monitor_backend.sh
```

### 2. 生产环境
```bash
# 使用Docker Compose
docker-compose up -d

# 或使用系统服务
sudo systemctl start xboard-backend
```

### 3. 故障排除

#### 检查端口占用
```bash
lsof -i :8000
```

#### 强制清理端口
```bash
./start_backend.sh clean
```

#### 查看服务日志
```bash
# 启动脚本日志
tail -f backend.log

# 监控日志
tail -f monitor.log

# Docker日志
docker logs xboard-backend
```

## 配置优化

### 1. 环境变量
```bash
# 设置Python路径
export PYTHONPATH=/path/to/xboard

# 设置日志级别
export LOG_LEVEL=info
```

### 2. 系统限制
```bash
# 增加文件描述符限制
ulimit -n 65536

# 增加进程限制
ulimit -u 4096
```

### 3. 网络配置
```bash
# 检查防火墙
sudo ufw status

# 开放端口
sudo ufw allow 8000
```

## 监控和维护

### 1. 健康检查
```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查API文档
curl http://localhost:8000/docs
```

### 2. 性能监控
```bash
# 查看进程资源使用
ps aux | grep uvicorn

# 查看端口连接
netstat -tulpn | grep 8000
```

### 3. 日志管理
```bash
# 日志轮转
logrotate /etc/logrotate.d/xboard

# 清理旧日志
find . -name "*.log" -mtime +7 -delete
```

## 故障恢复

### 1. 服务无法启动
1. 检查端口占用：`lsof -i :8000`
2. 清理端口：`./start_backend.sh clean`
3. 检查依赖：`pip list`
4. 查看日志：`tail -f backend.log`

### 2. 服务频繁重启
1. 检查资源使用：`top` 或 `htop`
2. 检查内存：`free -h`
3. 检查磁盘：`df -h`
4. 调整重启策略

### 3. 性能问题
1. 增加工作进程：`--workers 4`
2. 调整超时设置
3. 优化数据库连接
4. 使用缓存

## 总结

通过以上解决方案，可以有效避免后端服务的停止和端口冲突问题：

1. **开发环境**：使用启动脚本 + 监控脚本
2. **测试环境**：使用Docker容器
3. **生产环境**：使用Docker Compose或系统服务

选择适合你环境的方案，确保服务的稳定运行。
