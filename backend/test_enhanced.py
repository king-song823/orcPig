#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版OCR识别效果
"""

import requests
import json
import os
import glob
from pathlib import Path

def test_enhanced_ocr():
    """测试增强版OCR识别效果"""
    
    # 测试图片路径
    test_images = {
        "身份证": "测试/身份证/b838b3065e09d66f3bd56f73e2ad90b8.JPG",  # 原版识别失败的图片
        "银行卡": "测试/银行卡/99b7278fecbd6176545cd4529f6b366b.JPG",  # 原版识别失败的图片
    }
    
    print("🚀 测试增强版OCR识别效果")
    print("="*50)
    
    for name, image_path in test_images.items():
        if not os.path.exists(image_path):
            print(f"❌ {name}图片不存在: {image_path}")
            continue
            
        print(f"\n🔍 测试{name}识别 (原版失败的图片)...")
        
        try:
            with open(image_path, 'rb') as f:
                files = {'files': (os.path.basename(image_path), f, 'image/jpeg')}
                
                # 测试增强版OCR
                response = requests.post(
                    'http://localhost:8011/parse-docs',
                    files=files,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 增强版{name}识别结果:")
                    if name == "身份证":
                        print(f"   姓名: {result.get('insuredPerson', '未识别')}")
                        print(f"   身份证号: {result.get('idNumber', '未识别')}")
                    elif name == "银行卡":
                        print(f"   银行名称: {result.get('bankName', '未识别')}")
                        print(f"   卡号: {result.get('cardNumber', '未识别')}")
                else:
                    print(f"❌ 增强版识别失败: {response.status_code}")
                    print(f"   错误信息: {response.text}")
                    
        except Exception as e:
            print(f"❌ 测试出错: {e}")

def compare_ocr_engines():
    """对比不同OCR引擎的识别效果"""
    
    print("\n🔍 对比不同OCR引擎识别效果...")
    print("="*50)
    
    # 测试图片
    test_image = "测试/身份证/b838b3065e09d66f3bd56f73e2ad90b8.JPG"
    
    if not os.path.exists(test_image):
        print(f"❌ 测试图片不存在: {test_image}")
        return
    
    print(f"📷 测试图片: {os.path.basename(test_image)}")
    
    # 测试原版OCR
    try:
        with open(test_image, 'rb') as f:
            files = {'files': (os.path.basename(test_image), f, 'image/jpeg')}
            
            response = requests.post(
                'http://localhost:8010/parse-docs',
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n📊 原版OCR结果:")
                print(f"   姓名: {result.get('insuredPerson', '未识别')}")
                print(f"   身份证号: {result.get('idNumber', '未识别')}")
            else:
                print(f"❌ 原版OCR失败: {response.status_code}")
                
    except Exception as e:
        print(f"❌ 原版OCR测试出错: {e}")
    
    # 测试增强版OCR
    try:
        with open(test_image, 'rb') as f:
            files = {'files': (os.path.basename(test_image), f, 'image/jpeg')}
            
            response = requests.post(
                'http://localhost:8011/parse-docs',
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n📊 增强版OCR结果:")
                print(f"   姓名: {result.get('insuredPerson', '未识别')}")
                print(f"   身份证号: {result.get('idNumber', '未识别')}")
            else:
                print(f"❌ 增强版OCR失败: {response.status_code}")
                
    except Exception as e:
        print(f"❌ 增强版OCR测试出错: {e}")

def main():
    print("🎯 增强版OCR识别效果测试")
    print("="*50)
    
    # 检查增强版服务是否运行
    try:
        response = requests.get('http://localhost:8011', timeout=5)
        print("✅ 增强版后端服务正在运行")
    except:
        print("❌ 增强版后端服务未运行，请先启动: python3 app_enhanced.py")
        return
    
    # 测试增强版OCR
    test_enhanced_ocr()
    
    # 对比不同引擎
    compare_ocr_engines()

if __name__ == "__main__":
    main()
