# -*- coding: utf-8 -*-
"""
身份证识别模块 - 独立模块
专门用于识别身份证中的姓名和身份证号码
"""

import logging
import re

# 设置日志
logger = logging.getLogger(__name__)

class IDCardOCR:
    """身份证OCR识别类"""
    
    def __init__(self):
        """初始化"""
        pass
    
    def extract_id_card_enhanced(self, texts_with_boxes):
        """提取身份证中的关键信息"""
        name = None
        id_number = None
        
        # 提取姓名
        for b in texts_with_boxes:
            text = b["text"].strip()
            # 姓名通常在"姓名"后面，或者包含中文姓名特征
            if "姓名" in text:
                # 提取"姓名"后面的内容 - 改进正则表达式
                name_match = re.search(r'姓名[：:]?\s*([^\s]+)', text)
                if name_match:
                    name = name_match.group(1).strip()
                else:
                    # 如果没有找到冒号，直接提取"姓名"后面的内容
                    name_match = re.search(r'姓名([^\s]+)', text)
                    if name_match:
                        name = name_match.group(1).strip()
            elif "名" in text and len(text) <= 10:
                # 处理类似"08名杨春兰"的情况
                name_match = re.search(r'名([\u4e00-\u9fa5]{2,4})', text)
                if name_match:
                    name = name_match.group(1).strip()
            elif re.match(r'^[\u4e00-\u9fa5]{2,4}$', text) and len(text) <= 4:
                # 纯中文，2-4个字符，可能是姓名
                if not name:
                    name = text
        
        # 提取身份证号码
        for b in texts_with_boxes:
            text = b["text"].strip()
            # 查找18位身份证号码 - 改进正则表达式
            id_match = re.search(r'\b\d{18}\b', text)
            if id_match:
                id_number = id_match.group(0)
                break
            else:
                # 如果没有单词边界，直接查找18位数字
                id_match = re.search(r'\d{18}', text)
                if id_match:
                    id_number = id_match.group(0)
                    break
        
        result = {
            "name": name if name else "未识别",
            "id_number": id_number if id_number else "未识别"
        }
        
        logger.info(f"📌 身份证提取结果: {result}")
        return result

# 创建全局实例
idcard_ocr = IDCardOCR()

def recognize_id_card(texts_with_boxes):
    """身份证识别接口函数"""
    return idcard_ocr.extract_id_card_enhanced(texts_with_boxes)
