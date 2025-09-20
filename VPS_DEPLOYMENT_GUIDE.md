# VPS部署稳定性解决方案

## 问题分析

### 1. 邮件队列服务器停止的原因
- **内存不足** - VPS资源限制导致进程被系统杀死
- **数据库连接超时** - 长时间无活动导致连接断开
- **异常处理不当** - 邮件发送失败时处理器崩溃
- **线程管理问题** - 多线程竞争导致死锁

### 2. 后端容易停止的原因
- **端口冲突** - 多个进程占用同一端口
- **资源竞争** - CPU/内存使用过高
- **依赖服务失败** - 数据库、Redis等服务不可用
- **配置问题** - 环境变量或配置文件错误

## VPS部署解决方案

### 1. 系统服务配置

#### 创建系统服务文件
```bash
sudo nano /etc/systemd/system/xboard-backend.service
```

```ini
[Unit]
Description=XBoard Backend Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/root/xboard
Environment=PATH=/root/xboard/venv/bin
Environment=PYTHONPATH=/root/xboard
Environment=DOMAIN_NAME=your-domain.com
Environment=SSL_ENABLED=true
ExecStart=/root/xboard/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=xboard-backend

# 资源限制
LimitNOFILE=65536
LimitNPROC=4096
MemoryLimit=1G
CPUQuota=200%

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/root/xboard

[Install]
WantedBy=multi-user.target
```

#### 启用服务
```bash
sudo systemctl daemon-reload
sudo systemctl enable xboard-backend
sudo systemctl start xboard-backend
sudo systemctl status xboard-backend
```

### 2. 邮件队列稳定性优化

#### 修改邮件队列处理器
```python
# 在 app/services/email_queue_processor.py 中添加
class EmailQueueProcessor:
    def __init__(self):
        # 增加稳定性配置
        self.max_memory_usage = 100 * 1024 * 1024  # 100MB
        self.connection_timeout = 30
        self.max_processing_time = 300  # 5分钟
        self.health_check_interval = 60  # 1分钟
```

#### 添加内存监控
```python
def _check_memory_usage(self):
    """检查内存使用情况"""
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    
    if memory_info.rss > self.max_memory_usage:
        logger.warning(f"内存使用过高: {memory_info.rss / 1024 / 1024:.2f}MB")
        return False
    return True
```

### 3. 数据库连接优化

#### 配置数据库连接池
```python
# 在 app/core/database.py 中
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,  # 1小时回收连接
    echo=False
)
```

### 4. 监控和自动恢复

#### 创建监控脚本
```bash
#!/bin/bash
# /root/xboard/monitor.sh

LOG_FILE="/root/xboard/monitor.log"
SERVICE_NAME="xboard-backend"

check_service() {
    if ! systemctl is-active --quiet $SERVICE_NAME; then
        echo "$(date): 服务未运行，尝试重启" >> $LOG_FILE
        systemctl restart $SERVICE_NAME
        sleep 10
        
        if systemctl is-active --quiet $SERVICE_NAME; then
            echo "$(date): 服务重启成功" >> $LOG_FILE
        else
            echo "$(date): 服务重启失败" >> $LOG_FILE
        fi
    fi
}

check_memory() {
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ $MEMORY_USAGE -gt 90 ]; then
        echo "$(date): 内存使用过高: ${MEMORY_USAGE}%" >> $LOG_FILE
        systemctl restart $SERVICE_NAME
    fi
}

check_disk() {
    DISK_USAGE=$(df /root | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $DISK_USAGE -gt 90 ]; then
        echo "$(date): 磁盘使用过高: ${DISK_USAGE}%" >> $LOG_FILE
        # 清理日志文件
        find /root/xboard -name "*.log" -mtime +7 -delete
    fi
}

# 主监控循环
while true; do
    check_service
    check_memory
    check_disk
    sleep 60
done
```

#### 设置监控定时任务
```bash
# 添加到 crontab
crontab -e

# 添加以下行
* * * * * /root/xboard/monitor.sh
```

### 5. 日志管理

#### 配置日志轮转
```bash
sudo nano /etc/logrotate.d/xboard
```

```
/root/xboard/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload xboard-backend
    endscript
}
```

### 6. 防火墙和安全

#### 配置防火墙
```bash
# 只开放必要端口
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
```

#### 配置Nginx反向代理
```nginx
# /etc/nginx/sites-available/xboard
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7. 性能优化

#### 系统优化
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化内核参数
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" >> /etc/sysctl.conf
sysctl -p
```

#### 应用优化
```python
# 在 app/main.py 中
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加中间件
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

### 8. 部署脚本

#### 创建部署脚本
```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 开始部署 XBoard 到 VPS..."

# 更新系统
apt update && apt upgrade -y

# 安装依赖
apt install -y python3 python3-pip python3-venv nginx ufw

# 创建项目目录
mkdir -p /root/xboard
cd /root/xboard

# 克隆代码
git clone https://github.com/moneyfly1/Cboard.git .

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cat > .env << EOF
DOMAIN_NAME=your-domain.com
SSL_ENABLED=true
DEBUG=false
HOST=0.0.0.0
PORT=8000
WORKERS=2
EOF

# 配置系统服务
cp xboard-backend.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable xboard-backend

# 配置Nginx
cp nginx.conf /etc/nginx/sites-available/xboard
ln -s /etc/nginx/sites-available/xboard /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 配置防火墙
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 启动服务
systemctl start xboard-backend
systemctl status xboard-backend

echo "✅ 部署完成！"
```

## 总结

通过以上配置，可以确保：

1. **服务稳定性** - 系统服务自动重启
2. **资源监控** - 内存和磁盘使用监控
3. **日志管理** - 自动日志轮转
4. **安全防护** - 防火墙和反向代理
5. **性能优化** - 系统参数调优

这样配置后，你的XBoard应用在VPS上将会非常稳定！