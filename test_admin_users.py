#!/usr/bin/env python3
"""
测试管理员用户列表API
"""

import requests
import json

def test_admin_users_api():
    """测试管理员用户列表API"""
    
    # 测试登录获取token
    login_url = "http://localhost:8000/api/v1/auth/login-json"
    login_data = {
        "username": "admin",  # 假设管理员用户名是admin
        "password": "admin123"  # 假设管理员密码是admin123
    }
    
    try:
        print("1. 测试管理员登录...")
        login_response = requests.post(login_url, json=login_data)
        print(f"登录响应状态码: {login_response.status_code}")
        print(f"登录响应内容: {login_response.text}")
        
        if login_response.status_code != 200:
            print("登录失败，无法继续测试")
            return
        
        login_result = login_response.json()
        if not login_result.get("success", True):
            print("登录失败:", login_result.get("message"))
            return
        
        token = login_result.get("data", {}).get("access_token")
        if not token:
            print("未获取到访问令牌")
            return
        
        print("登录成功，获取到访问令牌")
        
        # 测试获取用户列表
        users_url = "http://localhost:8000/api/v1/admin/users"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("\n2. 测试获取用户列表...")
        users_response = requests.get(users_url, headers=headers)
        print(f"用户列表响应状态码: {users_response.status_code}")
        print(f"用户列表响应内容: {users_response.text}")
        
        if users_response.status_code == 200:
            users_result = users_response.json()
            if users_result.get("success", True):
                users_data = users_result.get("data", {})
                users = users_data.get("users", [])
                total = users_data.get("total", 0)
                print(f"成功获取用户列表，共 {total} 个用户")
                for user in users:
                    print(f"  - 用户ID: {user.get('id')}, 用户名: {user.get('username')}, 邮箱: {user.get('email')}, 状态: {user.get('status')}")
            else:
                print("获取用户列表失败:", users_result.get("message"))
        else:
            print("获取用户列表请求失败")
            
    except requests.exceptions.ConnectionError:
        print("连接失败，请确保后端服务正在运行")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")

def test_admin_users_statistics():
    """测试管理员用户统计API"""
    
    # 测试登录获取token
    login_url = "http://localhost:8000/api/v1/auth/login-json"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        print("\n3. 测试用户统计API...")
        login_response = requests.post(login_url, json=login_data)
        
        if login_response.status_code != 200:
            print("登录失败，无法测试统计API")
            return
        
        login_result = login_response.json()
        token = login_result.get("data", {}).get("access_token")
        
        if not token:
            print("未获取到访问令牌")
            return
        
        # 测试获取用户统计
        stats_url = "http://localhost:8000/api/v1/admin/users/statistics"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        stats_response = requests.get(stats_url, headers=headers)
        print(f"用户统计响应状态码: {stats_response.status_code}")
        print(f"用户统计响应内容: {stats_response.text}")
        
        if stats_response.status_code == 200:
            stats_result = stats_response.json()
            if stats_result.get("success", True):
                stats_data = stats_result.get("data", {})
                print("成功获取用户统计信息:")
                print(f"  总用户数: {stats_data.get('total_users', 0)}")
                print(f"  活跃用户数: {stats_data.get('active_users', 0)}")
                print(f"  已验证用户数: {stats_data.get('verified_users', 0)}")
                print(f"  今日新增用户数: {stats_data.get('today_users', 0)}")
            else:
                print("获取用户统计失败:", stats_result.get("message"))
        else:
            print("获取用户统计请求失败")
            
    except Exception as e:
        print(f"测试用户统计API时出现错误: {e}")

if __name__ == "__main__":
    print("开始测试管理员用户列表API...")
    test_admin_users_api()
    test_admin_users_statistics()
    print("\n测试完成")
