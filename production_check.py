#!/usr/bin/env python3
"""
生产环境部署检查脚本
"""
import os
import sys
import subprocess
import sqlite3
from pathlib import Path
import json
from datetime import datetime


class ProductionChecker:
    """生产环境检查器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.total_checks = 0
    
    def check(self, name: str, condition: bool, error_msg: str = None, warning_msg: str = None):
        """执行检查"""
        self.total_checks += 1
        if condition:
            self.checks_passed += 1
            print(f"✅ {name}")
        else:
            if error_msg:
                self.errors.append(f"{name}: {error_msg}")
                print(f"❌ {name}: {error_msg}")
            if warning_msg:
                self.warnings.append(f"{name}: {warning_msg}")
                print(f"⚠️  {name}: {warning_msg}")
    
    def check_environment_variables(self):
        """检查环境变量"""
        print("\n🔍 检查环境变量...")
        
        required_vars = [
            "SECRET_KEY",
            "DATABASE_URL",
            "SMTP_HOST",
            "SMTP_USERNAME",
            "SMTP_PASSWORD"
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            self.check(
                f"环境变量 {var}",
                value is not None and value != "",
                f"环境变量 {var} 未设置或为空"
            )
        
        # 检查SECRET_KEY强度
        secret_key = os.getenv("SECRET_KEY", "")
        self.check(
            "SECRET_KEY 强度",
            len(secret_key) >= 32,
            "SECRET_KEY 长度不足32位，存在安全风险"
        )
        
        # 检查DEBUG模式
        debug = os.getenv("DEBUG", "False").lower()
        self.check(
            "DEBUG 模式",
            debug == "false",
            "生产环境不应启用DEBUG模式"
        )
    
    def check_database(self):
        """检查数据库"""
        print("\n🔍 检查数据库...")
        
        db_path = "xboard.db"
        self.check(
            "数据库文件存在",
            os.path.exists(db_path),
            "数据库文件不存在"
        )
        
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 检查表结构
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = [
                    "users", "subscriptions", "orders", "packages",
                    "payment_transactions", "system_configs"
                ]
                
                for table in required_tables:
                    self.check(
                        f"数据表 {table}",
                        table in tables,
                        f"缺少必要的数据表: {table}"
                    )
                
                # 检查数据库大小
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                self.check(
                    "数据库大小",
                    db_size > 0,
                    "数据库文件为空"
                )
                
                conn.close()
                
            except Exception as e:
                self.check(
                    "数据库连接",
                    False,
                    f"数据库连接失败: {str(e)}"
                )
    
    def check_file_permissions(self):
        """检查文件权限"""
        print("\n🔍 检查文件权限...")
        
        # 检查关键目录权限
        critical_dirs = [
            "uploads",
            "uploads/config",
            "uploads/logs",
            "uploads/backups"
        ]
        
        for dir_path in critical_dirs:
            if os.path.exists(dir_path):
                stat = os.stat(dir_path)
                # 检查目录权限（应该是755或更严格）
                mode = oct(stat.st_mode)[-3:]
                self.check(
                    f"目录权限 {dir_path}",
                    int(mode) <= 755,
                    f"目录 {dir_path} 权限过于宽松: {mode}"
                )
    
    def check_ssl_certificates(self):
        """检查SSL证书"""
        print("\n🔍 检查SSL配置...")
        
        # 检查是否强制HTTPS
        force_https = os.getenv("FORCE_HTTPS", "False").lower()
        self.check(
            "强制HTTPS",
            force_https == "true",
            warning_msg="生产环境建议启用强制HTTPS"
        )
    
    def check_security_headers(self):
        """检查安全配置"""
        print("\n🔍 检查安全配置...")
        
        # 检查安全头配置
        enable_security_headers = os.getenv("ENABLE_SECURITY_HEADERS", "True").lower()
        self.check(
            "安全头配置",
            enable_security_headers == "true",
            warning_msg="建议启用安全头配置"
        )
        
        # 检查密码策略
        min_password_length = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))
        self.check(
            "密码最小长度",
            min_password_length >= 8,
            warning_msg="密码最小长度建议至少8位"
        )
    
    def check_backup_configuration(self):
        """检查备份配置"""
        print("\n🔍 检查备份配置...")
        
        backup_dir = os.getenv("BACKUP_DIR", "uploads/backups")
        self.check(
            "备份目录存在",
            os.path.exists(backup_dir),
            warning_msg="备份目录不存在，建议创建"
        )
        
        auto_backup = os.getenv("AUTO_BACKUP_INTERVAL", "0")
        self.check(
            "自动备份配置",
            auto_backup != "0",
            warning_msg="建议配置自动备份"
        )
    
    def check_logging_configuration(self):
        """检查日志配置"""
        print("\n🔍 检查日志配置...")
        
        log_dir = os.getenv("LOG_DIR", "uploads/logs")
        self.check(
            "日志目录存在",
            os.path.exists(log_dir),
            warning_msg="日志目录不存在，建议创建"
        )
        
        log_level = os.getenv("LOG_LEVEL", "INFO")
        self.check(
            "日志级别",
            log_level in ["INFO", "WARNING", "ERROR"],
            warning_msg="生产环境日志级别建议设置为INFO或更严格"
        )
    
    def check_dependencies(self):
        """检查依赖"""
        print("\n🔍 检查依赖...")
        
        try:
            import fastapi
            import uvicorn
            import sqlalchemy
            import psutil
            print("✅ 核心依赖已安装")
            self.checks_passed += 1
        except ImportError as e:
            self.errors.append(f"缺少依赖: {str(e)}")
            print(f"❌ 缺少依赖: {str(e)}")
        
        self.total_checks += 1
    
    def check_ports(self):
        """检查端口占用"""
        print("\n🔍 检查端口占用...")
        
        try:
            import socket
            
            # 检查8000端口
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 8000))
            sock.close()
            
            self.check(
                "端口8000可用",
                result != 0,
                "端口8000已被占用"
            )
            
        except Exception as e:
            self.check(
                "端口检查",
                False,
                f"端口检查失败: {str(e)}"
            )
    
    def generate_report(self):
        """生成检查报告"""
        print("\n" + "="*50)
        print("📊 生产环境检查报告")
        print("="*50)
        
        success_rate = (self.checks_passed / self.total_checks * 100) if self.total_checks > 0 else 0
        
        print(f"总检查项: {self.total_checks}")
        print(f"通过检查: {self.checks_passed}")
        print(f"成功率: {success_rate:.1f}%")
        
        if self.errors:
            print(f"\n❌ 错误 ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠️  警告 ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # 生成JSON报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_checks": self.total_checks,
            "checks_passed": self.checks_passed,
            "success_rate": success_rate,
            "errors": self.errors,
            "warnings": self.warnings,
            "ready_for_production": len(self.errors) == 0
        }
        
        with open("production_check_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存到: production_check_report.json")
        
        if len(self.errors) == 0:
            print("\n🎉 恭喜！系统已准备好投入生产环境！")
            return True
        else:
            print(f"\n⚠️  发现 {len(self.errors)} 个错误，请修复后再部署到生产环境。")
            return False
    
    def run_all_checks(self):
        """运行所有检查"""
        print("🚀 开始生产环境检查...")
        print("="*50)
        
        self.check_environment_variables()
        self.check_database()
        self.check_file_permissions()
        self.check_ssl_certificates()
        self.check_security_headers()
        self.check_backup_configuration()
        self.check_logging_configuration()
        self.check_dependencies()
        self.check_ports()
        
        return self.generate_report()


def main():
    """主函数"""
    checker = ProductionChecker()
    success = checker.run_all_checks()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
