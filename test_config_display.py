#!/usr/bin/env python3
"""
测试配置显示是否正确
"""

import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def test_config_display():
    """测试配置显示是否正确"""
    print("🚀 开始测试配置显示...")
    
    # 1. 登录获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("📝 正在登录...")
    login_response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        print(f"响应内容: {login_response.text}")
        return
    
    login_data = login_response.json()
    access_token = login_data.get("access_token")
    
    if not access_token:
        print("❌ 未获取到access_token")
        return
    
    print("✅ 登录成功")
    
    # 设置请求头
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 2. 测试系统配置API
    print("\n🔧 测试系统配置API...")
    try:
        response = requests.get(f"{BASE_URL}/admin/system-config", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 系统配置API正常")
            print(f"返回的数据结构:")
            print(f"  - success: {data.get('success')}")
            print(f"  - message: {data.get('message')}")
            print(f"  - data字段类型: {type(data.get('data'))}")
            if data.get('data'):
                config_data = data['data']
                print(f"  - 配置字段:")
                for key, value in config_data.items():
                    print(f"    {key}: {value}")
        else:
            print(f"❌ 系统配置API失败: {response.text}")
    except Exception as e:
        print(f"❌ 系统配置API异常: {e}")
    
    # 3. 测试邮件配置API
    print("\n📧 测试邮件配置API...")
    try:
        response = requests.get(f"{BASE_URL}/admin/email-config", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 邮件配置API正常")
            print(f"返回的数据结构:")
            print(f"  - success: {data.get('success')}")
            print(f"  - message: {data.get('message')}")
            print(f"  - data字段类型: {type(data.get('data'))}")
            if data.get('data'):
                config_data = data['data']
                print(f"  - 配置字段:")
                for key, value in config_data.items():
                    print(f"    {key}: {value}")
        else:
            print(f"❌ 邮件配置API失败: {response.text}")
    except Exception as e:
        print(f"❌ 邮件配置API异常: {e}")
    
    # 4. 测试Clash配置API
    print("\n⚡ 测试Clash配置API...")
    try:
        response = requests.get(f"{BASE_URL}/admin/clash-config", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Clash配置API正常")
            print(f"返回的数据结构:")
            print(f"  - success: {data.get('success')}")
            print(f"  - message: {data.get('message')}")
            print(f"  - data字段类型: {type(data.get('data'))}")
            if data.get('data'):
                config_data = data['data']
                print(f"  - 配置字段:")
                for key, value in config_data.items():
                    print(f"    {key}: {value}")
        else:
            print(f"❌ Clash配置API失败: {response.text}")
    except Exception as e:
        print(f"❌ Clash配置API异常: {e}")

if __name__ == "__main__":
    test_config_display()
