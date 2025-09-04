# app_enhanced.py - 增强版OCR识别系统

from sanic import Sanic, response
from sanic.request import Request
from paddleocr import PaddleOCR
import numpy as np
import cv2
import logging
import asyncio
import re
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# 初始化日志
logger = logging.getLogger("enhanced_ocr")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

# 初始化多个OCR引擎
logger.info("🔧 开始初始化OCR引擎...")
try:
    logger.info("🔧 初始化主OCR引擎...")
    primary_ocr = PaddleOCR(
        use_angle_cls=False,
        lang="ch",
        use_gpu=False,
        rec_batch_num=10,
        cpu_threads=6,
        use_mkldnn=True,
        det_limit_side_len=1280,
        drop_score=0.1,
        show_log=False
    )
    logger.info("✅ 主OCR引擎初始化成功")
    
    logger.info("🔧 初始化次OCR引擎...")
    secondary_ocr = PaddleOCR(
        use_angle_cls=False,
        lang="ch",
        use_gpu=False,
        rec_batch_num=10,
        cpu_threads=6,
        use_mkldnn=True,
        det_limit_side_len=960,
        drop_score=0.05,
        show_log=False
    )
    logger.info("✅ 次OCR引擎初始化成功")
    
    ocr_engines = {
        "primary": primary_ocr,
        "secondary": secondary_ocr
    }
    logger.info("✅ 所有OCR引擎初始化完成")
    
except Exception as e:
    logger.error(f"❌ OCR引擎初始化失败: {e}")
    raise

# 创建 Sanic 应用
app = Sanic("EnhancedOCRApp")

# 配置CORS
try:
    from sanic_cors import CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
except ImportError:
    logger.warning("sanic_cors not available, CORS not configured")
    # 回退方案：全局添加CORS响应头
    @app.middleware("response")
    async def add_cors_headers(request, resp):
        try:
            resp.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*") or "*"
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = request.headers.get(
                "Access-Control-Request-Headers", "Content-Type, Authorization"
            )
        except Exception:
            pass

# 线程池
executor = ThreadPoolExecutor(max_workers=4)

# 智能身份证检测函数
def detect_id_card_number(text):
    """智能检测身份证号码"""
    # 1. 直接查找18位数字
    if re.search(r'\b\d{18}\b', text):
        return True
    
    # 2. 查找包含18位数字的长字符串，但排除银行卡号
    long_numbers = re.findall(r'\d{15,}', text)
    for num in long_numbers:
        # 如果是19位数字，很可能是银行卡号，跳过
        if len(num) == 19:
            continue
        # 在长数字中查找18位身份证号码
        if len(num) >= 18:
            # 尝试从不同位置提取18位数字
            for i in range(len(num) - 17):
                candidate = num[i:i+18]
                if is_valid_id_card(candidate):
                    logger.info(f"🔍 在长数字 {num} 中找到身份证号码: {candidate}")
                    return True
    
    return False

def is_valid_id_card(id_number):
    """验证身份证号码格式"""
    if len(id_number) != 18:
        return False
    
    # 检查前17位是否为数字
    if not id_number[:17].isdigit():
        return False
    
    # 检查最后一位（可能是数字或X）
    if not (id_number[17].isdigit() or id_number[17] in ['X', 'x']):
        return False
    
    # 身份证校验码校验
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_map = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
    total = sum(int(id_number[i]) * weights[i] for i in range(17))
    check = check_map[total % 11]
    return check == id_number[17].upper()


def luhn_is_valid(number_str: str) -> bool:
    """Luhn 校验：用于银行卡号有效性判断"""
    if not number_str.isdigit():
        return False
    total = 0
    reverse_digits = number_str[::-1]
    for idx, ch in enumerate(reverse_digits):
        n = int(ch)
        if idx % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def find_luhn_cards_with_positions(texts_with_boxes):
    """从识别块中找出可能的银行卡号，返回 [(digits, center_x, center_y)]"""
    candidates = []
    for item in texts_with_boxes:
        text = item["text"]
        for m in re.finditer(r'(?:\d[\s-]?){16,19}', text):
            candidate_raw = m.group(0)
            digits = re.sub(r'[^0-9]', '', candidate_raw)
            if 16 <= len(digits) <= 19 and luhn_is_valid(digits):
                candidates.append((digits, item.get("center_x", 0.0), item.get("center_y", 0.0)))
    return candidates


def compute_keyword_proximity_score(texts_with_boxes, target_words):
    """根据文本块与关键词的邻近度给分，命中越近分越高"""
    keyword_positions = []
    for item in texts_with_boxes:
        t = item["text"].lower()
        if any(w.lower() in t for w in target_words):
            keyword_positions.append((item.get("center_x", 0.0), item.get("center_y", 0.0)))
    if not keyword_positions:
        return 0.0
    # 简单评分：有关键词就+1
    return 1.0

# 图像预处理函数
def preprocess_image(image_bytes):
    """图像预处理 - 身份证优化版，最小化预处理"""
    try:
        # 转换为numpy数组
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None
        
        # 对于身份证，使用最小化预处理策略
        # 只进行最基本的图像增强，避免破坏文字识别
        
        # 1. 轻微对比度增强（仅当图像过暗时）
        # 计算图像平均亮度
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        
        if mean_brightness < 100:  # 图像较暗时才增强
            img = cv2.convertScaleAbs(img, alpha=1.2, beta=10)
        
        # 2. 轻微去噪（仅当图像噪点较多时）
        # 这里暂时跳过去噪，因为可能影响文字识别
        
        # 3. 直接返回原图或轻微增强的图像
        return img
        
    except Exception as e:
        logger.error(f"图像预处理错误: {e}")
        return None

# 增强OCR函数
async def enhanced_ocr_image(image_bytes):
    """增强OCR识别"""
    try:
        # 预处理图像
        processed_img = preprocess_image(image_bytes)
        if processed_img is None:
            return []
        
        # 使用主引擎识别
        primary_results = await asyncio.get_event_loop().run_in_executor(
            executor, ocr_engines["primary"].ocr, processed_img
        )
        
        # 处理主引擎结果
        texts_with_boxes = []
        if primary_results and primary_results[0]:
            for line in primary_results[0]:
                if len(line) >= 2:
                    bbox = line[0]
                    text = line[1][0] if isinstance(line[1], (list, tuple)) else line[1]
                    confidence = line[1][1] if isinstance(line[1], (list, tuple)) and len(line[1]) > 1 else 0.0
                    
                    # 计算中心点
                    center_x = sum([point[0] for point in bbox]) / 4
                    center_y = sum([point[1] for point in bbox]) / 4
                    
                    texts_with_boxes.append({
                        "text": text,
                        "bbox": bbox,
                        "confidence": confidence,
                        "center_x": center_x,
                        "center_y": center_y
                    })
        
        # 如果主引擎结果不够好，使用次引擎
        if len(texts_with_boxes) < 3:
            secondary_results = await asyncio.get_event_loop().run_in_executor(
                executor, ocr_engines["secondary"].ocr, processed_img
            )
            
            if secondary_results and secondary_results[0]:
                for line in secondary_results[0]:
                    if len(line) >= 2:
                        bbox = line[0]
                        text = line[1][0] if isinstance(line[1], (list, tuple)) else line[1]
                        confidence = line[1][1] if isinstance(line[1], (list, tuple)) and len(line[1]) > 1 else 0.0
                        
                        # 计算中心点
                        center_x = sum([point[0] for point in bbox]) / 4
                        center_y = sum([point[1] for point in bbox]) / 4
                        
                        texts_with_boxes.append({
                            "text": text,
                            "bbox": bbox,
                            "confidence": confidence,
                            "center_x": center_x,
                            "center_y": center_y
                        })
        
        # 去重和合并结果
        unique_texts = {}
        for item in texts_with_boxes:
            text = item["text"]
            if text not in unique_texts or item["confidence"] > unique_texts[text]["confidence"]:
                unique_texts[text] = item
        
        results = list(unique_texts.values())
        logger.info(f"增强OCR识别到 {len(results)} 个文本块")
        return results
        
    except Exception as e:
        logger.error(f"增强OCR错误: {e}")
        return []

# 导入独立的识别模块
from eartag_ocr_module import recognize_pig_ear_tag
from idcard_ocr_module import recognize_id_card
from bankcard_ocr_module import recognize_bank_card
from screenshot_ocr_module import recognize_system_screenshot

# 处理预检请求
@app.options("/parse-docs")
async def options_parse_docs(request: Request):
    return response.text("", headers={
        "Access-Control-Allow-Origin": request.headers.get("Origin", "*") or "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": request.headers.get("Access-Control-Request-Headers", "Content-Type, Authorization"),
    })

# 主接口
@app.post("/parse-docs")
async def parse_docs(request: Request):
    if not request.files:
        return response.json({"error": "No files uploaded"}, status=400)

    files = request.files.getlist("files")
    if len(files) > 50:
        return response.json({"error": "最多上传 50 张图片"}, status=400)

    results = {
        "id_card": None,
        "bank_card": None,
        "system_screenshot": None,
        "pig_ear_tags": [],
        "debug_texts": []
    }

    for file in files:
        content = file.body
        logger.info(f"处理文件: {file.name}, 大小: {len(content)} bytes")

        # 执行OCR识别
        texts_with_boxes = await enhanced_ocr_image(content)
        
        if not texts_with_boxes:
            logger.warning(f"文件 {file.name} 未识别到文本")
            continue

        # 合并所有文本用于分类
        all_text = ' '.join([item["text"] for item in texts_with_boxes])
        text_str = all_text.lower()
        
        # 保存调试信息
        results["debug_texts"] = texts_with_boxes

        # 混合打分分类：同时考虑关键词、号码有效性
        id_kw = ["身份证", "公民身份号码", "姓名", "民族", "住址"]
        bank_kw = ["银行", "银行卡", "借记卡", "信用卡", "卡号", "农信", "信用社", "发卡行", "银行名称", "银联", "UNIONPAY", "VALID THRU", "CREDIT", "DEBIT"]
        ss_kw = ["保单号", "报案号", "系统"]
        eartag_kw = ["耳标", "猪耳标", "拍摄人", "查勘地点", "拍摄地点", "经纬度"]

        # 身份证分数
        id_score = 0.0
        if detect_id_card_number(all_text):
            id_score += 1.0
        id_score += compute_keyword_proximity_score(texts_with_boxes, id_kw)

        # 银行卡分数（提高权重）
        bank_score = 0.0
        luhn_cards = find_luhn_cards_with_positions(texts_with_boxes)
        if luhn_cards:
            bank_score += 2.0  # 银行卡号权重更高
        bank_score += compute_keyword_proximity_score(texts_with_boxes, bank_kw)

        # 系统截图分数
        ss_score = 0.0
        if re.search(r'\bP[0-9A-Z]{2,}N\d{2,}\b', all_text, re.I) or re.search(r'\bR[0-9A-Z]{2,}N\d{2,}\b', all_text, re.I):
            ss_score += 1.0
        ss_score += compute_keyword_proximity_score(texts_with_boxes, ss_kw)

        # 猪耳标分数（新增）- 大幅提高权重
        eartag_score = 0.0
        # 检测7位或8位数字（耳标特征）
        eartag_numbers = re.findall(r'\b\d{7,8}\b', all_text)
        if eartag_numbers:
            eartag_score += len(eartag_numbers) * 3.0  # 每个耳标数字加3.0分（进一步提高权重）
        eartag_score += compute_keyword_proximity_score(texts_with_boxes, eartag_kw)
        
        # 如果同时包含耳标数字和猪耳标关键词，额外加分
        if eartag_numbers and any(kw in all_text for kw in ["拍摄人", "查勘地点", "拍摄地点"]):
            eartag_score += 3.0  # 额外加分进一步提高
        
        # 特殊处理：如果包含"拍摄人"关键词，说明是猪耳标照片，大幅加分
        if "拍摄人" in all_text:
            eartag_score += 2.0  # 拍摄人是猪耳标的强特征

        logger.info(f"🧮 打分: 身份证={id_score:.1f}, 银行卡={bank_score:.1f}, 系统截图={ss_score:.1f}, 猪耳标={eartag_score:.1f}")

        # 选择分最高的类别；分数相等时按 身份证 > 银行卡 > 系统截图 > 猪耳标
        scores = [("id", id_score), ("bank", bank_score), ("ss", ss_score), ("eartag", eartag_score)]
        scores.sort(key=lambda x: x[1], reverse=True)

        chosen = scores[0][0] if scores and scores[0][1] > 0 else None
        if chosen == "id" and not results["id_card"]:
            logger.info("📌 打分最高 -> 身份证")
            results["id_card"] = recognize_id_card(texts_with_boxes)
        elif chosen == "bank" and not results["bank_card"]:
            logger.info("💳 打分最高 -> 银行卡")
            results["bank_card"] = recognize_bank_card(texts_with_boxes)
        elif chosen == "ss" and not results["system_screenshot"]:
            logger.info("📱 打分最高 -> 系统截图")
            results["system_screenshot"] = recognize_system_screenshot(texts_with_boxes)
        elif chosen == "eartag":
            logger.info("🐷 打分最高 -> 猪耳标")
            eartag_result = await asyncio.get_event_loop().run_in_executor(None, recognize_pig_ear_tag, content)
            if eartag_result.get("ear_tag_7digit") != "未识别" or eartag_result.get("ear_tag_8digit") != "未识别":
                results["pig_ear_tags"].append(eartag_result)
        else:
            logger.info("🐷 识别为猪耳标 (其他情况)")
            eartag_result = await asyncio.get_event_loop().run_in_executor(None, recognize_pig_ear_tag, content)
            if eartag_result.get("ear_tag_7digit") != "未识别" or eartag_result.get("ear_tag_8digit") != "未识别":
                results["pig_ear_tags"].append(eartag_result)

        # 按照用户逻辑：系统截图就是系统截图，不需要再识别猪耳标

    # 构建响应
    form_data = {
        # 身份证信息
        "name": results["id_card"].get("name", "未识别") if results["id_card"] else "未识别",
        "idNumber": results["id_card"].get("id_number", "未识别") if results["id_card"] else "未识别",
        # 银行卡信息
        "bankName": results["bank_card"].get("bank_name", "未识别") if results["bank_card"] else "未识别",
        "cardNumber": results["bank_card"].get("card_number", "未识别") if results["bank_card"] else "未识别",
        # 系统截图信息
        "policyNumber": results["system_screenshot"].get("policy_number", "未识别") if results["system_screenshot"] else "未识别",
        "claimNumber": results["system_screenshot"].get("claim_number", "未识别") if results["system_screenshot"] else "未识别",
        "insuredPerson": results["id_card"].get("name", "未识别") if results["id_card"] else "未识别",
        "insuranceSubject": results["system_screenshot"].get("insurance_subject", "未识别") if results["system_screenshot"] else "未识别",
        "coveragePeriod": results["system_screenshot"].get("coverage_period", "未识别") if results["system_screenshot"] else "未识别",
        "incidentDate": results["system_screenshot"].get("incident_date", "未识别") if results["system_screenshot"] else "未识别",
        "incidentLocation": results["system_screenshot"].get("incident_location", "未识别") if results["system_screenshot"] else "未识别",
        "reportTime": results["system_screenshot"].get("report_time", "未识别") if results["system_screenshot"] else "未识别",
        "inspectionTime": results["system_screenshot"].get("inspection_time", "未识别") if results["system_screenshot"] else "未识别",
        "inspectionMethod": results["system_screenshot"].get("inspection_method", "未识别") if results["system_screenshot"] else "未识别",
        "estimatedLoss": results["system_screenshot"].get("estimated_loss", "未识别") if results["system_screenshot"] else "未识别",
        "incidentCause": results["system_screenshot"].get("incident_cause", "未识别") if results["system_screenshot"] else "未识别",
        # 猪耳标信息
        "earTag7Digit": results["pig_ear_tags"][0].get("ear_tag_7digit", "未识别") if results["pig_ear_tags"] else "未识别",
        "earTag8Digit": results["pig_ear_tags"][0].get("ear_tag_8digit", "未识别") if results["pig_ear_tags"] else "未识别",
        "pigEarTags": results["pig_ear_tags"] if results["pig_ear_tags"] else [],
        # 调试信息
        "debug_ocr_texts": [item["text"] for item in results.get("debug_texts", [])],
    }

    return response.json(form_data)

# 启动服务
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8011, workers=1, debug=True)
