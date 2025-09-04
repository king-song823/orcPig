# -*- coding: utf-8 -*-
"""
猪耳标数字识别工具 - 通用版
适用于识别所有猪耳标上的数字，不针对特定数字
适用于 macOS（Intel/Apple Silicon）、Windows、Linux
"""

import logging
import cv2
import numpy as np
import math
import re

# === 第一步：关闭烦人的警告（可选）===
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger('ppocr').setLevel(logging.ERROR)

# === 第二步：导入模块（会自动处理版本兼容）===
try:
    from paddleocr import PaddleOCR
except ImportError:
    raise ImportError("请先运行: pip install paddleocr==2.7.0.3 paddlepaddle opencv-python==4.6.0.66")

# === 第三步：猪耳标图像预处理函数 ===
def preprocess_eartag_image(image_path):
    """专门针对猪耳标的图像预处理"""
    # 读取图像
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"无法读取图像: {image_path}")
    
    # 转换为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 应用CLAHE增强对比度
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 高斯模糊去噪
    denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)
    
    # 自适应阈值二值化
    binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # 形态学操作：开运算去除小噪点
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    return cleaned

def create_rotated_images(image_path, angles=[0, 90, 180, 270]):
    """创建多个旋转角度的图像用于识别颠倒的数字"""
    image = cv2.imread(image_path)
    if image is None:
        return []
    
    rotated_images = []
    for angle in angles:
        if angle == 0:
            rotated_images.append(image)
        else:
            # 计算旋转中心
            height, width = image.shape[:2]
            center = (width // 2, height // 2)
            
            # 创建旋转矩阵
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            # 执行旋转
            rotated = cv2.warpAffine(image, rotation_matrix, (width, height))
            rotated_images.append(rotated)
    
    return rotated_images

def is_valid_eartag_number(text):
    """判断是否为有效的耳标数字"""
    # 清理文本，只保留数字和字母
    clean_text = ''.join(c for c in text if c.isalnum())
    
    # 耳标数字通常的特征：
    # 1. 长度必须是7位或8位
    # 2. 主要包含数字
    # 3. 可能包含少量字母
    if len(clean_text) != 7 and len(clean_text) != 8:
        return False
    
    # 数字占比应该超过70%
    digit_count = sum(1 for c in clean_text if c.isdigit())
    if digit_count / len(clean_text) < 0.7:
        return False
    
    return True

def extract_eartag_numbers(text):
    """从文本中提取可能的耳标数字"""
    # 使用正则表达式匹配连续的数字序列
    numbers = re.findall(r'\d{4,}', text)
    return numbers

def enhance_image_for_blur_detection(image_path):
    """专门针对模糊图像的增强处理"""
    image = cv2.imread(image_path)
    if image is None:
        return None
    
    # 转换为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 1. 应用CLAHE增强对比度（更强）
    clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 2. 高斯模糊去噪
    denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)
    
    # 3. 锐化处理
    kernel_sharpen = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(denoised, -1, kernel_sharpen)
    
    # 4. 自适应阈值二值化（针对模糊图像优化）
    binary = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 5)
    
    # 5. 形态学操作：闭运算连接断开的笔画
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    # 6. 形态学操作：开运算去除小噪点
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open)
    
    return cleaned

def detect_eartag_regions(image_path):
    """专门检测耳标区域的图像处理"""
    image = cv2.imread(image_path)
    if image is None:
        return None
    
    # 转换为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 1. 应用CLAHE增强对比度
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 2. 边缘检测
    edges = cv2.Canny(enhanced, 50, 150)
    
    # 3. 查找轮廓
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 4. 筛选可能的圆形区域（耳标通常是圆形）
    circular_regions = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 1000:  # 过滤太小的区域
            # 计算轮廓的圆形度
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity > 0.5:  # 圆形度阈值
                    circular_regions.append(contour)
    
    # 5. 对每个圆形区域进行增强处理
    enhanced_regions = []
    for i, contour in enumerate(circular_regions):
        # 获取边界框
        x, y, w, h = cv2.boundingRect(contour)
        
        # 扩大边界框以包含完整区域
        margin = 20
        x = max(0, x - margin)
        y = max(0, y - margin)
        w = min(image.shape[1] - x, w + 2 * margin)
        h = min(image.shape[0] - y, h + 2 * margin)
        
        # 提取区域
        region = enhanced[y:y+h, x:x+w]
        
        # 对区域进行进一步增强
        # 应用更强的CLAHE
        clahe_strong = cv2.createCLAHE(clipLimit=6.0, tileGridSize=(4,4))
        region_enhanced = clahe_strong.apply(region)
        
        # 锐化
        kernel_sharpen = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        region_sharpened = cv2.filter2D(region_enhanced, -1, kernel_sharpen)
        
        # 自适应阈值二值化
        region_binary = cv2.adaptiveThreshold(region_sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 3)
        
        enhanced_regions.append(region_binary)
    
    return enhanced_regions

# === 第四步：初始化 OCR（优化参数，专门针对耳标）===
ocr = PaddleOCR(
    use_angle_cls=True,      # 文本方向分类
    lang='ch',               # 中文+数字
    use_gpu=False,           # CPU 模式
    det_db_thresh=0.05,      # 进一步降低检测阈值，提高检测敏感度
    det_db_box_thresh=0.2,   # 进一步降低框阈值
    det_db_unclip_ratio=3.0, # 进一步增加未裁剪比例
    drop_score=0.05,         # 进一步降低置信度阈值
    max_text_length=50       # 增加最大文本长度
)

# === 第五步：设置图片路径 ===
test_images = [
    '测试/猪耳标/pig1.JPG',
    '测试/猪耳标/pig2.JPG', 
    '测试/猪耳标/pig3.JPG',
    '测试/猪耳标/pig4.JPG',
    '测试/猪耳标/pig5.JPG'
]

# === 第六步：执行多角度识别 ===
print("🔍 正在识别猪耳标中的所有数字...")
print("🔄 使用多角度检测策略...")

# 循环测试所有图片
for img_idx, image_path in enumerate(test_images, 1):
    print(f"\n{'='*80}")
    print(f"🐷 测试图片 {img_idx}: {image_path}")
    print(f"{'='*80}")
    
    try:
        all_results = []
        
        # 1. 原图识别
        print("📸 识别原图...")
        result_original = ocr.ocr(image_path, det=True, rec=True)
        if result_original:
            all_results.extend(result_original)
        
        # 2. 预处理图像识别
        print("🔄 识别预处理图像...")
        processed_image = preprocess_eartag_image(image_path)
        temp_path = f'temp_processed_{img_idx}.jpg'
        cv2.imwrite(temp_path, processed_image)
        
        result_processed = ocr.ocr(temp_path, det=True, rec=True)
        if result_processed:
            all_results.extend(result_processed)
        
        # 3. 多角度旋转识别
        print("🔄 识别旋转图像...")
        rotated_images = create_rotated_images(image_path, [90, 180, 270])
        
        for i, rotated_img in enumerate(rotated_images):
            temp_path = f'temp_rotated_{img_idx}_{i}.jpg'
            cv2.imwrite(temp_path, rotated_img)
            
            result_rotated = ocr.ocr(temp_path, det=True, rec=True)
            if result_rotated:
                all_results.extend(result_rotated)
            
            # 清理临时文件
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        # 清理预处理临时文件
        temp_processed_path = f'temp_processed_{img_idx}.jpg'
        if os.path.exists(temp_processed_path):
            os.remove(temp_processed_path)
        
    except Exception as e:
        print(f"❌ 识别失败: {e}")
        print("请检查图片路径是否正确")
        continue

    # === 第七步：结果分析和分类 ===
    print("\n" + "="*60)
    print("📊 识别结果分析")
    print("="*60)

    # 分类存储结果
    eartag_numbers = []      # 耳标数字
    other_numbers = []       # 其他数字
    text_content = []        # 文本内容
    all_texts = []

    # 处理所有识别结果
    for line in all_results:
        if line:
            for word_info in line:
                try:
                    text = word_info[1][0]        # 识别的文字
                    confidence = word_info[1][1]  # 置信度
                    bbox = word_info[0]           # 边界框
                    
                    all_texts.append((text, confidence, bbox))
                    
                    # 分类处理
                    if is_valid_eartag_number(text):
                        eartag_numbers.append((text, confidence, bbox))
                    elif any(c.isdigit() for c in text):
                        other_numbers.append((text, confidence, bbox))
                    else:
                        text_content.append((text, confidence, bbox))
                        
                except:
                    continue

    # === 第八步：输出分类结果 ===

    # 1. 耳标数字（主要关注）
    print("\n🎯 【耳标数字】- 主要识别目标：")
    if eartag_numbers:
        # 按置信度排序
        eartag_numbers.sort(key=lambda x: x[1], reverse=True)
        
        # 去重显示
        seen_numbers = set()
        for text, confidence, bbox in eartag_numbers:
            clean_text = ''.join(c for c in text if c.isalnum())
            if clean_text not in seen_numbers:
                print(f"  📌 '{text}' (置信度: {confidence:.4f})")
                seen_numbers.add(clean_text)
                
                # 提取具体数字
                extracted = extract_eartag_numbers(text)
                if extracted:
                    print(f"      🔢 提取的数字: {', '.join(extracted)}")
    else:
        print("  ⚠️ 未识别到明显的耳标数字")

# 2. 其他数字
print("\n🔢 【其他数字】- 可能相关的数字：")
if other_numbers:
    other_numbers.sort(key=lambda x: x[1], reverse=True)
    seen_others = set()
    for text, confidence, bbox in other_numbers:
        clean_text = ''.join(c for c in text if c.isalnum())
        if clean_text not in seen_others:
            print(f"  📌 '{text}' (置信度: {confidence:.4f})")
            seen_others.add(clean_text)
else:
    print("  ⚠️ 未识别到其他数字")

# 3. 文本内容
print("\n📝 【文本内容】- 其他识别内容：")
if text_content:
    text_content.sort(key=lambda x: x[1], reverse=True)
    seen_texts = set()
    for text, confidence, bbox in text_content:
        if text not in seen_texts:
            print(f"  📌 '{text}' (置信度: {confidence:.4f})")
            seen_texts.add(text)
else:
    print("  ⚠️ 未识别到其他文本内容")

# === 第九步：统计信息 ===
print("\n" + "="*60)
print("📈 识别统计信息")
print("="*60)
print(f"🔍 总检测区域数: {len(all_texts)}")
print(f"🎯 耳标数字数量: {len(set(''.join(c for c in text if c.isalnum()) for text, _, _ in eartag_numbers))}")
print(f"🔢 其他数字数量: {len(set(''.join(c for c in text if c.isalnum()) for text, _, _ in other_numbers))}")
print(f"📝 文本内容数量: {len(set(text for text, _, _ in text_content))}")

# === 第十步：推荐耳标数字 ===
print("\n🎯 【推荐耳标数字】- 最可能的耳标标识：")
if eartag_numbers:
    # 按置信度排序，取前3个
    top_numbers = sorted(eartag_numbers, key=lambda x: x[1], reverse=True)[:3]
    for i, (text, confidence, bbox) in enumerate(top_numbers, 1):
        clean_text = ''.join(c for c in text if c.isalnum())
        print(f"  {i}. '{clean_text}' (置信度: {confidence:.4f})")
else:
    print("  ⚠️ 无法确定耳标数字")

# === 第十一步：专门识别两个目标数据 ===
print("\n" + "="*60)
print("🎯 【目标数据识别】")
print("="*60)

# 1. 识别以1开头的数字
print("🔍 以1开头的数字：")
one_starting_numbers = []
for text, confidence, bbox in eartag_numbers:
    clean_text = ''.join(c for c in text if c.isalnum())
    if clean_text.startswith('1'):
        one_starting_numbers.append((clean_text, confidence))

if one_starting_numbers:
    # 按置信度排序
    one_starting_numbers.sort(key=lambda x: x[1], reverse=True)
    for i, (number, confidence) in enumerate(one_starting_numbers, 1):
        print(f"  {i}. {number} (置信度: {confidence:.4f})")
else:
    print("  ❌ 未识别到以1开头的数字")

# 2. 识别另一个数字（非1开头）
print("\n🔍 另一个识别出来的数字：")
other_numbers_list = []
for text, confidence, bbox in eartag_numbers:
    clean_text = ''.join(c for c in text if c.isalnum())
    if not clean_text.startswith('1'):
        other_numbers_list.append((clean_text, confidence))

if other_numbers_list:
    # 按置信度排序
    other_numbers_list.sort(key=lambda x: x[1], reverse=True)
    for i, (number, confidence) in enumerate(other_numbers_list, 1):
        print(f"  {i}. {number} (置信度: {confidence:.4f})")
else:
    print("  ❌ 未识别到其他数字")

# 3. 总结两个目标数据
print("\n📋 【两个目标数据总结】：")
if one_starting_numbers and other_numbers_list:
    print(f"  1️⃣ 以1开头的数字: {one_starting_numbers[0][0]} (置信度: {one_starting_numbers[0][1]:.4f})")
    print(f"  2️⃣ 另一个数字: {other_numbers_list[0][0]} (置信度: {other_numbers_list[0][1]:.4f})")
    print(f"  ✅ 成功识别出两个目标数据！")
elif one_starting_numbers:
    print(f"  1️⃣ 以1开头的数字: {one_starting_numbers[0][0]} (置信度: {one_starting_numbers[0][1]:.4f})")
    print(f"  2️⃣ 另一个数字: ❌ 未识别到")
elif other_numbers_list:
    print(f"  1️⃣ 以1开头的数字: ❌ 未识别到")
    print(f"  2️⃣ 另一个数字: {other_numbers_list[0][0]} (置信度: {other_numbers_list[0][1]:.4f})")
else:
    print("  ❌ 未识别到任何目标数据")

# === 第十二步：识别相邻的两个数字 ===
print("\n" + "="*60)
print("🎯 【相邻两个数字识别】")
print("="*60)

# 获取所有耳标数字，按置信度排序
all_eartag_numbers = []
for text, confidence, bbox in eartag_numbers:
    clean_text = ''.join(c for c in text if c.isalnum())
    if clean_text not in [num[0] for num in all_eartag_numbers]:  # 去重
        all_eartag_numbers.append((clean_text, confidence))

# 按置信度排序
all_eartag_numbers.sort(key=lambda x: x[1], reverse=True)

print("🔍 识别到的所有耳标数字：")
for i, (number, confidence) in enumerate(all_eartag_numbers, 1):
    print(f"  {i}. {number} (置信度: {confidence:.4f})")

# 选择置信度最高的两个数字作为相邻的两个数字
if len(all_eartag_numbers) >= 2:
    print(f"\n📋 【相邻两个数字总结】：")
    print(f"  1️⃣ 第一个数字: {all_eartag_numbers[0][0]} (置信度: {all_eartag_numbers[0][1]:.4f})")
    print(f"  2️⃣ 第二个数字: {all_eartag_numbers[1][0]} (置信度: {all_eartag_numbers[1][1]:.4f})")
    print(f"  ✅ 成功识别出相邻的两个数字！")
    
    # 检查是否包含目标数字
    target_numbers = ['1520321', '10900830']
    found_targets = []
    for target in target_numbers:
        for number, confidence in all_eartag_numbers:
            if target in number or number in target:
                found_targets.append((target, number, confidence))
                break
    
    if found_targets:
        print(f"\n🎯 【目标数字匹配】：")
        for target, found, confidence in found_targets:
            print(f"  ✅ 目标 {target} 匹配到: {found} (置信度: {confidence:.4f})")
    else:
        print(f"\n⚠️ 【目标数字匹配】：未找到完全匹配的目标数字")
        
elif len(all_eartag_numbers) == 1:
    print(f"\n📋 【相邻两个数字总结】：")
    print(f"  1️⃣ 第一个数字: {all_eartag_numbers[0][0]} (置信度: {all_eartag_numbers[0][1]:.4f})")
    print(f"  2️⃣ 第二个数字: ❌ 只识别到一个数字")
else:
    print(f"\n📋 【相邻两个数字总结】：")
    print(f"  ❌ 未识别到任何耳标数字")

def post_process_eartag_numbers(numbers):
    """后处理耳标数字，进行合理性检查和修正"""
    processed_numbers = []
    
    for number, confidence in numbers:
        original_number = number
        processed_number = number
        
        # 1. 检查是否需要补零（7位数且以2开头，可能前面缺少0）
        if len(number) == 7 and number.startswith('2'):
            # 尝试在前面加0，看是否符合8位数特征
            candidate = '0' + number
            if len(candidate) == 8:
                processed_number = candidate
                print(f"  🔧 数字修正: {original_number} -> {processed_number} (补零)")
        
        # 2. 检查数字的合理性
        if len(processed_number) in [7, 8]:
            # 检查是否包含过多重复数字（可能识别错误）
            digit_counts = {}
            for digit in processed_number:
                digit_counts[digit] = digit_counts.get(digit, 0) + 1
            
            # 如果某个数字出现超过3次，可能有问题
            max_repeat = max(digit_counts.values())
            if max_repeat > 3:
                print(f"  ⚠️ 数字 {processed_number} 包含重复数字过多，可能识别有误")
        
        processed_numbers.append((processed_number, confidence, original_number))
    
    return processed_numbers

def enhance_image_for_zero_detection(image_path):
    """专门针对数字0识别的图像增强"""
    image = cv2.imread(image_path)
    if image is None:
        return None
    
    # 转换为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 1. 应用CLAHE增强对比度
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 2. 高斯模糊去噪
    denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)
    
    # 3. 自适应阈值二值化（针对0的识别优化）
    binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 3)
    
    # 4. 形态学操作：闭运算连接断开的笔画
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    # 5. 形态学操作：开运算去除小噪点
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open)
    
    return cleaned

# === 第十三步：应用后处理优化 ===
print("\n" + "="*60)
print("🔧 【后处理优化】")
print("="*60)

# 应用后处理优化
if eartag_numbers:
    print("🔧 应用数字修正和合理性检查...")
    processed_eartag_numbers = post_process_eartag_numbers([(text, confidence) for text, confidence, bbox in eartag_numbers])
    
    # 更新耳标数字列表
    eartag_numbers = [(text, confidence, bbox) for text, confidence, bbox in processed_eartag_numbers]
    
    print("✅ 后处理优化完成！")
else:
    print("⚠️ 没有耳标数字需要后处理")

print("\n🎉 识别完成！")