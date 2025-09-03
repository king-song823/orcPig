#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多文件上传测试脚本
测试同时上传多张图片的识别效果
"""

import requests
import json
from pathlib import Path

def test_multiple_files():
    """测试多文件上传识别"""
    print("🧪 测试多文件上传识别")
    print("=" * 50)
    
    # API地址
    api_url = "http://localhost:8011/parse-docs"
    
    # 测试用例
    test_cases = [
        {
            "name": "两张银行卡",
            "files": [
                "测试/身份证/b838b3065e09d66f3bd56f73e2ad90b8.JPG",
                "测试/银行卡/fa13cf89c2fce2f4a363e5270d7805b6.JPG"
            ]
        },
        {
            "name": "身份证+银行卡",
            "files": [
                "测试/身份证/e0a2074108be994c1ac6fe03c103c0cc.JPG",
                "测试/银行卡/99b7278fecbd6176545cd4529f6b366b.JPG"
            ]
        },
        {
            "name": "三张银行卡",
            "files": [
                "测试/银行卡/99b7278fecbd6176545cd4529f6b366b.JPG",
                "测试/银行卡/fa13cf89c2fce2f4a363e5270d7805b6.JPG",
                "测试/银行卡/fdcba9c95497faa3916cf944ad2a8873.JPG"
            ]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 测试用例: {test_case['name']}")
        print("-" * 30)
        
        # 检查文件是否存在
        existing_files = []
        for file_path in test_case["files"]:
            if Path(file_path).exists():
                existing_files.append(file_path)
                print(f"✅ 文件存在: {Path(file_path).name}")
            else:
                print(f"❌ 文件不存在: {file_path}")
        
        if not existing_files:
            print("⚠️  没有可用的测试文件")
            continue
        
        try:
            # 准备文件
            files = []
            for file_path in existing_files:
                with open(file_path, 'rb') as f:
                    files.append(('files', (Path(file_path).name, f.read(), 'image/jpeg')))
            
            # 发送请求
            response = requests.post(api_url, files=files, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API调用成功")
                print(f"📋 返回数据:")
                print(f"  身份证号: {data.get('idNumber', '未识别')}")
                print(f"  姓名: {data.get('insuredPerson', '未识别')}")
                print(f"  银行名称: {data.get('bankName', '未识别')}")
                print(f"  卡号: {data.get('cardNumber', '未识别')}")
                
                # 分析结果
                id_recognized = data.get('idNumber') != '未识别'
                bank_recognized = data.get('bankName') != '未识别' and data.get('cardNumber') != '未识别'
                
                if id_recognized and bank_recognized:
                    print("🎉 身份证和银行卡都识别成功!")
                elif id_recognized:
                    print("✅ 身份证识别成功")
                elif bank_recognized:
                    print("✅ 银行卡识别成功")
                else:
                    print("❌ 识别失败")
                    
            else:
                print(f"❌ API调用失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败: 请确保增强版后端服务正在运行 (端口8011)")
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
        except Exception as e:
            print(f"❌ 其他错误: {e}")

if __name__ == "__main__":
    print("🚀 开始多文件上传测试")
    print("⏰ 请确保增强版后端服务正在运行: python3 app_enhanced.py")
    print()
    
    test_multiple_files()
    
    print("\n🎉 测试完成!")
