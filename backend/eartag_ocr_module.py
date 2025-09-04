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
        """初始化OCR引擎"""
        self.ocr = PaddleOCR(
            use_angle_cls=True,      # 文本方向分类
            lang='ch',               # 中文+数字
            use_gpu=False,           # CPU 模式
            det_db_thresh=0.005,     # 极低检测阈值，提高8位数字检测敏感度
            det_db_box_thresh=0.05,  # 极低框阈值
            det_db_unclip_ratio=5.0, # 增加未裁剪比例，捕获更多数字
            drop_score=0.005,        # 极低置信度阈值
            max_text_length=100,     # 增加最大文本长度
            det_limit_side_len=960,  # 增加检测图像尺寸
            det_limit_type='max',    # 使用最大边限制
            rec_batch_num=6,         # 增加识别批处理数量
            show_log=False
        )
    
    def is_valid_eartag_number(self, text):
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
    
    def create_rotated_images(self, img, angles=[0, 90, 180, 270, 45, 135, 225, 315]):
        """创建多个旋转角度的图像用于识别颠倒的数字"""
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
        """增强版猪耳标OCR识别 - 智能分层策略"""
        try:
            # 解码图像
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                logger.error("❌ 无法解码图像")
                return []
            
            all_results = []
            
            # === 第一层：快速识别（原图 + 多种预处理）===
            logger.info("🐷 【第一层】快速识别...")
            
            # 1. 原图识别
            result_original = self.ocr.ocr(img, cls=True)
            if result_original and result_original[0]:
                all_results.extend(result_original[0])
            
            # 2. 多种预处理图像识别
            processed_imgs = self.preprocess_image_for_eartag(img)
            for processed_img in processed_imgs:
                result_processed = self.ocr.ocr(processed_img, cls=True)
                if result_processed and result_processed[0]:
                    all_results.extend(result_processed[0])
            
            # 3. 增强预处理图像识别
            enhanced_img = self.enhance_image_for_blur_detection(img)
            result_enhanced = self.ocr.ocr(enhanced_img, cls=True)
            if result_enhanced and result_enhanced[0]:
                all_results.extend(result_enhanced[0])
            
            # 检查第一层是否检测到足够的耳标候选数字
            eartag_candidates = 0
            for result in all_results:
                if result and len(result) >= 2:
                    text = result[1][0]
                    if self.is_valid_eartag_number(text):
                        eartag_candidates += 1
            
            logger.info(f"🐷 第一层识别结果：检测到 {eartag_candidates} 个耳标候选数字")
            
            # === 第二层：多角度旋转处理（如果需要）===
            if eartag_candidates < 2:
                logger.info("🐷 【第二层】多角度旋转处理...")
                
                # 创建多角度旋转图像
                rotated_images = self.create_rotated_images(img)
                
                for rotated_img in rotated_images:
                    result_rotated = self.ocr.ocr(rotated_img, cls=True)
                    if result_rotated and result_rotated[0]:
                        all_results.extend(result_rotated[0])
                
                logger.info("🐷 第二层多角度旋转处理完成")
            
            # 合并和去重结果
            unique_results = []
            seen_texts = set()
            
            for result in all_results:
                if result and len(result) >= 2:
                    text = result[1][0]
                    confidence = result[1][1]
                    
                    # 清理文本用于去重
                    clean_text = ''.join(c for c in text if c.isalnum())
                    
                    if clean_text not in seen_texts:
                        unique_results.append({
                            "text": text,
                            "confidence": confidence,
                            "bbox": result[0]
                        })
                        seen_texts.add(clean_text)
            
            logger.info(f"✅ 猪耳标智能分层OCR识别到 {len(unique_results)} 个文本块")
            return unique_results
            
        except Exception as e:
            logger.error(f"猪耳标OCR识别错误: {e}")
            return []
    
    def extract_pig_ear_tag_enhanced(self, texts_with_boxes):
        """提取猪耳标中的耳标号码 - 基于科学方案"""
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
                
                # 分类处理
                if self.is_valid_eartag_number(text):
                    eartag_numbers.append((text, confidence))
                elif any(c.isdigit() for c in text):
                    other_numbers.append((text, confidence))
                else:
                    text_content.append((text, confidence))
                    
            except:
                continue
        
        logger.info(f"🔍 耳标数字候选: {[num[0] for num in eartag_numbers]}")
        logger.info(f"🔍 其他数字候选: {[num[0] for num in other_numbers]}")
        
        # 按置信度排序耳标数字
        eartag_numbers.sort(key=lambda x: x[1], reverse=True)
        
        # 去重并提取最可能的两个数字
        seen_numbers = set()
        valid_eartag_numbers = []
        
        for text, confidence in eartag_numbers:
            clean_text = ''.join(c for c in text if c.isalnum())
            if clean_text not in seen_numbers and len(clean_text) in [7, 8]:
                valid_eartag_numbers.append((clean_text, confidence))
                seen_numbers.add(clean_text)
        
        logger.info(f"🔍 有效耳标数字: {valid_eartag_numbers}")
        
        # 选择最可能的两个数字
        if len(valid_eartag_numbers) >= 2:
            # 按置信度选择前两个
            first_num = valid_eartag_numbers[0][0]
            second_num = valid_eartag_numbers[1][0]
            
            # 根据长度分配7位和8位数字
            if len(first_num) == 7 and len(second_num) == 8:
                result["ear_tag_7digit"] = first_num
                result["ear_tag_8digit"] = second_num
            elif len(first_num) == 8 and len(second_num) == 7:
                result["ear_tag_7digit"] = second_num
                result["ear_tag_8digit"] = first_num
            elif len(first_num) == 7 and len(second_num) == 7:
                # 两个都是7位，选择置信度高的作为7位，另一个补0作为8位
                result["ear_tag_7digit"] = first_num
                result["ear_tag_8digit"] = second_num + "0"
            elif len(first_num) == 8 and len(second_num) == 8:
                # 两个都是8位，选择置信度高的作为8位，另一个截取前7位
                result["ear_tag_7digit"] = second_num[:7]
                result["ear_tag_8digit"] = first_num
            else:
                # 其他情况，按置信度分配
                result["ear_tag_7digit"] = first_num if len(first_num) == 7 else first_num[:7]
                result["ear_tag_8digit"] = second_num if len(second_num) == 8 else second_num + "0"
                
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
