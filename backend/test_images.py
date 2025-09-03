#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图片识别功能
测试保单、系统截图、ID等图片的识别正确性和耗时
"""

import requests
import time
import os
from pathlib import Path

def test_image_recognition(image_path, category):
    """测试单张图片的识别功能"""
    print(f"\n{'='*60}")
    print(f"测试图片: {image_path}")
    print(f"分类: {category}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # 读取图片文件
        with open(image_path, 'rb') as f:
            files = {'files': (os.path.basename(image_path), f, 'image/jpeg')}
            
            # 发送请求到后端
            response = requests.post('http://localhost:8010/parse-docs', files=files)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 识别成功！耗时: {processing_time:.2f}秒")
                print(f"识别结果:")
                
                # 根据分类显示不同的结果
                if category == "身份证":
                    print(f"  姓名: {result.get('insuredPerson', '未识别')}")
                    print(f"  身份证号: {result.get('idNumber', '未识别')}")
                elif category == "银行卡":
                    print(f"  银行名称: {result.get('bankName', '未识别')}")
                    print(f"  卡号: {result.get('cardNumber', '未识别')}")
                elif category == "保单":
                    print(f"  保单号: {result.get('policyNumber', '未识别')}")
                    print(f"  报案号: {result.get('claimNumber', '未识别')}")
                    print(f"  被保险人: {result.get('insuredName', '未识别')}")
                    print(f"  保险标的: {result.get('insuranceSubject', [])}")
                    print(f"  保险期间: {result.get('coveragePeriod', '未识别')}")
                    print(f"  出险地点: {result.get('incidentLocation', '未识别')}")
                    print(f"  出险原因: {result.get('incidentCause', '未识别')}")
                    print(f"  报案时间: {result.get('reportTime', '未识别')}")
                    print(f"  查勘时间: {result.get('inspectionTime', '未识别')}")
                    print(f"  估损金额: {result.get('estimatedLoss', '未识别')}")
                elif category == "系统截图":
                    print(f"  保单号: {result.get('policyNumber', '未识别')}")
                    print(f"  报案号: {result.get('claimNumber', '未识别')}")
                    print(f"  被保险人: {result.get('insuredName', '未识别')}")
                    print(f"  保险标的: {result.get('insuranceSubject', [])}")
                    print(f"  保险期间: {result.get('coveragePeriod', '未识别')}")
                    print(f"  出险地点: {result.get('incidentLocation', '未识别')}")
                    print(f"  出险原因: {result.get('incidentCause', '未识别')}")
                    print(f"  报案时间: {result.get('reportTime', '未识别')}")
                    print(f"  查勘时间: {result.get('inspectionTime', '未识别')}")
                    print(f"  估损金额: {result.get('estimatedLoss', '未识别')}")
                
                return True, processing_time, result
            else:
                print(f"❌ 识别失败！状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                return False, processing_time, None
                
    except Exception as e:
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"❌ 测试出错: {str(e)}")
        return False, processing_time, None

def main():
    """主测试函数"""
    print("开始测试图片识别功能...")
    print("请确保后端服务已启动在 http://localhost:8010")
    
    # 测试图片路径
    test_images = [
        # 身份证
        ("测试/🆔/b512bca6f5da75508be3c7887882e46b.JPG", "身份证"),
        ("测试/🆔/b838b3065e09d66f3bd56f73e2ad90b8.JPG", "身份证"),
        ("测试/🆔/e0a2074108be994c1ac6fe03c103c0cc.JPG", "身份证"),
        
        # 银行卡
        ("测试/💳/95d4c07fcbd5f873413baf5c9c022ffd.JPG", "银行卡"),
        ("测试/💳/99b7278fecbd6176545cd4529f6b366b.JPG", "银行卡"),
        ("测试/💳/cd11656a20f17ada2a052e4c8c73578b.JPG", "银行卡"),
        ("测试/💳/fa13cf89c2fce2f4a363e5270d7805b6.JPG", "银行卡"),
        ("测试/💳/fdcba9c95497faa3916cf944ad2a8873.JPG", "银行卡"),
        
        # 保单
        ("测试/保单/74b22cd8e235e5677760d751ba37c928.JPG", "保单"),
        ("测试/保单/dd43efbca85ba3fb9784ff849d3a1f91.JPG", "保单"),
        ("测试/保单/Xnip2025-08-03_21-54-30.jpg", "保单"),
        
        # 系统截图
        ("测试/系统截图/45f30a67671ff9cb9e512ff49040e719.JPG", "系统截图"),
        ("测试/系统截图/8030db48ec4896455c0dd1034b71333f.JPG", "系统截图"),
        ("测试/系统截图/ca3cb94b0f702f61cc20f6450fc5ac3e.JPG", "系统截图"),
        ("测试/系统截图/e37ef75ba754cb68feef72729e637f3c.JPG", "系统截图"),
    ]
    
    # 统计结果
    total_tests = len(test_images)
    successful_tests = 0
    total_time = 0
    results_summary = {}
    
    print(f"\n总共需要测试 {total_tests} 张图片")
    
    for image_path, category in test_images:
        # 检查文件是否存在
        if not os.path.exists(image_path):
            print(f"❌ 文件不存在: {image_path}")
            continue
            
        success, processing_time, result = test_image_recognition(image_path, category)
        
        if success:
            successful_tests += 1
            total_time += processing_time
            
            # 记录结果摘要
            if category not in results_summary:
                results_summary[category] = {'success': 0, 'total': 0, 'avg_time': 0}
            results_summary[category]['success'] += 1
            results_summary[category]['total'] += 1
            results_summary[category]['avg_time'] += processing_time
        
        if category in results_summary:
            results_summary[category]['total'] += 1
    
    # 计算平均时间
    for category in results_summary:
        if results_summary[category]['success'] > 0:
            results_summary[category]['avg_time'] /= results_summary[category]['success']
    
    # 输出测试总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    print(f"总测试数: {total_tests}")
    print(f"成功数: {successful_tests}")
    print(f"失败数: {total_tests - successful_tests}")
    print(f"成功率: {successful_tests/total_tests*100:.1f}%")
    print(f"总耗时: {total_time:.2f}秒")
    print(f"平均耗时: {total_time/successful_tests:.2f}秒" if successful_tests > 0 else "平均耗时: N/A")
    
    print(f"\n各类别详细结果:")
    for category, stats in results_summary.items():
        success_rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"  {category}: {stats['success']}/{stats['total']} ({success_rate:.1f}%) - 平均耗时: {stats['avg_time']:.2f}秒")

if __name__ == "__main__":
    main()
