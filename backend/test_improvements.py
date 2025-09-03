#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试改进后的身份证和银行卡识别功能
"""

import requests
import time
import os
from datetime import datetime

def test_improved_recognition():
    """测试改进后的识别功能"""
    print("开始测试改进后的身份证和银行卡识别功能...")
    print("请确保后端服务已启动在 http://localhost:8010")
    print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试图片路径
    test_images = [
        # 身份证 - 之前识别效果不好的
        ("测试/身份证/b838b3065e09d66f3bd56f73e2ad90b8.JPG", "身份证"),
        
        # 银行卡 - 之前识别效果不好的
        ("测试/银行卡/99b7278fecbd6176545cd4529f6b366b.JPG", "银行卡"),
        ("测试/银行卡/cd11656a20f17ada2a052e4c8c73578b.JPG", "银行卡"),
        
        # 身份证 - 之前识别效果好的（对比）
        ("测试/身份证/b512bca6f5da75508be3c7887882e46b.JPG", "身份证"),
        ("测试/身份证/e0a2074108be994c1ac6fe03c103c0cc.JPG", "身份证"),
        
        # 银行卡 - 之前识别效果好的（对比）
        ("测试/银行卡/95d4c07fcbd5f873413baf5c9c022ffd.JPG", "银行卡"),
        ("测试/银行卡/fa13cf89c2fce2f4a363e5270d7805b6.JPG", "银行卡"),
        ("测试/银行卡/fdcba9c95497faa3916cf944ad2a8873.JPG", "银行卡"),
    ]
    
    print(f"\n总共需要测试 {len(test_images)} 张图片")
    
    results = []
    total_time = 0
    
    for i, (image_path, category) in enumerate(test_images, 1):
        print(f"\n{'='*60}")
        print(f"进度: {i}/{len(test_images)}")
        print(f"测试图片: {image_path}")
        print(f"分类: {category}")
        print(f"{'='*60}")
        
        if not os.path.exists(image_path):
            print(f"❌ 文件不存在: {image_path}")
            continue
        
        start_time = time.time()
        
        try:
            with open(image_path, 'rb') as f:
                files = {'files': (os.path.basename(image_path), f, 'image/jpeg')}
                response = requests.post('http://localhost:8010/parse-docs', files=files)
                
                end_time = time.time()
                processing_time = end_time - start_time
                total_time += processing_time
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 识别成功！耗时: {processing_time:.2f}秒")
                    
                    if category == "身份证":
                        name = result.get('insuredPerson', '未识别')
                        id_number = result.get('idNumber', '未识别')
                        print(f"  姓名: {name}")
                        print(f"  身份证号: {id_number}")
                        
                        # 评估识别质量
                        if name != "未识别" and id_number != "未识别":
                            print(f"  🎯 识别质量: 优秀 (姓名+身份证号)")
                        elif name != "未识别" or id_number != "未识别":
                            print(f"  🎯 识别质量: 良好 (部分识别)")
                        else:
                            print(f"  🎯 识别质量: 需要改进")
                            
                    elif category == "银行卡":
                        bank_name = result.get('bankName', '未识别')
                        card_number = result.get('cardNumber', '未识别')
                        print(f"  银行名称: {bank_name}")
                        print(f"  卡号: {card_number}")
                        
                        # 评估识别质量
                        if bank_name != "未识别" and card_number != "未识别":
                            print(f"  🎯 识别质量: 优秀 (银行名称+卡号)")
                        elif bank_name != "未识别" or card_number != "未识别":
                            print(f"  🎯 识别质量: 良好 (部分识别)")
                        else:
                            print(f"  🎯 识别质量: 需要改进")
                    
                    results.append({
                        'image': image_path,
                        'category': category,
                        'success': True,
                        'processing_time': processing_time,
                        'result': result
                    })
                    
                else:
                    print(f"❌ 识别失败！状态码: {response.status_code}")
                    print(f"错误信息: {response.text}")
                    results.append({
                        'image': image_path,
                        'category': category,
                        'success': False,
                        'processing_time': processing_time,
                        'result': None
                    })
                    
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"❌ 测试出错: {str(e)}")
            results.append({
                'image': image_path,
                'category': category,
                'success': False,
                'processing_time': processing_time,
                'result': None
            })
    
    # 输出测试总结
    print(f"\n{'='*60}")
    print("改进效果测试总结")
    print(f"{'='*60}")
    
    # 按分类统计
    id_results = [r for r in results if r['category'] == '身份证']
    bank_results = [r for r in results if r['success'] and r['category'] == '银行卡']
    
    print(f"\n📊 身份证识别改进效果:")
    print(f"  总测试数: {len(id_results)}")
    print(f"  成功数: {sum(1 for r in id_results if r['success'])}")
    
    # 统计姓名和身份证号的识别情况
    names_recognized = sum(1 for r in id_results if r['success'] and r['result'] and r['result'].get('insuredPerson') != '未识别')
    ids_recognized = sum(1 for r in id_results if r['success'] and r['result'] and r['result'].get('idNumber') != '未识别')
    
    print(f"  姓名识别率: {names_recognized}/{len(id_results)} ({names_recognized/len(id_results)*100:.1f}%)")
    print(f"  身份证号识别率: {ids_recognized}/{len(id_results)} ({ids_recognized/len(id_results)*100:.1f}%)")
    
    print(f"\n📊 银行卡识别改进效果:")
    print(f"  总测试数: {len(bank_results)}")
    
    # 统计银行名称和卡号的识别情况
    banks_recognized = sum(1 for r in bank_results if r['result'] and r['result'].get('bankName') != '未识别')
    cards_recognized = sum(1 for r in bank_results if r['result'] and r['result'].get('cardNumber') != '未识别')
    
    print(f"  银行名称识别率: {banks_recognized}/{len(bank_results)} ({banks_recognized/len(bank_results)*100:.1f}%)")
    print(f"  卡号识别率: {cards_recognized}/{len(bank_results)} ({cards_recognized/len(bank_results)*100:.1f}%)")
    
    print(f"\n⏱️ 性能统计:")
    print(f"  总耗时: {total_time:.2f}秒")
    print(f"  平均耗时: {total_time/len(results):.2f}秒")
    
    print(f"\n🎯 改进效果评估:")
    
    # 评估身份证改进效果
    if names_recognized/len(id_results) > 0.8 and ids_recognized/len(id_results) > 0.8:
        print(f"  🆔 身份证识别: 显著改进 ✅")
    elif names_recognized/len(id_results) > 0.6 or ids_recognized/len(id_results) > 0.6:
        print(f"  🆔 身份证识别: 有所改进 ⚠️")
    else:
        print(f"  🆔 身份证识别: 需要进一步优化 ❌")
    
    # 评估银行卡改进效果
    if banks_recognized/len(bank_results) > 0.8 and cards_recognized/len(bank_results) > 0.8:
        print(f"  💳 银行卡识别: 显著改进 ✅")
    elif banks_recognized/len(bank_results) > 0.6 or cards_recognized/len(bank_results) > 0.6:
        print(f"  💳 银行卡识别: 有所改进 ⚠️")
    else:
        print(f"  💳 银行卡识别: 需要进一步优化 ❌")
    
    print(f"\n测试结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test_improved_recognition()
