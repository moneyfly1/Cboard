#!/usr/bin/env python3
"""
软件识别规则初始化脚本
包含所有主流订阅软件的识别规则
"""

import sqlite3
from datetime import datetime

def init_software_rules():
    """初始化软件识别规则"""
    
    # 软件识别规则数据
    software_rules = [
        # iOS 订阅软件
        {
            'software_name': 'Shadowrocket',
            'software_category': 'ios',
            'user_agent_pattern': 'shadowrocket',
            'os_pattern': 'ios',
            'device_pattern': 'iphone|ipad',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'iOS 代理客户端 Shadowrocket'
        },
        {
            'software_name': 'Quantumult X',
            'software_category': 'ios',
            'user_agent_pattern': 'quantumult',
            'os_pattern': 'ios',
            'device_pattern': 'iphone|ipad',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'iOS 代理客户端 Quantumult X'
        },
        {
            'software_name': 'Surge',
            'software_category': 'ios',
            'user_agent_pattern': 'surge',
            'os_pattern': 'ios|macos',
            'device_pattern': 'iphone|ipad|macintosh',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'iOS/macOS 代理客户端 Surge'
        },
        {
            'software_name': 'Loon',
            'software_category': 'ios',
            'user_agent_pattern': 'loon',
            'os_pattern': 'ios',
            'device_pattern': 'iphone|ipad',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'iOS 代理客户端 Loon'
        },
        {
            'software_name': 'Stash',
            'software_category': 'ios',
            'user_agent_pattern': 'stash',
            'os_pattern': 'ios',
            'device_pattern': 'iphone|ipad',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'iOS 代理客户端 Stash'
        },
        {
            'software_name': 'Sparkle',
            'software_category': 'ios',
            'user_agent_pattern': 'sparkle',
            'os_pattern': 'ios',
            'device_pattern': 'iphone|ipad',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'iOS 代理客户端 Sparkle'
        },
        
        # Android 订阅软件
        {
            'software_name': 'Clash Meta for Android',
            'software_category': 'android',
            'user_agent_pattern': 'clashmetaforandroid',
            'os_pattern': 'android',
            'device_pattern': 'android',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'Android Clash Meta 客户端'
        },
        {
            'software_name': 'Clash for Android',
            'software_category': 'android',
            'user_agent_pattern': 'clashforandroid',
            'os_pattern': 'android',
            'device_pattern': 'android',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'Android Clash 客户端'
        },
        {
            'software_name': 'V2rayNG',
            'software_category': 'android',
            'user_agent_pattern': 'v2rayng',
            'os_pattern': 'android',
            'device_pattern': 'android',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'Android V2Ray 客户端'
        },
        {
            'software_name': 'SagerNet',
            'software_category': 'android',
            'user_agent_pattern': 'sagernet',
            'os_pattern': 'android',
            'device_pattern': 'android',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'Android 代理客户端 SagerNet'
        },
        {
            'software_name': 'Matsuri',
            'software_category': 'android',
            'user_agent_pattern': 'matsuri',
            'os_pattern': 'android',
            'device_pattern': 'android',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'Android 代理客户端 Matsuri'
        },
        {
            'software_name': 'AnXray',
            'software_category': 'android',
            'user_agent_pattern': 'anxray',
            'os_pattern': 'android',
            'device_pattern': 'android',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'Android Xray 客户端'
        },
        {
            'software_name': 'Nekobox',
            'software_category': 'android',
            'user_agent_pattern': 'nekobox',
            'os_pattern': 'android',
            'device_pattern': 'android',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'Android 代理客户端 Nekobox'
        },
        
        # Windows 订阅软件
        {
            'software_name': 'Clash for Windows',
            'software_category': 'windows',
            'user_agent_pattern': 'clashforwindows',
            'os_pattern': 'windows',
            'device_pattern': 'windows',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'Windows Clash 客户端'
        },
        {
            'software_name': 'v2rayN',
            'software_category': 'windows',
            'user_agent_pattern': 'v2rayn',
            'os_pattern': 'windows',
            'device_pattern': 'windows',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'Windows V2Ray 客户端'
        },
        {
            'software_name': 'FlClash',
            'software_category': 'windows',
            'user_agent_pattern': 'flclash',
            'os_pattern': 'windows',
            'device_pattern': 'windows',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'Windows FlClash 客户端'
        },
        {
            'software_name': 'Clash Verge',
            'software_category': 'windows',
            'user_agent_pattern': 'clash-verge',
            'os_pattern': 'windows',
            'device_pattern': 'windows',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'Windows Clash Verge 客户端'
        },
        {
            'software_name': 'ClashX',
            'software_category': 'windows',
            'user_agent_pattern': 'clashx',
            'os_pattern': 'windows',
            'device_pattern': 'windows',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'Windows ClashX 客户端'
        },
        
        # macOS 订阅软件
        {
            'software_name': 'ClashX Pro',
            'software_category': 'macos',
            'user_agent_pattern': 'clashxpro',
            'os_pattern': 'macos',
            'device_pattern': 'macintosh',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'macOS ClashX Pro 客户端'
        },
        {
            'software_name': 'Clash for Mac',
            'software_category': 'macos',
            'user_agent_pattern': 'clashformac',
            'os_pattern': 'macos',
            'device_pattern': 'macintosh',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'macOS Clash 客户端'
        },
        
        # Linux 订阅软件
        {
            'software_name': 'Clash for Linux',
            'software_category': 'linux',
            'user_agent_pattern': 'clashforlinux',
            'os_pattern': 'linux',
            'device_pattern': 'linux',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': 'Linux Clash 客户端'
        },
        
        # 通用订阅软件
        {
            'software_name': 'Clash Meta',
            'software_category': 'universal',
            'user_agent_pattern': 'clash.meta',
            'os_pattern': '',
            'device_pattern': '',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': '通用 Clash Meta 客户端'
        },
        {
            'software_name': 'V2Ray Core',
            'software_category': 'universal',
            'user_agent_pattern': 'v2ray-core',
            'os_pattern': '',
            'device_pattern': '',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': '通用 V2Ray Core 客户端'
        },
        {
            'software_name': 'Xray Core',
            'software_category': 'universal',
            'user_agent_pattern': 'xray-core',
            'os_pattern': '',
            'device_pattern': '',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'description': '通用 Xray Core 客户端'
        }
    ]
    
    # 连接数据库
    conn = sqlite3.connect('xboard.db')
    cursor = conn.cursor()
    
    try:
        # 创建软件规则表（如果不存在）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS software_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                software_name VARCHAR(100) NOT NULL,
                software_category VARCHAR(50) NOT NULL,
                user_agent_pattern VARCHAR(200) NOT NULL,
                os_pattern VARCHAR(100),
                device_pattern VARCHAR(100),
                version_pattern VARCHAR(100),
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 清空现有数据
        cursor.execute('DELETE FROM software_rules')
        
        # 插入软件规则
        for rule in software_rules:
            cursor.execute('''
                INSERT INTO software_rules (
                    software_name, software_category, user_agent_pattern,
                    os_pattern, device_pattern, version_pattern,
                    is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            ''', (
                rule['software_name'],
                rule['software_category'],
                rule['user_agent_pattern'],
                rule['os_pattern'],
                rule['device_pattern'],
                rule['version_pattern'],
                datetime.now(),
                datetime.now()
            ))
        
        conn.commit()
        print(f"成功初始化 {len(software_rules)} 条软件识别规则")
        
    except Exception as e:
        print(f"初始化软件规则失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    init_software_rules()
