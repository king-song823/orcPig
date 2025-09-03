#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前后端集成测试脚本
测试增强版后端API是否正常工作
"""

import requests
import json
from pathlib import Path

def test_enhanced_api():
    """测试增强版API接口"""
    print("🧪 测试增强版后端API接口")
    print("=" * 50)
    
    # API地址
    api_url = "http://localhost:8011/parse-docs"
    
    # 测试图片路径
    test_images = [
        "测试/身份证/e0a2074108be994c1ac6fe03c103c0cc.JPG",
        "测试/银行卡/99b7278fecbd6176545cd4529f6b366b.JPG"
    ]
    
    for image_path in test_images:
        if not Path(image_path).exists():
            print(f"❌ 测试图片不存在: {image_path}")
            continue
            
        print(f"\n📸 测试图片: {Path(image_path).name}")
        
        try:
            # 准备文件
            with open(image_path, 'rb') as f:
                files = {'files': f}
                
                # 发送请求
                response = requests.post(api_url, files=files, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ API调用成功")
                    print(f"📋 返回数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
                else:
                    print(f"❌ API调用失败: {response.status_code}")
                    print(f"错误信息: {response.text}")
                    
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败: 请确保增强版后端服务正在运行 (端口8011)")
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
        except Exception as e:
            print(f"❌ 其他错误: {e}")

def test_cors_headers():
    """测试CORS头设置"""
    print("\n🌐 测试CORS设置")
    print("=" * 50)
    
    try:
        # 发送OPTIONS预检请求
        response = requests.options("http://localhost:8011/parse-docs", 
                                  headers={'Origin': 'http://localhost:5173'})
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        print("✅ CORS头设置:")
        for header, value in cors_headers.items():
            print(f"  {header}: {value}")
            
        if cors_headers['Access-Control-Allow-Origin'] == 'http://localhost:5173':
            print("✅ CORS配置正确，前端可以正常访问")
        else:
            print("⚠️  CORS配置可能有问题")
            
    except Exception as e:
        print(f"❌ CORS测试失败: {e}")

if __name__ == "__main__":
    print("🚀 开始前后端集成测试")
    print("⏰ 请确保增强版后端服务正在运行: python3 app_enhanced.py")
    print()
    
    test_enhanced_api()
    test_cors_headers()
    
    print("\n🎉 测试完成!")
    print("\n📝 使用说明:")
    print("1. 启动增强版后端: cd backend && python3 app_enhanced.py")
    print("2. 启动前端服务: cd idcard-ocr-frontend && npm run dev")
    print("3. 访问前端页面: http://localhost:5173")
