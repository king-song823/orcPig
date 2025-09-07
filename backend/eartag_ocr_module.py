# -*- coding: utf-8 -*-
"""
猪耳标识别模块 - 独立模块
专门用于识别猪耳标中的7位和8位数字
基于demo_eartag_ocr.py的科学方案
"""

import logging
import cv2
import numpy as np
import re
from paddleocr import PaddleOCR

# 设置日志
logger = logging.getLogger(__name__)

class EartagOCR:
    """猪耳标OCR识别类"""
    
    def __init__(self):
        """初始化OCR引擎 - 基于demo_eartag_ocr.py的优化参数"""
        self.ocr = PaddleOCR(
            use_angle_cls=True,      # 文本方向分类
            lang='ch',               # 中文+数字
            use_gpu=False,           # CPU 模式
            det_db_thresh=0.05,      # 进一步降低检测阈值，提高检测敏感度
            det_db_box_thresh=0.2,   # 进一步降低框阈值
            det_db_unclip_ratio=3.0, # 进一步增加未裁剪比例
            drop_score=0.05,         # 进一步降低置信度阈值
            max_text_length=50,      # 增加最大文本长度
            show_log=False
        )
    
    def is_valid_eartag_number(self, text):
        """判断是否为有效的耳标数字（基于demo_eartag_ocr.py的验证逻辑）"""
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
        
        # 过滤掉明显的日期格式（如2025-08-0, 2025080等）
        if self._is_date_format(clean_text):
            return False
        
        return True
    
    def _is_date_format(self, text):
        """检查是否为日期格式，用于过滤误识别"""
        # 检查是否包含常见的日期模式
        date_patterns = [
            r'^20\d{2}[0-1]\d[0-3]\d$',  # 2025080 格式
            r'^20\d{2}-[0-1]\d-[0-3]\d$',  # 2025-08-0 格式
            r'^\d{4}-\d{2}-\d{1}$',  # 2025-08-0 格式
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, text):
                return True
        
        # 检查是否以202开头且长度合适（可能是年份）
        if text.startswith('202') and len(text) >= 6:
            return True
            
        return False
    
    def extract_eartag_numbers(self, text):
        """从文本中提取可能的耳标数字（基于demo_eartag_ocr.py）"""
        # 使用正则表达式匹配连续的数字序列
        numbers = re.findall(r'\d{4,}', text)
        return numbers
    
    def extract_circular_rois(self, img):
        """检测并提取圆形耳标区域，返回裁剪后的ROI列表。
        优先只对这些圆形区域进行OCR，过滤其他区域干扰。
        """
        try:
            if img is None:
                return []
            # 转灰度与降噪
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
            blur = cv2.GaussianBlur(gray, (7, 7), 1.5)
            # Hough 圆检测 - 简化参数以提高性能
            param_sets = [
                (1.2, 50, 60, 20),  # 只保留一组参数
            ]
            rois = []
            h, w = gray.shape[:2]
            for dp, minDist, param1, param2 in param_sets:
                circles = cv2.HoughCircles(
                    blur,
                    cv2.HOUGH_GRADIENT,
                    dp=dp,
                    minDist=min(h, w) // 8,
                    param1=param1,
                    param2=param2,
                    minRadius=min(h, w) // 12,
                    maxRadius=min(h, w) // 2,
                )
                if circles is not None:
                    circles = np.uint16(np.around(circles))
                    # 只保留最多3个半径较大的圆以避免超时
                    sorted_circles = sorted(circles[0, :], key=lambda x: x[2], reverse=True)[:3]
                    for c in sorted_circles:
                        cx, cy, r = int(c[0]), int(c[1]), int(c[2])
                        # 创建圆形掩膜
                        mask = np.zeros_like(gray)
                        cv2.circle(mask, (cx, cy), r, 255, -1)
                        masked = cv2.bitwise_and(img, img, mask=mask)
                        # 以圆为中心裁剪正方形ROI，带边距
                        margin = int(r * 0.2)
                        x1 = max(0, cx - r - margin)
                        y1 = max(0, cy - r - margin)
                        x2 = min(w, cx + r + margin)
                        y2 = min(h, cy + r + margin)
                        roi = masked[y1:y2, x1:x2]
                        # 过滤极小区域
                        if roi is not None and roi.size > 0 and roi.shape[0] > 20 and roi.shape[1] > 20:
                            rois.append(roi)
                if rois:
                    break
            return rois
        except Exception as e:
            logger.error(f"圆形ROI提取错误: {e}")
            return []
    
    def extract_numbers_from_mixed_text(self, text):
        """从混合文本中提取7位和8位数字"""
        import re
        # 提取所有连续的数字序列
        numbers = re.findall(r'\d+', text)
        valid_numbers = []
        
        for num in numbers:
            if len(num) == 7 or len(num) == 8:
                valid_numbers.append(num)
        
        return valid_numbers
    
    def clean_text_for_eartag(self, text):
        """清理文本，去除中文字符和特殊符号，只保留数字和字母"""
        import re
        # 只保留数字和字母
        cleaned = re.sub(r'[^\w]', '', text)
        # 去除中文字符（保留数字和英文字母）
        cleaned = re.sub(r'[^\x00-\x7F]', '', cleaned)
        return cleaned
    
    def post_process_eartag_numbers(self, numbers):
        """后处理耳标数字，进行合理性检查和修正（参考demo_eartag_ocr.py）"""
        processed_numbers = []
        
        for number, confidence in numbers:
            original_number = number
            processed_number = number
            
            # 1. 检查数字的合理性
            if len(processed_number) in [7, 8]:
                # 检查是否包含过多重复数字（可能识别错误）
                digit_counts = {}
                for digit in processed_number:
                    digit_counts[digit] = digit_counts.get(digit, 0) + 1
                
                # 如果某个数字出现超过3次，可能有问题
                max_repeat = max(digit_counts.values())
                if max_repeat > 3:
                    logger.warning(f"⚠️ 数字 {processed_number} 包含重复数字过多，可能识别有误")
                    # 对于重复数字过多的数字，降低其优先级但不完全排除
                    confidence = confidence * 0.5
            
            processed_numbers.append((processed_number, confidence, original_number))
        
        return processed_numbers
    
    def detect_and_correct_rotation(self, img):
        """检测并校正图像旋转"""
        try:
            # 转换为灰度图
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img.copy()
            
            # 边缘检测
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # 霍夫直线检测
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None and len(lines) > 0:
                # 计算主要角度
                angles = []
                for line in lines:
                    rho, theta = line[0]
                    angle = theta * 180 / np.pi
                    if angle > 90:
                        angle = angle - 180
                    angles.append(angle)
                
                # 计算平均角度
                avg_angle = np.mean(angles)
                logger.info(f"🔍 检测到旋转角度: {avg_angle:.2f}度")
                
                # 如果角度大于阈值，进行校正
                if abs(avg_angle) > 5:
                    # 计算旋转中心
                    height, width = gray.shape[:2]
                    center = (width // 2, height // 2)
                    
                    # 创建旋转矩阵
                    rotation_matrix = cv2.getRotationMatrix2D(center, -avg_angle, 1.0)
                    
                    # 执行旋转
                    corrected = cv2.warpAffine(img, rotation_matrix, (width, height))
                    logger.info(f"✅ 已校正旋转角度: {avg_angle:.2f}度")
                    return corrected
            
            return img
            
        except Exception as e:
            logger.error(f"旋转检测错误: {e}")
            return img
    
    def preprocess_image_for_eartag(self, img):
        """专门针对猪耳标的图像预处理 - 增强版"""
        try:
            # 首先进行旋转检测和校正
            corrected_img = self.detect_and_correct_rotation(img)
            
            # 转换为灰度图
            gray = cv2.cvtColor(corrected_img, cv2.COLOR_BGR2GRAY)
            
            # 多种预处理方案，提高8位数字识别率
            preprocessed_images = []
            
            # 方案1: 标准处理
            denoised1 = cv2.GaussianBlur(gray, (3, 3), 0)
            clahe1 = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced1 = clahe1.apply(denoised1)
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened1 = cv2.filter2D(enhanced1, -1, kernel)
            binary1 = cv2.adaptiveThreshold(sharpened1, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            preprocessed_images.append(binary1)
            
            # 方案2: 强对比度处理（针对模糊的8位数字）
            denoised2 = cv2.GaussianBlur(gray, (5, 5), 0)
            clahe2 = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(6, 6))
            enhanced2 = clahe2.apply(denoised2)
            # 更强的锐化
            kernel_strong = np.array([[-2,-2,-2], [-2,17,-2], [-2,-2,-2]])
            sharpened2 = cv2.filter2D(enhanced2, -1, kernel_strong)
            binary2 = cv2.adaptiveThreshold(sharpened2, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 3)
            preprocessed_images.append(binary2)
            
            # 方案3: 伽马校正 + 双边滤波
            gamma = 1.3
            lookup_table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255 for i in np.arange(0, 256)]).astype("uint8")
            gamma_corrected = cv2.LUT(gray, lookup_table)
            bilateral = cv2.bilateralFilter(gamma_corrected, 9, 75, 75)
            binary3 = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 13, 2)
            preprocessed_images.append(binary3)
            
            # 方案4: 对比度增强
            enhanced4 = cv2.convertScaleAbs(gray, alpha=1.8, beta=40)
            denoised4 = cv2.GaussianBlur(enhanced4, (3, 3), 0)
            binary4 = cv2.adaptiveThreshold(denoised4, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 9, 2)
            preprocessed_images.append(binary4)
            
            # 方案5: 形态学增强
            denoised5 = cv2.GaussianBlur(gray, (3, 3), 0)
            clahe5 = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(7, 7))
            enhanced5 = clahe5.apply(denoised5)
            # 开运算去除噪点
            kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            opened = cv2.morphologyEx(enhanced5, cv2.MORPH_OPEN, kernel_open)
            binary5 = cv2.adaptiveThreshold(opened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            preprocessed_images.append(binary5)
            
            # 对每个预处理图像进行形态学操作
            final_images = []
            for binary in preprocessed_images:
                # 形态学操作，去除噪点
                kernel = np.ones((2, 2), np.uint8)
                cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
                cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
                
                # 确保图像是3通道的，因为PaddleOCR期望彩色图像
                if len(cleaned.shape) == 2:
                    cleaned = cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)
                
                final_images.append(cleaned)
            
            return final_images
            
        except Exception as e:
            logger.error(f"猪耳标图像预处理错误: {e}")
            return [img]
    
    def create_rotated_images(self, img, angles=[0, 90, 180, 270]):
        """创建多个旋转角度的图像用于识别颠倒的数字（基于demo_eartag_ocr.py）"""
        rotated_images = []
        for angle in angles:
            if angle == 0:
                rotated_images.append(img)
            else:
                # 计算旋转中心
                height, width = img.shape[:2]
                center = (width // 2, height // 2)
                
                # 创建旋转矩阵
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                
                # 执行旋转
                rotated = cv2.warpAffine(img, rotation_matrix, (width, height))
                rotated_images.append(rotated)
        
        return rotated_images
    
    def enhance_image_for_blur_detection(self, img):
        """专门针对模糊图像的增强处理"""
        try:
            # 转换为灰度图
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img.copy()
            
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
            
            # 确保图像是3通道的
            if len(cleaned.shape) == 2:
                cleaned = cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"模糊图像增强错误: {e}")
            return img
    
    def enhanced_ocr_image_for_eartag(self, image_bytes):
        """增强版猪耳标OCR识别 - 基于demo_eartag_ocr.py的多角度策略"""
        try:
            # 解码图像
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                logger.error("❌ 无法解码图像")
                return []
            
            all_results = []
            
            # === 第一层：原图识别 ===
            logger.info("🐷 【第一层】原图识别...")
            try:
                result_original = self.ocr.ocr(img, det=True, rec=True)
                if result_original:
                    all_results.extend(result_original)
            except Exception as e:
                logger.warning(f"原图OCR失败: {e}")
            
            # === 第二层：预处理图像识别 ===
            logger.info("🐷 【第二层】预处理图像识别...")
            try:
                # 使用demo_eartag_ocr.py的预处理方法
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                enhanced = clahe.apply(gray)
                denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)
                binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
                
                result_processed = self.ocr.ocr(cleaned, det=True, rec=True)
                if result_processed:
                    all_results.extend(result_processed)
            except Exception as e:
                logger.warning(f"预处理OCR失败: {e}")
            
            # === 第三层：多角度旋转识别（demo_eartag_ocr.py的核心优势）===
            logger.info("🐷 【第三层】多角度旋转识别...")
            try:
                rotated_images = self.create_rotated_images(img, [90, 180, 270])
                
                for rotated_img in rotated_images:
                    try:
                        result_rotated = self.ocr.ocr(rotated_img, det=True, rec=True)
                        if result_rotated:
                            all_results.extend(result_rotated)
                    except Exception as e:
                        logger.warning(f"旋转图像OCR失败: {e}")
                
                logger.info("🐷 多角度旋转识别完成")
            except Exception as e:
                logger.warning(f"多角度旋转识别失败: {e}")
            
            # 处理识别结果
            unique_results = []
            seen_texts = set()
            
            for result in all_results:
                if result and len(result) > 0:
                    for line in result:
                        if len(line) >= 2:
                            text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                            confidence = line[1][1] if isinstance(line[1], (list, tuple)) and len(line[1]) > 1 else 0.5
                            bbox = line[0] if len(line) > 0 else None
                            
                            # 清理文本用于去重
                            clean_text = ''.join(c for c in text if c.isalnum())
                            
                            if clean_text not in seen_texts:
                                unique_results.append({
                                    "text": text,
                                    "confidence": confidence,
                                    "bbox": bbox
                                })
                                seen_texts.add(clean_text)
            
            logger.info(f"✅ 猪耳标多角度OCR识别到 {len(unique_results)} 个文本块")
            return unique_results
            
        except Exception as e:
            logger.error(f"猪耳标OCR识别错误: {e}")
            return []
    
    def extract_pig_ear_tag_enhanced(self, texts_with_boxes):
        """提取猪耳标中的耳标号码 - 基于demo_eartag_ocr.py的优化方案"""
        # 初始化结果
        result = {
            "ear_tag_7digit": "未识别",  # 7位耳标号码
            "ear_tag_8digit": "未识别",  # 8位耳标号码
        }
        
        # 分类存储结果
        eartag_numbers = []      # 耳标数字
        other_numbers = []       # 其他数字
        text_content = []        # 文本内容
        
        # 处理所有识别结果，进行分类
        for word_info in texts_with_boxes:
            try:
                text = word_info["text"]        # 识别的文字
                confidence = word_info.get("confidence", 0.0)  # 置信度
                
                # 清理文本，只保留数字和字母
                clean_text = ''.join(c for c in text if c.isalnum())
                
                # 分类处理 - 基于demo_eartag_ocr.py的逻辑
                if self.is_valid_eartag_number(clean_text):
                    eartag_numbers.append((clean_text, confidence))
                    logger.info(f"🎯 识别到耳标数字: '{clean_text}' (置信度: {confidence:.4f})")
                elif any(c.isdigit() for c in text):
                    # 混合文本，先尝试提取纯数字
                    extracted_numbers = self.extract_eartag_numbers(text)
                    if extracted_numbers:
                        # 如果提取到有效数字，检查是否为耳标数字
                        for num in extracted_numbers:
                            if self.is_valid_eartag_number(num):
                                eartag_numbers.append((num, confidence))
                                logger.info(f"🔧 从混合文本 '{text}' 提取耳标数字: {num}")
                            else:
                                other_numbers.append((num, confidence))
                    else:
                        other_numbers.append((text, confidence))
                else:
                    text_content.append((text, confidence))
                    
            except Exception as e:
                logger.warning(f"处理文本时出错: {e}")
                continue
        
        logger.info(f"🔍 耳标数字候选: {[num[0] for num in eartag_numbers]}")
        logger.info(f"🔍 其他数字候选: {[num[0] for num in other_numbers]}")
        logger.info(f"🔍 详细耳标数字候选: {eartag_numbers}")
        
        # 按置信度排序耳标数字
        eartag_numbers.sort(key=lambda x: x[1], reverse=True)
        logger.info(f"🔍 排序后的耳标数字: {eartag_numbers}")
        
        # 去重并提取最可能的两个数字
        seen_numbers = set()
        valid_eartag_numbers = []
        
        for text, confidence in eartag_numbers:
            clean_text = ''.join(c for c in text if c.isalnum())
            if clean_text not in seen_numbers and len(clean_text) in [7, 8]:
                valid_eartag_numbers.append((clean_text, confidence))
                seen_numbers.add(clean_text)
        
        logger.info(f"🔍 有效耳标数字: {valid_eartag_numbers}")
        print(f"🔍 DEBUG: 有效耳标数字: {valid_eartag_numbers}")
        
        # 应用后处理优化（参考demo_eartag_ocr.py）
        if valid_eartag_numbers:
            logger.info("🔧 应用后处理优化...")
            processed_numbers = self.post_process_eartag_numbers(valid_eartag_numbers)
            # 更新为处理后的数字
            valid_eartag_numbers = [(num, conf) for num, conf, orig in processed_numbers]
            logger.info(f"🔧 后处理后的耳标数字: {valid_eartag_numbers}")
            print(f"🔍 DEBUG: 后处理后的耳标数字: {valid_eartag_numbers}")
        
        # 调试：显示最终的数字分配逻辑
        logger.info(f"🔍 开始数字分配，有效数字数量: {len(valid_eartag_numbers)}")
        
        # 选择最可能的两个数字 - 智能分配策略
        if len(valid_eartag_numbers) >= 2:
            # 按长度分类
            seven_digit_candidates = [(num, conf) for num, conf in valid_eartag_numbers if len(num) == 7]
            eight_digit_candidates = [(num, conf) for num, conf in valid_eartag_numbers if len(num) == 8]
            
            print(f"🔍 DEBUG: 7位候选: {seven_digit_candidates}")
            print(f"🔍 DEBUG: 8位候选: {eight_digit_candidates}")
            
            # 优先选择置信度最高的7位和8位数字
            if seven_digit_candidates and eight_digit_candidates:
                # 有7位和8位数字，优先选择以"1"开头的7位数字
                best_8digit = max(eight_digit_candidates, key=lambda x: x[1])
                
                # 优先选择以"1"开头的7位数字
                one_start_candidates = [c for c in seven_digit_candidates if c[0].startswith('1')]
                if one_start_candidates:
                    best_7digit = max(one_start_candidates, key=lambda x: x[1])
                    print(f"✅ DEBUG: 优先选择1开头的7位数字 - 7位: {best_7digit[0]}, 8位: {best_8digit[0]}")
                else:
                    # 如果没有以"1"开头的，选择置信度最高的
                    best_7digit = max(seven_digit_candidates, key=lambda x: x[1])
                    print(f"⚠️ DEBUG: 无1开头的7位数字，选择置信度最高的 - 7位: {best_7digit[0]}, 8位: {best_8digit[0]}")
                
                result["ear_tag_7digit"] = best_7digit[0]
                result["ear_tag_8digit"] = best_8digit[0]
            elif seven_digit_candidates:
                # 只有7位数字，优先选择以"1"开头的
                one_start_candidates = [c for c in seven_digit_candidates if c[0].startswith('1')]
                if one_start_candidates:
                    # 优先选择以"1"开头的7位数字
                    seven_digit_candidates = one_start_candidates
                    print(f"✅ DEBUG: 优先选择1开头的7位数字")
                
                seven_digit_candidates.sort(key=lambda x: x[1], reverse=True)
                result["ear_tag_7digit"] = seven_digit_candidates[0][0]
                if len(seven_digit_candidates) > 1:
                    # 第二个7位数字补零变成8位
                    result["ear_tag_8digit"] = seven_digit_candidates[1][0] + "0"
                else:
                    # 只有一个7位数字，补零变成8位
                    result["ear_tag_8digit"] = seven_digit_candidates[0][0] + "0"
                print(f"✅ DEBUG: 7位数字策略 - 7位: {result['ear_tag_7digit']}, 8位: {result['ear_tag_8digit']}")
            elif eight_digit_candidates:
                # 只有8位数字，选择置信度最高的两个
                eight_digit_candidates.sort(key=lambda x: x[1], reverse=True)
                result["ear_tag_8digit"] = eight_digit_candidates[0][0]
                if len(eight_digit_candidates) > 1:
                    # 第二个8位数字截取前7位
                    result["ear_tag_7digit"] = eight_digit_candidates[1][0][:7]
                else:
                    # 只有一个8位数字，截取前7位
                    result["ear_tag_7digit"] = eight_digit_candidates[0][0][:7]
                print(f"✅ DEBUG: 8位数字策略 - 7位: {result['ear_tag_7digit']}, 8位: {result['ear_tag_8digit']}")
            else:
                # 其他情况，按置信度分配
                first_num = valid_eartag_numbers[0][0]
                second_num = valid_eartag_numbers[1][0]
                print(f"🔍 DEBUG: 按长度分配 - first: {first_num}, second: {second_num}")
                
                if len(first_num) == 7 and len(second_num) == 8:
                    result["ear_tag_7digit"] = first_num
                    result["ear_tag_8digit"] = second_num
                elif len(first_num) == 8 and len(second_num) == 7:
                    result["ear_tag_7digit"] = second_num
                    result["ear_tag_8digit"] = first_num
                else:
                    # 其他情况，优先使用7位数字
                    for num, conf in valid_eartag_numbers:
                        if len(num) == 7 and result["ear_tag_7digit"] == "未识别":
                            result["ear_tag_7digit"] = num
                        elif len(num) == 8 and result["ear_tag_8digit"] == "未识别":
                            result["ear_tag_8digit"] = num
                
        elif len(valid_eartag_numbers) == 1:
            # 只有一个有效数字
            num = valid_eartag_numbers[0][0]
            if len(num) == 7:
                result["ear_tag_7digit"] = num
                result["ear_tag_8digit"] = num + "0"
            elif len(num) == 8:
                result["ear_tag_7digit"] = num[:7]
                result["ear_tag_8digit"] = num
            else:
                result["ear_tag_7digit"] = num
                result["ear_tag_8digit"] = "未识别"
        
        # 如果还是没有找到，尝试从其他数字中寻找
        if result["ear_tag_7digit"] == "未识别" or result["ear_tag_8digit"] == "未识别":
            other_valid_numbers = []
            for text, confidence in other_numbers:
                clean_text = ''.join(c for c in text if c.isalnum())
                if len(clean_text) in [7, 8] and clean_text not in seen_numbers:
                    other_valid_numbers.append((clean_text, confidence))
            
            other_valid_numbers.sort(key=lambda x: x[1], reverse=True)
            
            if other_valid_numbers:
                for num, confidence in other_valid_numbers:
                    if result["ear_tag_7digit"] == "未识别" and len(num) == 7:
                        result["ear_tag_7digit"] = num
                    elif result["ear_tag_8digit"] == "未识别" and len(num) == 8:
                        result["ear_tag_8digit"] = num
                    elif result["ear_tag_7digit"] == "未识别" and len(num) == 8:
                        result["ear_tag_7digit"] = num[:7]
                    elif result["ear_tag_8digit"] == "未识别" and len(num) == 7:
                        result["ear_tag_8digit"] = num + "0"
        
        logger.info(f"📌 科学猪耳标提取结果: {result}")
        print(f"🔍 DEBUG: 最终结果 - 7位: {result['ear_tag_7digit']}, 8位: {result['ear_tag_8digit']}")
        return result
    
    def recognize_eartag(self, image_bytes):
        """猪耳标识别主函数"""
        try:
            # 执行增强OCR识别
            texts_with_boxes = self.enhanced_ocr_image_for_eartag(image_bytes)
            
            if not texts_with_boxes:
                logger.warning("⚠️ 未识别到任何文本")
                return {
                    "ear_tag_7digit": "未识别",
                    "ear_tag_8digit": "未识别"
                }
            
            # 提取耳标数字
            result = self.extract_pig_ear_tag_enhanced(texts_with_boxes)
            return result
            
        except Exception as e:
            logger.error(f"猪耳标识别错误: {e}")
            return {
                "ear_tag_7digit": "未识别",
                "ear_tag_8digit": "未识别"
            }

# 创建全局实例
eartag_ocr = EartagOCR()

def recognize_pig_ear_tag(image_bytes):
    """猪耳标识别接口函数"""
    return eartag_ocr.recognize_eartag(image_bytes)
