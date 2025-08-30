# XBoard Modern 智能安装指南

## 🚀 智能目录识别

现在安装脚本具有智能目录识别功能，可以在以下任意位置运行：

### 支持的运行位置

1. **项目根目录** (推荐)
   ```bash
   cd /path/to/xboard-modern
   ./install_complete.sh
   ```

2. **包含项目的父目录**
   ```bash
   cd /path/to/parent/directory
   ./xboard-modern/install_complete.sh
   ```

3. **任意目录** (自动查找)
   ```bash
   cd /any/directory
   /path/to/xboard-modern/install_complete.sh
   ```

## 📋 安装步骤

### 方法1: 使用完整安装脚本
```bash
# 在任何位置运行
chmod +x /path/to/xboard-modern/install_complete.sh
/path/to/xboard-modern/install_complete.sh
```

### 方法2: 使用修复安装脚本
```bash
# 在任何位置运行
chmod +x /path/to/xboard-modern/install_fix.sh
/path/to/xboard-modern/install_fix.sh
```

### 方法3: 测试目录识别
```bash
# 测试目录识别功能
chmod +x /path/to/xboard-modern/test_path_detection.sh
/path/to/xboard-modern/test_path_detection.sh
```

## 🔍 智能识别策略

脚本会按以下顺序尝试识别项目目录：

1. **策略1**: 检查当前目录是否包含 `backend/` 和 `frontend/` 目录
2. **策略2**: 检查当前目录是否包含 `xboard-modern/` 子目录
3. **策略3**: 检查脚本所在目录是否在项目内
4. **策略4**: 检查脚本父目录是否包含项目
5. **策略5**: 递归向上查找项目目录

## 📁 项目结构要求

项目必须包含以下文件和目录：
```
xboard-modern/
├── backend/
│   ├── requirements.txt
│   └── app/
├── frontend/
│   ├── package.json
│   └── src/
├── install_complete.sh
├── install_fix.sh
└── test_path_detection.sh
```

## 🛠️ 故障排除

### 问题1: 找不到项目目录
```bash
# 运行测试脚本查看详细信息
./test_path_detection.sh
```

### 问题2: 权限问题
```bash
# 给脚本添加执行权限
chmod +x install_complete.sh
chmod +x install_fix.sh
chmod +x test_path_detection.sh
```

### 问题3: Python依赖安装失败
```bash
# 手动安装依赖
cd /path/to/xboard-modern
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

## 📝 安装后配置

1. **配置环境变量**
   ```bash
   cp env.example .env
   nano .env  # 编辑数据库配置等
   ```

2. **初始化数据库**
   ```bash
   python init_database.py
   ```

3. **启动服务**
   ```bash
   # 后端
   python -m uvicorn app.main:app --reload
   
   # 前端 (新终端)
   cd frontend
   npm install
   npm run dev
   ```

## 🎯 使用示例

### 示例1: 在网站根目录安装
```bash
# 假设项目在 /www/wwwroot/new.moneyfly.top/xboard-modern
cd /www/wwwroot/new.moneyfly.top
./xboard-modern/install_complete.sh
```

### 示例2: 在任意目录安装
```bash
# 从任何位置运行
/home/user/xboard-modern/install_complete.sh
```

### 示例3: 测试安装
```bash
# 先测试目录识别
./test_path_detection.sh

# 如果测试通过，再运行安装
./install_complete.sh
```

## ✅ 验证安装

安装完成后，检查以下内容：

1. **Python环境**
   ```bash
   source venv/bin/activate
   python -c "import fastapi, uvicorn, sqlalchemy"
   ```

2. **项目文件**
   ```bash
   ls -la backend/
   ls -la frontend/
   ```

3. **配置文件**
   ```bash
   ls -la .env
   ls -la backend/requirements.txt
   ```

## 🆘 获取帮助

如果遇到问题，请：

1. 运行测试脚本：`./test_path_detection.sh`
2. 查看详细日志输出
3. 检查项目结构是否完整
4. 确认Python和Node.js环境

---

**注意**: 新版本的安装脚本会自动识别项目位置，无需手动指定路径！ 