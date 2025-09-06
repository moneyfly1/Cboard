#!/usr/bin/env python3
"""
测试设备管理器
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.device_manager import DeviceManager

def test_device_manager():
    """测试设备管理器"""
    try:
        # 获取数据库连接
        db = next(get_db())
        
        # 创建设备管理器
        device_manager = DeviceManager(db)
        
        # 测试UA解析
        test_ua = "Clash for Android/1.18.0"
        device_info = device_manager.parse_user_agent(test_ua)
        print("设备信息解析结果:")
        print(f"  软件名称: {device_info.get('software_name')}")
        print(f"  软件分类: {device_info.get('software_category')}")
        print(f"  操作系统: {device_info.get('os_name')}")
        print(f"  系统版本: {device_info.get('os_version')}")
        print(f"  设备型号: {device_info.get('device_model')}")
        print(f"  设备品牌: {device_info.get('device_brand')}")
        
        # 测试设备哈希生成
        device_hash = device_manager.generate_device_hash(test_ua, "127.0.0.1")
        print(f"\n设备哈希: {device_hash}")
        
        # 测试软件规则获取
        rules = device_manager.get_software_rules()
        print(f"\n软件规则数量: {len(rules)}")
        if rules:
            print("前5个软件规则:")
            for i, rule in enumerate(rules[:5]):
                print(f"  {i+1}. {rule['software_name']} - {rule['software_category']}")
        
        print("\n设备管理器测试完成!")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    test_device_manager()
