#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试图片识别功能
测试身份证、银行卡、系统截图等图片的识别正确性和耗时
不包含猪耳标测试
"""

import requests
import time
import os
import json
from datetime import datetime

def test_image_recognition(image_path, category):
    """测试单张图片的识别功能"""
    print(f"\n{'='*80}")
    print(f"测试图片: {image_path}")
    print(f"分类: {category}")
    print(f"{'='*80}")
    
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

def analyze_recognition_accuracy(category, results):
    """分析识别准确率"""
    if not results:
        return {"total": 0, "success": 0, "accuracy": 0, "avg_time": 0}
    
    total = len(results)
    success = sum(1 for r in results if r['success'])
    accuracy = success / total * 100 if total > 0 else 0
    avg_time = sum(r['processing_time'] for r in results) / total if total > 0 else 0
    
    return {
        "total": total,
        "success": success,
        "accuracy": accuracy,
        "avg_time": avg_time
    }

def main():
    """主测试函数"""
    print("开始全面测试图片识别功能...")
    print("请确保后端服务已启动在 http://localhost:8010")
    print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试图片路径（不包含猪耳标）
    test_images = [
        # 身份证
        ("测试/身份证/b512bca6f5da75508be3c7887882e46b.JPG", "身份证"),
        ("测试/身份证/b838b3065e09d66f3bd56f73e2ad90b8.JPG", "身份证"),
        ("测试/身份证/e0a2074108be994c1ac6fe03c103c0cc.JPG", "身份证"),
        
        # 银行卡
        ("测试/银行卡/95d4c07fcbd5f873413baf5c9c022ffd.JPG", "银行卡"),
        ("测试/银行卡/99b7278fecbd6176545cd4529f6b366b.JPG", "银行卡"),
        ("测试/银行卡/cd11656a20f17ada2a052e4c8c73578b.JPG", "银行卡"),
        ("测试/银行卡/fa13cf89c2fce2f4a363e5270d7805b6.JPG", "银行卡"),
        ("测试/银行卡/fdcba9c95497faa3916cf944ad2a8873.JPG", "银行卡"),
        
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
    results_by_category = {}
    all_results = []
    
    print(f"\n总共需要测试 {total_tests} 张图片")
    print("测试分类: 身份证(3张), 银行卡(5张), 系统截图(4张)")
    
    for i, (image_path, category) in enumerate(test_images, 1):
        print(f"\n进度: {i}/{total_tests}")
        
        # 检查文件是否存在
        if not os.path.exists(image_path):
            print(f"❌ 文件不存在: {image_path}")
            continue
            
        success, processing_time, result = test_image_recognition(image_path, category)
        
        # 记录结果
        result_data = {
            'image_path': image_path,
            'category': category,
            'success': success,
            'processing_time': processing_time,
            'result': result
        }
        all_results.append(result_data)
        
        if success:
            successful_tests += 1
            total_time += processing_time
            
            # 按分类记录结果
            if category not in results_by_category:
                results_by_category[category] = []
            results_by_category[category].append(result_data)
    
    # 分析各类别结果
    print(f"\n{'='*80}")
    print("测试结果分析")
    print(f"{'='*80}")
    
    category_analysis = {}
    for category, results in results_by_category.items():
        analysis = analyze_recognition_accuracy(category, results)
        category_analysis[category] = analysis
        
        print(f"\n📊 {category}识别结果:")
        print(f"  总数量: {analysis['total']}")
        print(f"  成功数: {analysis['success']}")
        print(f"  准确率: {analysis['accuracy']:.1f}%")
        print(f"  平均耗时: {analysis['avg_time']:.2f}秒")
        
        # 显示识别内容统计
        if category == "身份证":
            names = [r['result'].get('insuredPerson', '未识别') for r in results if r['success'] and r['result']]
            id_numbers = [r['result'].get('idNumber', '未识别') for r in results if r['success'] and r['result']]
            print(f"  识别出的姓名: {names}")
            print(f"  识别出的身份证号: {id_numbers}")
            
        elif category == "银行卡":
            bank_names = [r['result'].get('bankName', '未识别') for r in results if r['success'] and r['result']]
            card_numbers = [r['result'].get('cardNumber', '未识别') for r in results if r['success'] and r['result']]
            print(f"  识别出的银行名称: {bank_names}")
            print(f"  识别出的卡号: {card_numbers}")
            
        elif category == "系统截图":
            policy_numbers = [r['result'].get('policyNumber', '未识别') for r in results if r['success'] and r['result']]
            claim_numbers = [r['result'].get('claimNumber', '未识别') for r in results if r['success'] and r['result']]
            insured_names = [r['result'].get('insuredName', '未识别') for r in results if r['success'] and r['result']]
            print(f"  识别出的保单号: {policy_numbers}")
            print(f"  识别出的报案号: {claim_numbers}")
            print(f"  识别出的被保险人: {insured_names}")
    
    # 输出总体测试总结
    print(f"\n{'='*80}")
    print("总体测试总结")
    print(f"{'='*80}")
    print(f"总测试数: {total_tests}")
    print(f"成功数: {successful_tests}")
    print(f"失败数: {total_tests - successful_tests}")
    print(f"总体成功率: {successful_tests/total_tests*100:.1f}%")
    print(f"总耗时: {total_time:.2f}秒")
    print(f"平均耗时: {total_time/successful_tests:.2f}秒" if successful_tests > 0 else "平均耗时: N/A")
    
    # 保存详细结果到文件
    output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'total_time': total_time,
                'overall_success_rate': successful_tests/total_tests*100 if total_tests > 0 else 0
            },
            'category_analysis': category_analysis,
            'detailed_results': all_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 详细测试结果已保存到: {output_file}")
    print(f"测试结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
