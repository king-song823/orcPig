#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OCR识别功能
"""

import requests
import json
import os
from pathlib import Path

def test_recognition():
    """测试各种图片的识别功能"""
    
    # 测试图片路径
    test_images = {
        "身份证": "测试/身份证/b512bca6f5da75508be3c7887882e46b.JPG",
        "银行卡": "测试/银行卡/95d4c07fcbd5f873413baf5c9c022ffd.JPG", 
        "猪耳标": "测试/猪耳标/pig1.JPG",
        "系统截图": "测试/系统截图/45f30a67671ff9cb9e512ff49040e719.JPG"
    }
    
    # 检查图片是否存在
    for name, path in test_images.items():
        if not os.path.exists(path):
            print(f"❌ {name}图片不存在: {path}")
            continue
        print(f"✅ 找到{name}图片: {path}")
    
    print("\n" + "="*50)
    print("开始测试识别功能...")
    print("="*50)
    
    # 测试单个图片识别
    for name, image_path in test_images.items():
        if not os.path.exists(image_path):
            continue
            
        print(f"\n🔍 测试{name}识别...")
        
        try:
            with open(image_path, 'rb') as f:
                files = {'files': (os.path.basename(image_path), f, 'image/jpeg')}
                
                response = requests.post(
                    'http://localhost:8010/parse-docs',
                    files=files,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ {name}识别成功!")
                    print(f"   识别结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                else:
                    print(f"❌ {name}识别失败: {response.status_code}")
                    print(f"   错误信息: {response.text}")
                    
        except Exception as e:
            print(f"❌ {name}测试出错: {e}")
    
    # 测试多图混合识别
    print(f"\n🔍 测试多图混合识别...")
    
    try:
        files = []
        file_handles = []  # 保持文件句柄打开
        
        for name, image_path in test_images.items():
            if os.path.exists(image_path):
                f = open(image_path, 'rb')
                file_handles.append(f)  # 保存文件句柄
                files.append(('files', (os.path.basename(image_path), f, 'image/jpeg')))
        
        if files:
            response = requests.post(
                'http://localhost:8010/parse-docs',
                files=files,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 多图混合识别成功!")
                print(f"   识别结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            else:
                print(f"❌ 多图混合识别失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
        else:
            print("❌ 没有可用的测试图片")
            
        # 关闭所有文件句柄
        for f in file_handles:
            f.close()
            
    except Exception as e:
        print(f"❌ 多图混合识别测试出错: {e}")
        # 确保文件句柄被关闭
        for f in file_handles:
            try:
                f.close()
            except:
                pass

if __name__ == "__main__":
    print("🚀 OCR识别功能测试")
    print("请确保后端服务已启动 (python app.py)")
    print()
    
    # 检查后端服务是否运行
    try:
        response = requests.get('http://localhost:8010', timeout=5)
        print("✅ 后端服务正在运行")
    except:
        print("❌ 后端服务未运行，请先启动: python app.py")
        exit(1)
    
    test_recognition()
