# -*- coding: utf-8 -*-
"""
猪耳标数字识别测试工具 - 智能分层版
测试前5张猪耳标图片的识别准确性
"""

import logging
import cv2
import numpy as np
import re
import os

# 关闭烦人的警告
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger('ppocr').setLevel(logging.ERROR)

# 导入模块
try:
    from paddleocr import PaddleOCR
except ImportError:
    raise ImportError("请先运行: pip install paddleocr==2.7.0.3 paddlepaddle opencv-python==4.6.0.66")

def preprocess_eartag_image(image_path):
    """专门针对猪耳标的图像预处理"""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"无法读取图像: {image_path}")
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)
    binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    return cleaned

def enhance_image_for_blur_detection(image_path):
    """专门针对模糊图像的增强处理"""
    image = cv2.imread(image_path)
    if image is None:
        return None
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)
    kernel_sharpen = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(denoised, -1, kernel_sharpen)
    binary = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 5)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open)
    return cleaned

def is_valid_eartag_number(text):
    """判断是否为有效的耳标数字"""
    clean_text = ''.join(c for c in text if c.isalnum())
    if len(clean_text) != 7 and len(clean_text) != 8:
        return False
    digit_count = sum(1 for c in clean_text if c.isdigit())
    if digit_count / len(clean_text) < 0.7:
        return False
    return True

# 初始化 OCR
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='ch',
    use_gpu=False,
    det_db_thresh=0.01,
    det_db_box_thresh=0.1,
    det_db_unclip_ratio=4.0,
    drop_score=0.01,
    max_text_length=50
)

# 测试图片列表
test_images = [
    '测试/猪耳标/pig1.JPG',
    '测试/猪耳标/pig2.JPG', 
    '测试/猪耳标/pig3.JPG',
    '测试/猪耳标/pig4.JPG',
    '测试/猪耳标/pig5.JPG'
]

print("🔍 开始测试前5张猪耳标图片的识别准确性...")
print("🔄 使用智能分层识别策略...")

# 循环测试所有图片
for img_idx, image_path in enumerate(test_images, 1):
    print(f"\n{'='*80}")
    print(f"🐷 测试图片 {img_idx}: {image_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(image_path):
        print(f"❌ 图片不存在: {image_path}")
        continue
    
    try:
        all_results = []
        
        # 第一层：快速识别
        print("📸 【第一层】快速识别...")
        
        # 1. 原图识别
        print("  📸 识别原图...")
        result_original = ocr.ocr(image_path, det=True, rec=True)
        if result_original:
            all_results.extend(result_original)
        
        # 2. 基础预处理图像识别
        print("  🔄 识别基础预处理图像...")
        processed_image = preprocess_eartag_image(image_path)
        temp_path = f'temp_processed_{img_idx}.jpg'
        cv2.imwrite(temp_path, processed_image)
        
        result_processed = ocr.ocr(temp_path, det=True, rec=True)
        if result_processed:
            all_results.extend(result_processed)
        
        # 3. 增强预处理图像识别
        print("  🔄 识别增强预处理图像...")
        enhanced_image = enhance_image_for_blur_detection(image_path)
        if enhanced_image is not None:
            temp_enhanced_path = f'temp_enhanced_{img_idx}.jpg'
            cv2.imwrite(temp_enhanced_path, enhanced_image)
            
            result_enhanced = ocr.ocr(temp_enhanced_path, det=True, rec=True)
            if result_enhanced:
                all_results.extend(result_enhanced)
        
        # 清理临时文件
        for temp_file in [temp_path, temp_enhanced_path]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        # 处理识别结果
        all_text_results = []
        for result in all_results:
            if result and len(result) > 0:
                for line in result:
                    if len(line) >= 2:
                        text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                        confidence = line[1][1] if isinstance(line[1], (list, tuple)) and len(line[1]) > 1 else 0.5
                        bbox = line[0] if len(line) > 0 else None
                        all_text_results.append((text, confidence, bbox))
        
        # 分类结果
        eartag_numbers = []
        other_numbers = []
        text_content = []
        
        for text, confidence, bbox in all_text_results:
            clean_text = ''.join(c for c in text if c.isalnum())
            
            if is_valid_eartag_number(clean_text):
                eartag_numbers.append((text, confidence, bbox))
            elif any(c.isdigit() for c in text):
                other_numbers.append((text, confidence, bbox))
            else:
                text_content.append((text, confidence, bbox))
        
        # 按置信度排序
        eartag_numbers.sort(key=lambda x: x[1], reverse=True)
        
        # 显示结果
        print(f"\n📊 识别结果分析:")
        print(f"🔍 总检测区域数: {len(all_text_results)}")
        print(f"🎯 耳标数字数量: {len(eartag_numbers)}")
        print(f"🔢 其他数字数量: {len(other_numbers)}")
        print(f"📝 文本内容数量: {len(text_content)}")
        
        # 显示耳标数字
        print(f"\n🎯 【耳标数字】- 主要识别目标：")
        if eartag_numbers:
            for i, (text, confidence, bbox) in enumerate(eartag_numbers[:5], 1):
                clean_text = ''.join(c for c in text if c.isalnum())
                print(f"  {i}. '{text}' -> '{clean_text}' (置信度: {confidence:.4f})")
        else:
            print("  ❌ 未识别到任何耳标数字")
        
        # 推荐耳标数字
        print(f"\n🎯 【推荐耳标数字】- 最可能的耳标标识：")
        if eartag_numbers:
            # 去重并选择最佳结果
            seen_numbers = set()
            unique_eartag_numbers = []
            for text, confidence, bbox in eartag_numbers:
                clean_text = ''.join(c for c in text if c.isalnum())
                if clean_text not in seen_numbers:
                    unique_eartag_numbers.append((clean_text, confidence))
                    seen_numbers.add(clean_text)
            
            if len(unique_eartag_numbers) >= 2:
                print(f"  ✅ 成功识别出两个耳标数字：")
                print(f"    1️⃣ 第一个数字: {unique_eartag_numbers[0][0]} (置信度: {unique_eartag_numbers[0][1]:.4f})")
                print(f"    2️⃣ 第二个数字: {unique_eartag_numbers[1][0]} (置信度: {unique_eartag_numbers[1][1]:.4f})")
            elif len(unique_eartag_numbers) == 1:
                print(f"  ⚠️ 只识别到一个耳标数字：")
                print(f"    1️⃣ 数字: {unique_eartag_numbers[0][0]} (置信度: {unique_eartag_numbers[0][1]:.4f})")
            else:
                print("  ❌ 未识别到任何耳标数字")
        else:
            print("  ❌ 未识别到任何耳标数字")
        
        # 显示其他数字（可能相关的）
        if other_numbers:
            print(f"\n🔢 【其他数字】- 可能相关的数字：")
            for i, (text, confidence, bbox) in enumerate(other_numbers[:3], 1):
                print(f"  {i}. '{text}' (置信度: {confidence:.4f})")
        
    except Exception as e:
        print(f"❌ 识别失败: {e}")

print(f"\n🎉 测试完成！")
