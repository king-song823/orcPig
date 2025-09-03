#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断OCR识别失败的原因
"""

import requests
import json
import os
import glob
from pathlib import Path

def get_raw_ocr_result(image_path):
    """获取图片的原始OCR结果，不进行任何后处理"""
    try:
        with open(image_path, 'rb') as f:
            files = {'files': (os.path.basename(image_path), f, 'image/jpeg')}
            
            response = requests.post(
                'http://localhost:8010/parse-docs',
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
    except Exception as e:
        return f"请求错误: {e}"

def analyze_image_quality(image_path):
    """分析图片质量"""
    import cv2
    import numpy as np
    
    try:
        img = cv2.imread(image_path)
        if img is None:
            return "无法读取图片"
        
        # 获取图片基本信息
        height, width = img.shape[:2]
        channels = img.shape[2] if len(img.shape) > 2 else 1
        
        # 计算图片清晰度（拉普拉斯方差）
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if channels > 1 else img
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 计算图片亮度
        brightness = np.mean(gray)
        
        # 计算图片对比度
        contrast = np.std(gray)
        
        return {
            "尺寸": f"{width}x{height}",
            "通道数": channels,
            "清晰度": f"{laplacian_var:.2f}",
            "亮度": f"{brightness:.2f}",
            "对比度": f"{contrast:.2f}",
            "文件大小": f"{os.path.getsize(image_path) / 1024:.1f}KB"
        }
        
    except Exception as e:
        return f"分析失败: {e}"

def diagnose_id_card_failures():
    """诊断身份证识别失败的原因"""
    print("🔍 诊断身份证识别失败原因...")
    print("="*50)
    
    id_card_images = glob.glob("测试/身份证/*.JPG")
    
    for image_path in id_card_images:
        print(f"\n📷 分析图片: {os.path.basename(image_path)}")
        print("-" * 40)
        
        # 分析图片质量
        quality_info = analyze_image_quality(image_path)
        print("📊 图片质量分析:")
        if isinstance(quality_info, dict):
            for key, value in quality_info.items():
                print(f"   {key}: {value}")
        else:
            print(f"   {quality_info}")
        
        # 获取OCR结果
        result = get_raw_ocr_result(image_path)
        if result:
            print("\n🔍 OCR识别结果:")
            print(f"   姓名: {result.get('insuredPerson', '未识别')}")
            print(f"   身份证号: {result.get('idNumber', '未识别')}")
            
            # 分析失败原因
            if result.get('insuredPerson') == '未识别' and result.get('idNumber') == '未识别':
                print("\n❌ 识别失败分析:")
                print("   可能原因:")
                print("   1. 图片质量差（模糊、反光、角度不正）")
                print("   2. 文字区域被遮挡或损坏")
                print("   3. 图片分辨率过低")
                print("   4. 光线条件差（过暗或过亮）")
                print("   5. 文字与背景对比度低")
        else:
            print("❌ OCR请求失败")

def diagnose_bank_card_failures():
    """诊断银行卡识别失败的原因"""
    print("\n🔍 诊断银行卡识别失败原因...")
    print("="*50)
    
    bank_card_images = glob.glob("测试/银行卡/*.JPG")
    
    for image_path in bank_card_images:
        print(f"\n📷 分析图片: {os.path.basename(image_path)}")
        print("-" * 40)
        
        # 分析图片质量
        quality_info = analyze_image_quality(image_path)
        print("📊 图片质量分析:")
        if isinstance(quality_info, dict):
            for key, value in quality_info.items():
                print(f"   {key}: {value}")
        else:
            print(f"   {quality_info}")
        
        # 获取OCR结果
        result = get_raw_ocr_result(image_path)
        if result:
            print("\n🔍 OCR识别结果:")
            print(f"   银行名称: {result.get('bankName', '未识别')}")
            print(f"   卡号: {result.get('cardNumber', '未识别')}")
            
            # 分析失败原因
            if result.get('bankName') == '未识别' and result.get('cardNumber') == '未识别':
                print("\n❌ 识别失败分析:")
                print("   可能原因:")
                print("   1. 银行卡信息区域不清晰")
                print("   2. 卡号字体过小或模糊")
                print("   3. 银行名称被遮挡或模糊")
                print("   4. 图片角度不正或倾斜")
                print("   5. 反光或阴影影响文字识别")
        else:
            print("❌ OCR请求失败")

def suggest_optimizations():
    """提供优化建议"""
    print("\n🚀 OCR识别优化建议...")
    print("="*50)
    
    print("\n📸 图片预处理优化:")
    print("   1. 图像增强:")
    print("      - 对比度增强")
    print("      - 亮度调整")
    print("      - 锐化处理")
    print("      - 去噪处理")
    
    print("\n   2. 图像校正:")
    print("      - 透视校正")
    print("      - 旋转校正")
    print("      - 倾斜校正")
    
    print("\n   3. 区域检测:")
    print("      - 身份证区域自动检测")
    print("      - 银行卡信息区域定位")
    print("      - 文字区域ROI提取")
    
    print("\n🔧 算法优化:")
    print("   1. 多模型融合:")
    print("      - 结合多个OCR引擎")
    print("      - 投票机制选择最佳结果")
    
    print("\n   2. 后处理优化:")
    print("      - 正则表达式验证")
    print("      - 格式校验")
    print("      - 逻辑一致性检查")
    
    print("\n   3. 容错机制:")
    print("      - 模糊匹配")
    print("      - 相似度计算")
    print("      - 候选结果排序")

def main():
    print("🔍 OCR识别失败原因诊断")
    print("="*50)
    
    # 检查后端服务
    try:
        response = requests.get('http://localhost:8010', timeout=5)
        print("✅ 后端服务正在运行")
    except:
        print("❌ 后端服务未运行，请先启动: python3 app.py")
        return
    
    # 诊断身份证识别失败
    diagnose_id_card_failures()
    
    # 诊断银行卡识别失败
    diagnose_bank_card_failures()
    
    # 提供优化建议
    suggest_optimizations()

if __name__ == "__main__":
    main()
