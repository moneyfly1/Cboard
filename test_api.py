#!/usr/bin/env python3
import requests
import json

# 测试用户列表API
def test_users_api():
    base_url = "http://localhost:8000/api/v1"
    
    # 测试获取用户列表
    try:
        response = requests.get(f"{base_url}/admin/users", params={
            "page": 1,
            "size": 20
        })
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误响应: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")

if __name__ == "__main__":
    test_users_api()
