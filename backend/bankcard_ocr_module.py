# -*- coding: utf-8 -*-
"""
银行卡识别模块 - 独立模块
专门用于识别银行卡中的银行名称和卡号
"""

import logging
import re

# 设置日志
logger = logging.getLogger(__name__)

class BankCardOCR:
    """银行卡OCR识别类"""
    
    def __init__(self):
        """初始化"""
        # 简易 BIN 映射（可按需扩充）
        self.bin_map = {
            # 农村信用社/农商常见 BIN（样例）
            '621779': '贵州农信',
            '621780': '农村信用社',
            '621781': '农村信用社',
            '621700': '农村信用社',
            # 常见银行示例（可继续补充真实 BIN）
            '622202': '中国工商银行',
            '621662': '中国建设银行',
            '622848': '农业银行',
            '621661': '中国银行',
            '622588': '招商银行',
            '622700': '建设银行',
            '622260': '交通银行',
            '622150': '中国邮政储蓄银行',
        }
    
    def extract_bank_card_enhanced(self, texts_with_boxes):
        """提取银行卡中的关键信息"""
        bank_name = "未识别"
        card_number = "未识别"
        
        # 提取全部候选银行卡号（容错：去除空格/短横线/点等分隔符），并打分选择最佳
        candidates = []
        joined_upper = " ".join([b["text"] for b in texts_with_boxes]).upper()
        has_unionpay = ("UNIONPAY" in joined_upper) or ("UNION PAY" in joined_upper)
        has_rccu = ("农村信用社" in joined_upper) or ("农信" in joined_upper) or ("信用社" in joined_upper)
        candidate_6217 = None
        for b in texts_with_boxes:
            text = b["text"].strip()
            # 所有16-19位序列（允许分隔符）
            for m in re.finditer(r'(?:\d[\s\-\.]?){16,19}', text):
                raw = m.group(0)
                digits = re.sub(r'[^0-9]', '', raw)
                if 16 <= len(digits) <= 19:
                    candidates.append(digits)
                    if digits.startswith('6217') and candidate_6217 is None:
                        candidate_6217 = digits
        # 去重
        candidates = list(dict.fromkeys(candidates))
        # 打分选择
        best = None
        best_score = -1
        best_62 = None
        best_62_score = -1
        def luhn_ok(num: str) -> bool:
            s = 0
            rev = num[::-1]
            for i, ch in enumerate(rev):
                n = int(ch)
                if i % 2 == 1:
                    n *= 2
                    if n > 9:
                        n -= 9
                s += n
            return s % 10 == 0
        for num in candidates:
            score = 0
            if luhn_ok(num):
                score += 3
            if num.startswith('62'):
                score += 2
            if has_unionpay and num.startswith('62'):
                score += 2
            if has_rccu and num.startswith('6217'):
                score += 2
            if len(num) == 19:
                score += 1
            if score > best_score:
                best_score = score
                best = num
            if num.startswith('62') and score > best_62_score:
                best_62_score = score
                best_62 = num
        # 优先选择以6217/62开头（银联/本地银行）的卡号；若有UnionPay更偏向本地62卡
        if candidate_6217 is not None:
            card_number = candidate_6217
        elif has_unionpay and best_62 is not None:
            card_number = best_62
        elif best_62 is not None:
            card_number = best_62
        elif best:
            card_number = best
        
        # 先根据候选卡号的 BIN 反推银行（优先级最高）
        inferred_from_bin = None
        for num in candidates:
            for bin_len in (8, 7, 6):
                if len(num) >= bin_len:
                    bin_key = num[:bin_len]
                    if bin_key in self.bin_map:
                        inferred_from_bin = self.bin_map[bin_key]
                        break
            if inferred_from_bin:
                break

        # 根据卡号前缀判断发卡网络（先判断更具体的前缀）
        if card_number != "未识别":
            # 先尝试 BIN 推测银行
            for bin_len in (8, 7, 6):
                if len(card_number) >= bin_len:
                    bin_key = card_number[:bin_len]
                    if bin_key in self.bin_map:
                        bank_name = self.bin_map[bin_key]
                        break
            # 发卡网络
            if card_number.startswith('62') and bank_name == "未识别":
                bank_name = "中国银联"
            elif card_number.startswith('65'):
                bank_name = "Discover"
            elif card_number.startswith('4'):
                bank_name = "Visa"
            elif card_number.startswith('5'):
                bank_name = "MasterCard"
            elif card_number.startswith('3'):
                bank_name = "American Express"
            elif card_number.startswith('6'):
                bank_name = "Discover"
        
        # 从文本中识别银行名称
        text_str = " ".join([b["text"] for b in texts_with_boxes])
        text_upper = text_str.upper()
        # BIN 反推若命中，优先使用
        if inferred_from_bin:
            bank_name = inferred_from_bin

        # 中文银行关键词优先覆盖
        if "贵州农信" in text_str or "贵州农村信用社" in text_str:
            bank_name = "贵州农信"
        elif "农村信用社" in text_str or "农信" in text_str or "信用社" in text_str:
            bank_name = "农村信用社"
        elif "农商银行" in text_str or "农村商业银行" in text_str:
            bank_name = "农村商业银行"
        elif "工商银行" in text_str or "ICBC" in text_upper:
            bank_name = "中国工商银行"
        elif "建设银行" in text_str or "CCB" in text_upper:
            bank_name = "中国建设银行"
        elif "农业银行" in text_str or "ABC" in text_upper:
            bank_name = "中国农业银行"
        elif "中国银行" in text_str or "BOC" in text_upper:
            bank_name = "中国银行"
        elif "招商银行" in text_str or "CMB" in text_upper:
            bank_name = "招商银行"
        elif "中信银行" in text_str or "CITIC" in text_upper:
            bank_name = "中信银行"
        elif "民生银行" in text_str or "CMBC" in text_upper:
            bank_name = "中国民生银行"
        elif "浦发银行" in text_str or "SPDB" in text_upper:
            bank_name = "上海浦东发展银行"
        elif "兴业银行" in text_str or "CIB" in text_upper:
            bank_name = "兴业银行"
        elif "平安银行" in text_str or "PAB" in text_upper:
            bank_name = "平安银行"
        elif "光大银行" in text_str or "CEB" in text_upper:
            bank_name = "中国光大银行"
        elif "华夏银行" in text_str or "HXB" in text_upper:
            bank_name = "华夏银行"
        elif "广发银行" in text_str or "GDB" in text_upper:
            bank_name = "广发银行"
        elif "交通银行" in text_str or "BOCOM" in text_upper:
            bank_name = "交通银行"
        elif "邮储银行" in text_str or "PSBC" in text_upper:
            bank_name = "中国邮政储蓄银行"
        # 国际品牌关键词覆盖
        elif "UNIONPAY" in text_upper or "UNION PAY" in text_upper:
            bank_name = "中国银联"
        elif "VISA" in text_upper:
            bank_name = "Visa"
        elif "MASTERCARD" in text_upper:
            bank_name = "MasterCard"
        elif "DISCOVER" in text_upper and bank_name == "未识别":
            bank_name = "Discover"

        # 如果仍未识别中文银行，但存在 UnionPay 且卡号以62开头，倾向标记为 农村信用社（若 BIN 匹配）或 中国银联
        if bank_name == "未识别" and ("UNIONPAY" in text_upper or "UNION PAY" in text_upper):
            if card_number.startswith('6217'):
                bank_name = "农村信用社"
            elif card_number.startswith('62'):
                bank_name = "中国银联"
        
        result = {
            "bank_name": bank_name,
            "card_number": card_number
        }
        
        logger.info(f"📌 银行卡提取结果: {result}")
        return result

# 创建全局实例
bankcard_ocr = BankCardOCR()

def recognize_bank_card(texts_with_boxes):
    """银行卡识别接口函数"""
    return bankcard_ocr.extract_bank_card_enhanced(texts_with_boxes)
