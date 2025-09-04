# -*- coding: utf-8 -*-
"""
系统截图识别模块 - 独立模块
专门用于识别系统截图中的保险相关信息
"""

import logging
import re

# 设置日志
logger = logging.getLogger(__name__)

class ScreenshotOCR:
    """系统截图OCR识别类"""
    
    def __init__(self):
        """初始化"""
        pass
    
    def normalize_date_to_yyyy_mm_dd(self, date_str):
        """将日期字符串标准化为YYYY-MM-DD格式"""
        if not date_str:
            return None
        
        # 匹配各种日期格式
        patterns = [
            r"(\d{4})-?(\d{1,2})-?(\d{1,2})",  # YYYY-MM-DD, YYYYMMDD
            r"(\d{4})年(\d{1,2})月(\d{1,2})日",  # YYYY年MM月DD日
            r"(\d{4})\.(\d{1,2})\.(\d{1,2})",   # YYYY.MM.DD
            r"(\d{4})/(\d{1,2})/(\d{1,2})",     # YYYY/MM/DD
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                year, month, day = match.groups()
                yyyy_int = int(year)
                mm_int = int(month)
                dd_int = int(day)
                
                # 验证日期合理性
                if (yyyy_int >= 2000 and yyyy_int <= 2030 and 
                    mm_int >= 1 and mm_int <= 12 and 
                    dd_int >= 1 and dd_int <= 31):
                    return f"{yyyy_int:04d}-{mm_int:02d}-{dd_int:02d}"
        
        return None
    
    def find_date_near(self, texts, keyword, window=15):
        """在关键词附近查找日期"""
        keyword_positions = []
        dates = []
        
        # 找到所有关键词位置
        for i, text in enumerate(texts):
            if keyword in text:
                keyword_positions.append(i)
        
        # 找到所有日期
        for i, text in enumerate(texts):
            date_match = re.search(r'\d{4}-\d{1,2}-\d{1,2}', text)
            if date_match:
                normalized_date = self.normalize_date_to_yyyy_mm_dd(date_match.group(0))
                if normalized_date:
                    dates.append((i, normalized_date))
        
        if not keyword_positions or not dates:
            return None
        
        # 为每个关键词位置找到最近的日期
        best_dates = []
        for kp in keyword_positions:
            candidates = []
            for date_pos, date_str in dates:
                distance = abs(date_pos - kp)
                if distance <= window:
                    candidates.append((distance, date_str, date_pos))
            
            if candidates:
                # 按距离排序，选择最近的
                candidates.sort(key=lambda x: x[0])
                best_dates.append(candidates[0])
        
        if not best_dates:
            return None
        
        # 如果有多个候选，选择最合理的
        if len(best_dates) == 1:
            return best_dates[0][1]
        
        # 多个候选时，选择距离最近的
        best_dates.sort(key=lambda x: x[0])
        return best_dates[0][1]
    
    def extract_system_screenshot_enhanced(self, texts_with_boxes):
        """提取系统截图中的关键信息"""
        texts = [b["text"] for b in texts_with_boxes]
        
        # 初始化结果
        result = {
            "policy_number": "未识别",
            "claim_number": "未识别", 
            "insured_person": "未识别",
            "insurance_subject": "育肥猪",  # 默认值
            "coverage_period": "未识别",
            "incident_date": "未识别",
            "incident_location": "未识别",
            "report_time": "未识别",
            "inspection_time": "未识别",
            "inspection_method": "未识别",
            "estimated_loss": "未识别",
            "incident_cause": "未识别"
        }
        
        # 提取保单号 - 匹配完整的P开头编号
        for text in texts:
            # 保单号以P开头，包含字母和数字的完整编号
            policy_match = re.search(r'P[A-Z0-9]{15,}', text)
            if policy_match:
                result["policy_number"] = policy_match.group(0)
                break
        
        # 提取报案号
        for text in texts:
            # 报案号以R开头
            claim_match = re.search(r'R[A-Z0-9]+', text)
            if claim_match:
                result["claim_number"] = claim_match.group(0)
                break
        
        # 提取被保险人
        for text in texts:
            if "被保险人" in text:
                insured_match = re.search(r'被保险人[：:]\s*([^\s]+)', text)
                if insured_match:
                    result["insured_person"] = insured_match.group(1).strip()
                    break
        
        # 提取保险标的
        for text in texts:
            if "保险标的" in text:
                subject_match = re.search(r'保险标的[：:]\s*([^\s]+)', text)
                if subject_match:
                    subject = subject_match.group(1).strip()
                    if subject and subject != "未识别":
                        result["insurance_subject"] = subject
                break
        
        # 提取保险期间 - 改进日期查找逻辑，支持相邻行搜索
        start_date = None
        end_date = None
        
        # 搜索起保日期 - 在关键词行及其相邻行中搜索
        for i, text in enumerate(texts):
            if "起保日期" in text:
                # 在当前行中搜索日期
                start_match = re.search(r'(\d{4}-\d{1,2}-\d{1,2})', text)
                if start_match:
                    start_date = start_match.group(1)
                    break
                # 如果当前行没有，在相邻行中搜索（扩大搜索范围）
                for j in range(max(0, i-5), min(len(texts), i+6)):
                    start_match = re.search(r'(\d{4}-\d{1,2}-\d{1,2})', texts[j])
                    if start_match:
                        start_date = start_match.group(1)
                        break
                if start_date:
                    break
        
        # 搜索终保日期 - 在关键词行及其相邻行中搜索
        for i, text in enumerate(texts):
            if "终保日期" in text:
                # 在当前行中搜索日期
                end_match = re.search(r'(\d{4}-\d{1,2}-\d{1,2})', text)
                if end_match:
                    end_date = end_match.group(1)
                    break
                # 如果当前行没有，在相邻行中搜索（扩大搜索范围）
                for j in range(max(0, i-5), min(len(texts), i+6)):
                    end_match = re.search(r'(\d{4}-\d{1,2}-\d{1,2})', texts[j])
                    if end_match:
                        end_date = end_match.group(1)
                        break
                if end_date:
                    break
        
        # 如果起保日期和终保日期相同，说明可能找到了同一个日期，需要重新搜索
        if start_date and end_date and start_date == end_date:
            # 重新搜索，确保找到不同的日期
            all_dates = []
            for i, text in enumerate(texts):
                if "起保日期" in text or "终保日期" in text:
                    # 在相邻行中搜索所有日期（扩大搜索范围）
                    for j in range(max(0, i-5), min(len(texts), i+6)):
                        date_matches = re.findall(r'(\d{4}-\d{1,2}-\d{1,2})', texts[j])
                        all_dates.extend(date_matches)
            
            # 去重并排序
            unique_dates = list(set(all_dates))
            if len(unique_dates) >= 2:
                unique_dates.sort()
                start_date = unique_dates[0]
                end_date = unique_dates[1]
            elif len(unique_dates) == 1:
                start_date = unique_dates[0]
                end_date = None
        
        # 设置保险期间
        if start_date and end_date:
            result["coverage_period"] = f"{start_date} 至 {end_date}"
        elif start_date:
            result["coverage_period"] = f"{start_date} 至 未识别"
        elif end_date:
            result["coverage_period"] = f"未识别 至 {end_date}"
        
        # 提取出险日期
        incident_date = self.find_date_near(texts, "出险日期", window=15)
        if incident_date:
            result["incident_date"] = incident_date
            result["report_time"] = incident_date
            result["inspection_time"] = incident_date
        
        # 提取出险地点 - 改进匹配逻辑
        for text in texts:
            if "出险地点" in text or "出险区域" in text or "投保区域" in text:
                # 优先匹配具体地址
                location_match = re.search(r'(?:出险地点|出险区域|投保区域)[：:]\s*([^\n]+)', text)
                if location_match:
                    location = location_match.group(1).strip()
                    if location and location != "未识别":
                        result["incident_location"] = location
                        break
                # 如果没有找到，尝试在附近文本中查找地址信息
                if not result["incident_location"] or result["incident_location"] == "未识别":
                    for i, t in enumerate(texts):
                        if "出险地点" in t or "出险区域" in t or "投保区域" in t:
                            # 在附近几行查找地址
                            for j in range(max(0, i-2), min(len(texts), i+3)):
                                if re.search(r'[省市区县乡村组]', texts[j]) and len(texts[j]) > 5:
                                    result["incident_location"] = texts[j].strip()
                                    break
                            if result["incident_location"] != "未识别":
                                break
        
        # 提取查勘方式 - 改进匹配逻辑，处理OCR识别错误
        for text in texts:
            # 直接匹配"现场查勘"文本
            if "现场查勘" in text:
                result["inspection_method"] = "现场查勘"
                break
            # 处理OCR识别错误：现场查助 -> 现场查勘
            elif "现场查助" in text:
                result["inspection_method"] = "现场查勘"
                break
            # 处理OCR识别错误：现汤查勘 -> 现场查勘
            elif "现汤查勘" in text:
                result["inspection_method"] = "现场查勘"
                break
            elif "查勘方式" in text or "处理方式" in text:
                # 查找查勘方式关键词
                if "现场" in text:
                    result["inspection_method"] = "现场查勘"
                    break
                elif "电话" in text:
                    result["inspection_method"] = "电话查勘"
                    break
                elif "视频" in text:
                    result["inspection_method"] = "视频查勘"
                    break
                elif "自助" in text:
                    result["inspection_method"] = "自助查勘"
                    break
                else:
                    # 尝试提取冒号后的内容
                    method_match = re.search(r'(?:查勘方式|处理方式)[：:]\s*([^\s\n]+)', text)
                    if method_match:
                        result["inspection_method"] = method_match.group(1).strip()
                        break
        
        # 提取估损金额 - 改进匹配逻辑
        for text in texts:
            # 查找估损金额相关关键词
            if "估损金额" in text or "估计赔款" in text or "估损" in text:
                # 匹配数字金额
                loss_match = re.search(r'(?:估损金额|估计赔款|估损)[：:]\s*([0-9,]+\.?\d*)', text)
                if loss_match:
                    result["estimated_loss"] = loss_match.group(1)
                    break
                # 如果没有找到，尝试在附近文本中查找金额
                if not result["estimated_loss"] or result["estimated_loss"] == "未识别":
                    for i, t in enumerate(texts):
                        if "估损金额" in t or "估计赔款" in t or "估损" in t:
                            # 在附近几行查找金额数字
                            for j in range(max(0, i-2), min(len(texts), i+3)):
                                amount_match = re.search(r'([0-9,]+\.?\d*)', texts[j])
                                if amount_match and float(amount_match.group(1).replace(',', '')) > 0:
                                    result["estimated_loss"] = amount_match.group(1)
                                    break
                            if result["estimated_loss"] != "未识别":
                                break
        
        # 提取出险原因 - 改进匹配逻辑
        for text in texts:
            # 直接匹配具体病因
            if "猪肺疫" in text or "猪瘟" in text or "猪丹毒" in text or "羊快疫" in text or "非传染病" in text:
                result["incident_cause"] = text.strip()
                break
            elif "出险原因" in text or "事故原因" in text or "病因" in text:
                # 优先匹配冒号后的内容
                cause_match = re.search(r'(?:出险原因|事故原因|病因)[：:]\s*([^\n]+)', text)
                if cause_match:
                    cause = cause_match.group(1).strip()
                    if cause and cause != "未识别":
                        result["incident_cause"] = cause
                        break
                # 如果没有找到，尝试在附近文本中查找原因
                if not result["incident_cause"] or result["incident_cause"] == "未识别":
                    for i, t in enumerate(texts):
                        if "出险原因" in t or "事故原因" in t or "病因" in t:
                            # 在附近几行查找原因文本
                            for j in range(max(0, i-2), min(len(texts), i+3)):
                                if len(texts[j]) > 2 and not re.search(r'[：:]', texts[j]):
                                    result["incident_cause"] = texts[j].strip()
                                    break
                            if result["incident_cause"] != "未识别":
                                break
        
        logger.info(f"📌 系统截图提取结果: {result}")
        return result

# 创建全局实例
screenshot_ocr = ScreenshotOCR()

def recognize_system_screenshot(texts_with_boxes):
    """系统截图识别接口函数"""
    return screenshot_ocr.extract_system_screenshot_enhanced(texts_with_boxes)
