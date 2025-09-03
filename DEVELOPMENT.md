# 🚀 XBoard 开发环境设置指南

## 📋 系统要求

- **Python**: 3.8+ (推荐 3.11+)
- **Node.js**: 16+ (推荐 18+)
- **npm**: 8+ 或 **yarn**: 1.22+
- **Git**: 最新版本

## 🔧 快速开始

### 方法1: 使用自动化脚本 (推荐)

#### Linux/macOS
```bash
chmod +x setup_environment.sh
./setup_environment.sh
```

#### Windows
```cmd
setup_environment.bat
```

### 方法2: 手动设置

#### 1. 克隆项目
```bash
git clone https://github.com/moneyfly1/xboard.git
cd xboard
```

#### 2. 创建Python虚拟环境
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate.bat
```

#### 3. 安装Python依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. 安装前端依赖
```bash
cd frontend
npm install
cd ..
```

#### 5. 配置环境变量
```bash
cp env.example .env
# 编辑 .env 文件，配置数据库、邮件等设置
```

## ⚙️ 环境配置

### 数据库配置
在 `.env` 文件中配置数据库连接：

```env
DATABASE_URL=sqlite:///./xboard.db
# 或者使用 MySQL/PostgreSQL
# DATABASE_URL=mysql://user:password@localhost/xboard
# DATABASE_URL=postgresql://user:password@localhost/xboard
```

### 邮件配置
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 安全配置
```env
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## 🚀 启动服务

### 1. 启动后端服务
```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate.bat  # Windows

# 启动服务
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端服务
```bash
cd frontend
npm run dev
```

### 3. 访问应用
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **前端应用**: http://localhost:5173

## 📊 数据库管理

### 初始化数据库
```bash
# 创建数据库表
python -c "from app.core.database import create_tables; create_tables()"

# 或者使用 Alembic 进行数据库迁移
alembic upgrade head
```

### 创建管理员用户
```bash
python add_test_users.py
```

## 🧪 测试

### 运行后端测试
```bash
# 激活虚拟环境
source venv/bin/activate

# 运行测试
python -m pytest tests/
```

### 运行前端测试
```bash
cd frontend
npm run test
```

## 📁 项目结构

```
xboard/
├── app/                    # 后端应用
│   ├── api/               # API路由
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── schemas/           # 数据验证
│   ├── services/          # 业务逻辑
│   └── utils/             # 工具函数
├── frontend/               # 前端应用
│   ├── src/               # 源代码
│   ├── public/            # 静态资源
│   └── package.json       # 依赖配置
├── uploads/                # 上传文件
├── static/                 # 静态资源
├── requirements.txt        # Python依赖
├── setup_environment.sh    # 环境设置脚本
└── README.md              # 项目说明
```

## 🔍 常见问题

### Q: 虚拟环境激活失败
**A**: 确保使用正确的激活命令：
- Linux/macOS: `source venv/bin/activate`
- Windows: `venv\Scripts\activate.bat`

### Q: 依赖安装失败
**A**: 尝试以下解决方案：
1. 升级 pip: `pip install --upgrade pip`
2. 使用国内镜像: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ -r requirements.txt`

### Q: 前端依赖安装失败
**A**: 尝试以下解决方案：
1. 清除 npm 缓存: `npm cache clean --force`
2. 删除 node_modules 并重新安装: `rm -rf node_modules && npm install`

### Q: 数据库连接失败
**A**: 检查以下配置：
1. 数据库服务是否启动
2. 连接字符串是否正确
3. 数据库用户权限是否足够

## 📚 相关文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Vue.js 官方文档](https://vuejs.org/)
- [Element Plus 组件库](https://element-plus.org/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支: `git checkout -b feature/AmazingFeature`
3. 提交更改: `git commit -m 'Add some AmazingFeature'`
4. 推送分支: `git push origin feature/AmazingFeature`
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 获取帮助

如果遇到问题，请：
1. 查看本文档
2. 搜索 [Issues](https://github.com/moneyfly1/xboard/issues)
3. 创建新的 Issue 描述问题
4. 联系项目维护者
