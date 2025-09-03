#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试除猪耳标外的所有图片识别准确率
"""

import requests
import json
import os
import glob
from pathlib import Path

def test_image_accuracy(image_path, expected_type):
    """测试单张图片的识别准确率"""
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
                return True, result
            else:
                return False, f"HTTP错误: {response.status_code}"
                
    except Exception as e:
        return False, f"请求错误: {e}"

def analyze_id_card_result(result):
    """分析身份证识别结果"""
    score = 0
    total = 2
    details = []
    
    # 检查姓名
    if result.get("insuredPerson") and result["insuredPerson"] != "未识别":
        score += 1
        details.append(f"✅ 姓名: {result['insuredPerson']}")
    else:
        details.append("❌ 姓名: 未识别")
    
    # 检查身份证号
    if result.get("idNumber") and result["idNumber"] != "未识别":
        if len(result["idNumber"]) == 18:
            score += 1
            details.append(f"✅ 身份证号: {result['idNumber']}")
        else:
            details.append(f"⚠️ 身份证号格式异常: {result['idNumber']}")
    else:
        details.append("❌ 身份证号: 未识别")
    
    return score, total, details

def analyze_bank_card_result(result):
    """分析银行卡识别结果"""
    score = 0
    total = 2
    details = []
    
    # 检查银行名称
    if result.get("bankName") and result["bankName"] != "未识别":
        score += 1
        details.append(f"✅ 银行名称: {result['bankName']}")
    else:
        details.append("❌ 银行名称: 未识别")
    
    # 检查卡号
    if result.get("cardNumber") and result["cardNumber"] != "未识别":
        if len(result["cardNumber"]) >= 16:
            score += 1
            details.append(f"✅ 卡号: {result['cardNumber']}")
        else:
            details.append(f"⚠️ 卡号格式异常: {result['cardNumber']}")
    else:
        details.append("❌ 卡号: 未识别")
    
    return score, total, details

def analyze_system_screenshot_result(result):
    """分析系统截图识别结果"""
    score = 0
    total = 8
    details = []
    
    # 检查保单号
    if result.get("policyNumber") and result["policyNumber"] != "未识别":
        score += 1
        details.append(f"✅ 保单号: {result['policyNumber']}")
    else:
        details.append("❌ 保单号: 未识别")
    
    # 检查报案号
    if result.get("claimNumber") and result["claimNumber"] != "未识别":
        score += 1
        details.append(f"✅ 报案号: {result['claimNumber']}")
    else:
        details.append("❌ 报案号: 未识别")
    
    # 检查被保险人
    if result.get("insuredName") and result["insuredName"]:
        score += 1
        details.append(f"✅ 被保险人: {result['insuredName']}")
    else:
        details.append("❌ 被保险人: 未识别")
    
    # 检查出险地点
    if result.get("incidentLocation") and result["incidentLocation"]:
        score += 1
        details.append(f"✅ 出险地点: {result['incidentLocation']}")
    else:
        details.append("❌ 出险地点: 未识别")
    
    # 检查出险原因
    if result.get("incidentCause") and result["incidentCause"]:
        score += 1
        details.append(f"✅ 出险原因: {result['incidentCause']}")
    else:
        details.append("❌ 出险原因: 未识别")
    
    # 检查报案时间
    if result.get("reportTime") and result["reportTime"]:
        score += 1
        details.append(f"✅ 报案时间: {result['reportTime']}")
    else:
        details.append("❌ 报案时间: 未识别")
    
    # 检查立案时间
    if result.get("inspectionTime") and result["inspectionTime"]:
        score += 1
        details.append(f"✅ 立案时间: {result['inspectionTime']}")
    else:
        details.append("❌ 立案时间: 未识别")
    
    # 检查估损金额
    if result.get("estimatedLoss") and result["estimatedLoss"]:
        score += 1
        details.append(f"✅ 估损金额: {result['estimatedLoss']}")
    else:
        details.append("❌ 估损金额: 未识别")
    
    return score, total, details

def test_all_images():
    """测试所有图片的识别准确率"""
    
    # 获取所有测试图片
    test_dirs = {
        "身份证": "测试/身份证/*.JPG",
        "银行卡": "测试/银行卡/*.JPG",
        "系统截图": "测试/系统截图/*.JPG"
    }
    
    total_stats = {
        "身份证": {"total": 0, "success": 0, "total_score": 0, "total_possible": 0},
        "银行卡": {"total": 0, "success": 0, "total_score": 0, "total_possible": 0},
        "系统截图": {"total": 0, "success": 0, "total_score": 0, "total_possible": 0}
    }
    
    print("🚀 开始测试所有图片识别准确率...")
    print("="*60)
    
    for category, pattern in test_dirs.items():
        print(f"\n📁 测试类别: {category}")
        print("-" * 40)
        
        images = glob.glob(pattern)
        total_stats[category]["total"] = len(images)
        
        for i, image_path in enumerate(images, 1):
            print(f"\n🔍 测试图片 {i}/{len(images)}: {os.path.basename(image_path)}")
            
            success, result = test_image_accuracy(image_path, category)
            
            if success:
                total_stats[category]["success"] += 1
                
                # 分析识别结果
                if category == "身份证":
                    score, total, details = analyze_id_card_result(result)
                elif category == "银行卡":
                    score, total, details = analyze_bank_card_result(result)
                elif category == "系统截图":
                    score, total, details = analyze_system_screenshot_result(result)
                
                total_stats[category]["total_score"] += score
                total_stats[category]["total_possible"] += total
                
                accuracy = (score / total) * 100
                print(f"   识别成功率: {accuracy:.1f}% ({score}/{total})")
                
                for detail in details:
                    print(f"   {detail}")
            else:
                print(f"   ❌ 识别失败: {result}")
        
        # 计算该类别的总体准确率
        if total_stats[category]["total"] > 0:
            success_rate = (total_stats[category]["success"] / total_stats[category]["total"]) * 100
            if total_stats[category]["total_possible"] > 0:
                accuracy_rate = (total_stats[category]["total_score"] / total_stats[category]["total_possible"]) * 100
            else:
                accuracy_rate = 0
            
            print(f"\n📊 {category}类别统计:")
            print(f"   图片总数: {total_stats[category]['total']}")
            print(f"   识别成功: {total_stats[category]['success']}")
            print(f"   识别成功率: {success_rate:.1f}%")
            print(f"   字段准确率: {accuracy_rate:.1f}%")
    
    # 总体统计
    print("\n" + "="*60)
    print("📊 总体识别准确率统计")
    print("="*60)
    
    total_images = sum(stats["total"] for stats in total_stats.values())
    total_success = sum(stats["success"] for stats in total_stats.values())
    total_score = sum(stats["total_score"] for stats in total_stats.values())
    total_possible = sum(stats["total_possible"] for stats in total_stats.values())
    
    if total_images > 0:
        overall_success_rate = (total_success / total_images) * 100
        print(f"📈 总体识别成功率: {overall_success_rate:.1f}% ({total_success}/{total_images})")
    
    if total_possible > 0:
        overall_accuracy_rate = (total_score / total_possible) * 100
        print(f"📈 总体字段准确率: {overall_accuracy_rate:.1f}% ({total_score}/{total_possible})")
    
    print(f"📁 测试图片总数: {total_images}")
    print(f"✅ 识别成功总数: {total_success}")
    print(f"🎯 识别字段总数: {total_possible}")
    print(f"🎯 正确字段总数: {total_score}")

if __name__ == "__main__":
    print("🎯 OCR识别准确率测试")
    print("测试除猪耳标外的所有图片")
    print()
    
    # 检查后端服务是否运行
    try:
        response = requests.get('http://localhost:8010', timeout=5)
        print("✅ 后端服务正在运行")
    except:
        print("❌ 后端服务未运行，请先启动: python3 app.py")
        exit(1)
    
    test_all_images()
