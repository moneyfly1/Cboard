 #!/usr/bin/env python3
"""
XBoard Modern 项目完整性检查脚本
检查所有必要的文件是否存在且内容完整
"""

import os
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 必需的文件列表
REQUIRED_FILES = {
    # 后端核心文件
    "backend/main.py": "后端主入口文件",
    "backend/requirements.txt": "Python依赖文件",
    "backend/app/main.py": "应用主文件",
    "backend/app/core/config.py": "配置管理",
    "backend/app/core/database.py": "数据库配置",
    "backend/app/core/settings_manager.py": "设置管理器",
    
    # 后端API文件
    "backend/app/api/api_v1/api.py": "API路由配置",
    "backend/app/api/api_v1/endpoints/auth.py": "认证API",
    "backend/app/api/api_v1/endpoints/users.py": "用户API",
    "backend/app/api/api_v1/endpoints/subscriptions.py": "订阅API",
    "backend/app/api/api_v1/endpoints/orders.py": "订单API",
    "backend/app/api/api_v1/endpoints/packages.py": "套餐API",
    "backend/app/api/api_v1/endpoints/nodes.py": "节点API",
    "backend/app/api/api_v1/endpoints/admin.py": "管理API",
    "backend/app/api/api_v1/endpoints/notifications.py": "通知API",
    "backend/app/api/api_v1/endpoints/config.py": "配置API",
    "backend/app/api/api_v1/endpoints/statistics.py": "统计API",
    "backend/app/api/api_v1/endpoints/payment.py": "支付API",
    "backend/app/api/api_v1/endpoints/settings.py": "设置API",
    
    # 后端模型文件
    "backend/app/models/__init__.py": "模型初始化",
    "backend/app/models/user.py": "用户模型",
    "backend/app/models/subscription.py": "订阅模型",
    "backend/app/models/order.py": "订单模型",
    "backend/app/models/node.py": "节点模型",
    "backend/app/models/email.py": "邮件模型",
    "backend/app/models/payment.py": "支付模型",
    "backend/app/models/notification.py": "通知模型",
    "backend/app/models/config.py": "配置模型",
    
    # 后端Schema文件
    "backend/app/schemas/__init__.py": "Schema初始化",
    "backend/app/schemas/user.py": "用户Schema",
    "backend/app/schemas/subscription.py": "订阅Schema",
    "backend/app/schemas/order.py": "订单Schema",
    "backend/app/schemas/common.py": "通用Schema",
    "backend/app/schemas/payment.py": "支付Schema",
    "backend/app/schemas/notification.py": "通知Schema",
    "backend/app/schemas/config.py": "配置Schema",
    
    # 后端服务文件
    "backend/app/services/auth.py": "认证服务",
    "backend/app/services/user.py": "用户服务",
    "backend/app/services/subscription.py": "订阅服务",
    "backend/app/services/order.py": "订单服务",
    "backend/app/services/package.py": "套餐服务",
    "backend/app/services/node.py": "节点服务",
    "backend/app/services/email.py": "邮件服务",
    "backend/app/services/payment.py": "支付服务",
    "backend/app/services/notification.py": "通知服务",
    "backend/app/services/settings.py": "设置服务",
    
    # 后端工具文件
    "backend/app/utils/__init__.py": "工具初始化",
    "backend/app/utils/security.py": "安全工具",
    "backend/app/utils/email.py": "邮件工具",
    "backend/app/utils/device.py": "设备工具",
    
    # 前端核心文件
    "frontend/index.html": "前端入口HTML",
    "frontend/package.json": "前端依赖配置",
    "frontend/vite.config.js": "Vite配置",
    "frontend/src/main.js": "前端主入口",
    "frontend/src/App.vue": "前端主组件",
    
    # 前端路由和状态管理
    "frontend/src/router/index.js": "路由配置",
    "frontend/src/store/auth.js": "认证状态",
    "frontend/src/store/settings.js": "设置状态",
    
    # 前端工具和配置
    "frontend/src/utils/api.js": "API工具",
    "frontend/src/config/theme.js": "主题配置",
    
    # 前端样式
    "frontend/src/styles/global.scss": "全局样式",
    "frontend/src/styles/main.scss": "主样式",
    
    # 前端组件
    "frontend/src/components/layout/UserLayout.vue": "用户布局",
    "frontend/src/components/layout/AdminLayout.vue": "管理布局",
    "frontend/src/components/ThemeSettings.vue": "主题设置",
    
    # 前端用户页面
    "frontend/src/views/Login.vue": "登录页面",
    "frontend/src/views/Register.vue": "注册页面",
    "frontend/src/views/ForgotPassword.vue": "忘记密码",
    "frontend/src/views/ResetPassword.vue": "重置密码",
    "frontend/src/views/VerifyEmail.vue": "邮箱验证",
    "frontend/src/views/Dashboard.vue": "用户仪表板",
    "frontend/src/views/Subscription.vue": "订阅管理",
    "frontend/src/views/Devices.vue": "设备管理",
    "frontend/src/views/Packages.vue": "套餐购买",
    "frontend/src/views/Orders.vue": "订单记录",
    "frontend/src/views/Nodes.vue": "节点列表",
    "frontend/src/views/Profile.vue": "个人资料",
    "frontend/src/views/Help.vue": "帮助中心",
    "frontend/src/views/NotFound.vue": "404页面",
    
    # 前端管理页面
    "frontend/src/views/admin/Dashboard.vue": "管理仪表板",
    "frontend/src/views/admin/Users.vue": "用户管理",
    "frontend/src/views/admin/Subscriptions.vue": "订阅管理",
    "frontend/src/views/admin/Orders.vue": "订单管理",
    "frontend/src/views/admin/Packages.vue": "套餐管理",
    "frontend/src/views/admin/PaymentConfig.vue": "支付配置",
    "frontend/src/views/admin/Settings.vue": "系统设置",
    "frontend/src/views/admin/Notifications.vue": "通知管理",
    "frontend/src/views/admin/Config.vue": "配置管理",
    "frontend/src/views/admin/Statistics.vue": "数据统计",
    
    # 安装和配置脚本
    "install_complete.sh": "Linux安装脚本",
    "install_windows.bat": "Windows安装脚本",
    "uninstall.sh": "卸载脚本",
    "check_env.sh": "环境检查脚本",
    "start.sh": "启动脚本",
    "dev.sh": "开发脚本",
    "docker-compose.yml": "Docker配置",
    "env.example": "环境变量示例",
    "README.md": "项目说明文档",
}

# 必需目录列表
REQUIRED_DIRS = [
    "backend/app/api/api_v1/endpoints",
    "backend/app/core",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/services",
    "backend/app/utils",
    "frontend/src/components/layout",
    "frontend/src/views/admin",
    "frontend/src/store",
    "frontend/src/router",
    "frontend/src/utils",
    "frontend/src/config",
    "frontend/src/styles",
    "frontend/public",
    "docs",
    "nginx",
]

def check_file_exists(file_path, description):
    """检查文件是否存在且不为空"""
    full_path = PROJECT_ROOT / file_path
    
    if not full_path.exists():
        return False, f"❌ 缺失: {file_path} ({description})"
    
    if full_path.stat().st_size == 0:
        return False, f"⚠️  空文件: {file_path} ({description})"
    
    return True, f"✅ 存在: {file_path} ({description})"

def check_directory_exists(dir_path):
    """检查目录是否存在"""
    full_path = PROJECT_ROOT / dir_path
    
    if not full_path.exists():
        return False, f"❌ 缺失目录: {dir_path}"
    
    if not full_path.is_dir():
        return False, f"⚠️  不是目录: {dir_path}"
    
    return True, f"✅ 目录存在: {dir_path}"

def main():
    """主检查函数"""
    print("🔍 XBoard Modern 项目完整性检查")
    print("=" * 50)
    
    # 检查文件
    print("\n📁 检查文件:")
    file_issues = []
    for file_path, description in REQUIRED_FILES.items():
        exists, message = check_file_exists(file_path, description)
        print(message)
        if not exists:
            file_issues.append(file_path)
    
    # 检查目录
    print("\n📂 检查目录:")
    dir_issues = []
    for dir_path in REQUIRED_DIRS:
        exists, message = check_directory_exists(dir_path)
        print(message)
        if not exists:
            dir_issues.append(dir_path)
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 检查结果:")
    
    total_files = len(REQUIRED_FILES)
    total_dirs = len(REQUIRED_DIRS)
    missing_files = len(file_issues)
    missing_dirs = len(dir_issues)
    
    print(f"文件总数: {total_files}")
    print(f"缺失文件: {missing_files}")
    print(f"目录总数: {total_dirs}")
    print(f"缺失目录: {missing_dirs}")
    
    if missing_files == 0 and missing_dirs == 0:
        print("\n🎉 项目完整性检查通过！所有文件都存在。")
        return 0
    else:
        print("\n⚠️  发现以下问题:")
        
        if file_issues:
            print("\n缺失的文件:")
            for file_path in file_issues:
                print(f"  - {file_path}")
        
        if dir_issues:
            print("\n缺失的目录:")
            for dir_path in dir_issues:
                print(f"  - {dir_path}")
        
        print(f"\n请创建缺失的 {missing_files} 个文件和 {missing_dirs} 个目录。")
        return 1

if __name__ == "__main__":
    sys.exit(main())