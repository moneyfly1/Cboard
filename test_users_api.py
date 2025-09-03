#!/usr/bin/env python3
import requests
import json

# 测试用户列表API
def test_users_api():
    base_url = "http://localhost:8000/api/v1"
    
    # 首先尝试登录获取token
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        login_response = requests.post(f"{base_url}/auth/login-json", json=login_data)
        print(f"登录状态码: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            print(f"登录成功: {json.dumps(login_result, indent=2, ensure_ascii=False)}")
            
            # 获取token
            access_token = login_result.get("access_token")
            if access_token:
                print(f"获取到token: {access_token[:20]}...")
                
                # 使用token测试用户列表API
                headers = {"Authorization": f"Bearer {access_token}"}
                
                users_response = requests.get(f"{base_url}/admin/users", 
                                           headers=headers,
                                           params={"page": 1, "size": 20})
                
                print(f"用户列表状态码: {users_response.status_code}")
                
                if users_response.status_code == 200:
                    users_data = users_response.json()
                    print(f"用户列表数据: {json.dumps(users_data, indent=2, ensure_ascii=False)}")
                else:
                    print(f"用户列表错误: {users_response.text}")
            else:
                print("未获取到token")
        else:
            print(f"登录失败: {login_response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")

if __name__ == "__main__":
    test_users_api()
