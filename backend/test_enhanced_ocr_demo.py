#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版OCR识别测试脚本
用于测试身份证和银行卡识别功能
"""

import os
import cv2
import numpy as np
from pathlib import Path
import json
import re
from datetime import datetime

# 导入增强版OCR功能
from app_enhanced import (
    enhanced_ocr_image, 
    extract_id_card_enhanced, 
    extract_bank_card_enhanced,
    extract_system_screenshot_enhanced,
    enhance_image
)

def test_single_image(image_path, image_type="unknown"):
    """测试单张图片的OCR识别"""
    print(f"\n{'='*60}")
    print(f"🔍 测试图片: {os.path.basename(image_path)}")
    print(f"📋 图片类型: {image_type}")
    print(f"{'='*60}")
    
    try:
        # 读取图片
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # 使用增强版OCR识别
        print("🔄 正在进行增强OCR识别...")
        texts_with_boxes = enhanced_ocr_image(image_bytes)
        
        if not texts_with_boxes:
            print("❌ OCR识别失败，未识别到任何文本")
            return None
        
        print(f"✅ OCR识别成功，识别到 {len(texts_with_boxes)} 个文本块")
        
        # 显示识别的文本
        print("\n📝 识别到的文本:")
        for i, text_block in enumerate(texts_with_boxes[:10]):  # 只显示前10个
            text = text_block["text"]
            score = text_block["score"]
            engine = text_block["engine"]
            print(f"  {i+1:2d}. [{engine:8s}] [{score:.3f}] {text}")
        
        if len(texts_with_boxes) > 10:
            print(f"  ... 还有 {len(texts_with_boxes) - 10} 个文本块")
        
        # 根据图片类型进行特定识别
        if image_type == "id_card":
            result = extract_id_card_enhanced(texts_with_boxes)
            print(f"\n🆔 身份证识别结果:")
            print(f"  姓名: {result.get('name', '未识别')}")
            print(f"  身份证号: {result.get('id_number', '未识别')}")
            
        elif image_type == "bank_card":
            result = extract_bank_card_enhanced(texts_with_boxes)
            print(f"\n💳 银行卡识别结果:")
            print(f"  银行名称: {result.get('bank_name', '未识别')}")
            print(f"  卡号: {result.get('card_number', '未识别')}")
            
        elif image_type == "system_screenshot":
            result = extract_system_screenshot_enhanced(texts_with_boxes)
            print(f"\n🖥️ 系统截图识别结果:")
            print(f"  保单号: {result.get('policy_number', '未识别')}")
            print(f"  报案号: {result.get('claim_number', '未识别')}")
            print(f"  被保险人: {result.get('insured_person', '未识别')}")
            print(f"  保险标的: {result.get('insurance_subject', '未识别')}")
            print(f"  保险期间: {result.get('coverage_period', '未识别')}")
            print(f"  出险日期: {result.get('incident_date', '未识别')}")
            print(f"  出险地点: {result.get('incident_location', '未识别')}")
            print(f"  报案时间: {result.get('report_time', '未识别')}")
            print(f"  查勘时间: {result.get('inspection_time', '未识别')}")
            print(f"  查勘方式: {result.get('inspection_method', '未识别')}")
            print(f"  估损金额: {result.get('estimated_loss', '未识别')}")
            print(f"  出险原因: {result.get('incident_cause', '未识别')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 处理图片时出错: {e}")
        return None

def auto_detect_image_type(texts_with_boxes):
    """自动检测图片类型"""
    texts = [b["text"] for b in texts_with_boxes]
    text_str = "\n".join(texts).upper()
    
    # 检查身份证特征
    if any(k in text_str for k in ["身份证", "姓名", "公民身份号码"]):
        return "id_card"
    
    # 检查系统截图特征
    has_screenshot_features = any(k in text_str for k in ["保单号", "报案号", "被保险人", "保险标的", "出险日期", "查勘", "估损金额", "理赔", "承保公司"])
    
    # 检查银行卡特征 - 改进逻辑
    has_bank_features = any(k in text_str for k in ["Union", "ATM", "银联"]) or \
                       any(re.search(r'\b\d{16,19}\b', text) for text in texts)
    
    if has_screenshot_features:
        return "system_screenshot"
    elif has_bank_features:
        return "bank_card"
    else:
        return "unknown"

def test_all_images():
    """测试所有测试图片"""
    print("🚀 开始测试增强版OCR识别系统")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试身份证
    id_card_dir = Path("测试/身份证")
    if id_card_dir.exists():
        print(f"\n📁 测试身份证文件夹: {id_card_dir}")
        id_card_results = []
        
        for image_file in id_card_dir.glob("*.JPG"):
            result = test_single_image(str(image_file), "id_card")
            if result:
                id_card_results.append({
                    "file": image_file.name,
                    "result": result
                })
        
        print(f"\n📊 身份证识别统计: 成功 {len(id_card_results)}/{len(list(id_card_dir.glob('*.JPG')))}")
    
    # 测试银行卡
    bank_card_dir = Path("测试/银行卡")
    if bank_card_dir.exists():
        print(f"\n📁 测试银行卡文件夹: {bank_card_dir}")
        bank_card_results = []
        
        for image_file in bank_card_dir.glob("*.JPG"):
            result = test_single_image(str(image_file), "bank_card")
            if result:
                bank_card_results.append({
                    "file": image_file.name,
                    "result": result
                })
        
        print(f"\n📊 银行卡识别统计: 成功 {len(bank_card_results)}/{len(list(bank_card_dir.glob('*.JPG')))}")
    
    # 测试系统截图
    screenshot_dir = Path("测试/系统截图")
    if screenshot_dir.exists():
        print(f"\n📁 测试系统截图文件夹: {screenshot_dir}")
        screenshot_results = []
        
        for image_file in screenshot_dir.glob("*.JPG"):
            result = test_single_image(str(image_file), "system_screenshot")
            if result:
                screenshot_results.append({
                    "file": image_file.name,
                    "result": result
                })
        
        print(f"\n📊 系统截图识别统计: 成功 {len(screenshot_results)}/{len(list(screenshot_dir.glob('*.JPG')))}")
    
    print(f"\n🎉 测试完成! 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def test_specific_image(image_path):
    """测试指定的单张图片"""
    if not os.path.exists(image_path):
        print(f"❌ 图片文件不存在: {image_path}")
        return
    
    # 先进行OCR识别
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    texts_with_boxes = enhanced_ocr_image(image_bytes)
    
    if not texts_with_boxes:
        print("❌ OCR识别失败")
        return
    
    # 自动检测图片类型
    image_type = auto_detect_image_type(texts_with_boxes)
    
    # 进行特定识别
    if image_type == "id_card":
        result = extract_id_card_enhanced(texts_with_boxes)
        print(f"\n🆔 身份证识别结果:")
        print(f"  姓名: {result.get('name', '未识别')}")
        print(f"  身份证号: {result.get('id_number', '未识别')}")
        
    elif image_type == "bank_card":
        result = extract_bank_card_enhanced(texts_with_boxes)
        print(f"\n💳 银行卡识别结果:")
        print(f"  银行名称: {result.get('bank_name', '未识别')}")
        print(f"  卡号: {result.get('card_number', '未识别')}")
        
    else:
        print(f"\n❓ 无法确定图片类型，显示所有识别文本:")
        for i, text_block in enumerate(texts_with_boxes):
            text = text_block["text"]
            score = text_block["score"]
            print(f"  {i+1:2d}. [{score:.3f}] {text}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 测试指定的图片
        image_path = sys.argv[1]
        test_specific_image(image_path)
    else:
        # 测试所有图片
        test_all_images()
