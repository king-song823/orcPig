# app.py - 支持多图上传 + 自动分类 + 猪耳标识别（v2.0）

from sanic import Sanic, response
from sanic.request import Request
from paddleocr import PaddleOCR
import numpy as np
import cv2
import logging
import asyncio
import re
from datetime import datetime, timedelta

# 初始化日志
logger = logging.getLogger("insurance_ocr")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

# 初始化 OCR 引擎（使用原始图，不预处理）
ocr_engine = PaddleOCR(
    use_angle_cls=True,
    lang="ch",
    use_gpu=False,
    det_limit_side_len=1280,      # 提高小字检测能力
    drop_score=0.1,               # 降低识别阈值
    show_log=False
)

# 创建 Sanic 应用
app = Sanic("InsuranceFormApp")

# CORS 响应头
@app.middleware("response")
async def cors_headers(request, resp):
    resp.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

# OPTIONS 预检
@app.options("/parse-docs")
async def options_handler(request: Request):
    return response.empty(
        status=204,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )


# OCR 识别函数（正确解析 result 结构）
def ocr_image(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return []
    try:
        # ✅ 直接使用原始图像（不要增强！否则可能破坏小字）
        result = ocr_engine.ocr(img)
        texts_with_boxes = []

        # ✅ 正确解析 PaddleOCR 三层结构: [ [ [box, (text, score)], ... ] ]
        if result and isinstance(result, list):
            for page_result in result:
                if not page_result:
                    continue
                for item in page_result:
                    if not isinstance(item, (list, tuple)) or len(item) < 2:
                        continue
                    box = item[0]
                    text = str(item[1][0]).strip()
                    score = item[1][1]

                    if not text:
                        continue

                    # 提取位置信息
                    x_coords = [pt[0] for pt in box]
                    y_coords = [pt[1] for pt in box]
                    center_x = sum(x_coords) / 4
                    center_y = sum(y_coords) / 4
                    width = max(x_coords) - min(x_coords)
                    height = max(y_coords) - min(y_coords)

                    texts_with_boxes.append({
                        "text": text,
                        "score": score,
                        "box": box,
                        "center_x": center_x,
                        "center_y": center_y,
                        "width": width,
                        "height": height
                    })

        # logger.info(f"✅ OCR 识别到 {len(texts_with_boxes)} 个文本块: {[b['text'] for b in texts_with_boxes]}")
        return texts_with_boxes

    except Exception as e:
        logger.error(f"OCR error: {e}")
        return []


# 提取身份证
def extract_id_card(texts):
    name = None
    id_number = None
    cleaned_lines = [re.sub(r'\s+', '', line.strip()) for line in texts if line.strip()]
    all_text = ''.join(cleaned_lines)

    for line in cleaned_lines:
        if name:
            break
        if '姓名' in line or '名字' in line:
            match = re.search(r'(?:姓名|名字)[^\u4e00-\u9fa5]*([\u4e00-\u9fa5]{2,4})', line)
            if match:
                name = match.group(1)
                logger.debug(f"✅ 提取姓名: {name}")
                break

    keywords = ['公民身份号码', '身份证号', '身份证号码']
    for i, line in enumerate(cleaned_lines):
        if id_number:
            break
        if any(kw in line for kw in keywords):
            for j in range(i + 1, min(i + 4, len(cleaned_lines))):
                digits = ''.join(filter(str.isdigit, cleaned_lines[j]))
                if len(digits) >= 18:
                    id_number = digits[-18:]
                    logger.debug(f"✅ 从第 {j} 行提取身份证号: {id_number}")
                    break

    if not id_number:
        candidates = re.findall(r'\b\d{17}[\dXx]\b', all_text, re.I)
        if candidates:
            id_number = candidates[-1].upper()

    result = {"name": name, "id_number": id_number}
    logger.info(f"📌 身份证提取结果: {result}")
    return result


# 银行卡 BIN 映射表
BIN_MAP = [
    (["621779", "623141", "622179"], "贵州农信"),
    (["621027", "622127", "623127"], "云南农信"),
    (["621737", "622137", "623137"], "四川农信"),
    (["622848", "622841"], "农业银行"),
    (["621088", "622188", "625188"], "邮政储蓄"),
    (["621288", "622288", "601388"], "建设银行"),
    (["621799", "622208", "620522"], "工商银行"),
    (["621661", "622260", "620522"], "交通银行"),
    (["621485", "622588", "620527"], "招商银行"),
]

def guess_bank_by_bin(card_number):
    if not card_number or len(card_number) < 6:
        return None
    bin_code = card_number[:6]
    for prefixes, bank_name in BIN_MAP:
        if any(bin_code.startswith(p[:6]) for p in prefixes):
            return bank_name
    return None

# 提取银行卡
def extract_bank_card(texts):
    bank_name = None
    card_number = None
    texts = [str(t).strip() for t in texts if t]

    noise_keywords = ['ATM', 'Union', '银联', 'GZRC', '通', '银用', 'Card', 'Logo', '客服', '热线']
    bank_keywords = ['银行', '农信', '信用社', '商行', '储蓄卡', '借记卡', '信用卡']

    for text in texts:
        if any(noise in text for noise in noise_keywords):
            continue
        if any(kw in text for kw in bank_keywords):
            bank_name = text
            break

    if not bank_name:
        for text in texts:
            if '农信' in text or '信用社' in text:
                bank_name = text
                break

    candidates = []
    for text in texts:
        cleaned = re.sub(r'\D', '', text)
        if 16 <= len(cleaned) <= 19 and cleaned.startswith(('62', '4', '5', '37')):
            candidates.append(cleaned)
    card_number = max(candidates, key=len) if candidates else None

    if not bank_name and card_number:
        guessed_bank = guess_bank_by_bin(card_number)
        if guessed_bank:
            bank_name = guessed_bank
            logger.info(f"🔍 通过卡号反推银行: {bank_name}")

    return {"bank_name": bank_name, "card_number": card_number}


# 提取系统截图
def extract_system_screenshot(texts):
    if not texts or not isinstance(texts, (list, tuple)):
        return {}

    full_text = "\n".join([str(t).strip() for t in texts if t and str(t).strip()])
    result = {
        "policy_number": "", "claim_number": "", "insured_name": "", "insurance_subject": [],
        "coverage_period": "", "incident_date": "", "incident_location": "",
        "report_time": "", "inspection_time": "", "inspection_method": "现场查勘",
        "estimated_loss": "", "incident_cause": ""
    }

    def extract_by_pattern(pattern, text, flags=re.IGNORECASE):
        match = re.search(pattern, text, flags)
        return match.group(1).strip() if match else ""

    def parse_date_str(date_str):
        date_str = re.sub(r'[年月]', '-', date_str).replace('日', '').strip()
        for fmt in ["%Y-%m-%d", "%Y-%m", "%Y/%m/%d"]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    result["policy_number"] = extract_by_pattern(r'(?:保单号|保单号码)[：:\s]*([A-Z0-9]{8,})', full_text)
    result["claim_number"] = extract_by_pattern(r'(?:报案号|案件号)[：:\s]*([A-Z0-9]{8,})', full_text)
    result["insured_name"] = extract_by_pattern(r'被保险人[：:\s]*([^\s，。；\n]+)', full_text)

    product_name = extract_by_pattern(r'险种名称[：:\s]*([^\n]+)', full_text)
    subjects = []
    if '育肥猪' in product_name: subjects.append("育肥猪")
    if '能繁母猪' in product_name: subjects.append("能繁母猪")
    if '香猪' in product_name: subjects.append("香 猪")
    if '仔猪' in product_name: subjects.append("仔猪")
    result["insurance_subject"] = subjects

    start_match = re.search(r'起保日期[：:\s]*(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?)', full_text)
    end_match = re.search(r'终保日期[：:\s]*(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?)', full_text)
    start_date = parse_date_str(start_match.group(1)) if start_match else None
    end_date = parse_date_str(end_match.group(1)) if end_match else None
    if start_date and end_date:
        result["coverage_period"] = f"{start_date.strftime('%Y年%m月%d日')} — {end_date.strftime('%Y年%m月%d日')}"

    incident_raw = extract_by_pattern(r'出险日期[：:\s]*([^\n，。]+)', full_text)
    incident_date = parse_date_str(incident_raw)
    if incident_date:
        result["incident_date"] = incident_date.strftime('%Y年%m月%d日')

    location_match = re.search(r'出险地点[：:\s]*([^\n，。]+?(?:乡|镇|村|组|屯|县|市|区|街道|农场|基地))', full_text)
    if location_match:
        result["incident_location"] = location_match.group(1).strip()

    report_raw = extract_by_pattern(r'报案日期[：:\s]*([^\n]+)', full_text)
    report_date = parse_date_str(report_raw)
    if report_date:
        result["report_time"] = report_date.strftime('%Y年%m月%d日')

    inspection_raw = extract_by_pattern(r'立案日期[：:\s]*([^\n]+)', full_text)
    inspection_date = parse_date_str(inspection_raw)
    if not inspection_date and result["incident_date"]:
        try:
            base_date = datetime.strptime(result["incident_date"], "%Y年%m月%d日")
            inspection_date = base_date + timedelta(days=1)
        except ValueError:
            pass
    if inspection_date:
        result["inspection_time"] = inspection_date.strftime('%Y年%m月%d日')

    claim_match = re.search(r'(?:估计赔款|估损金额|损失金额)[：:\s]*([0-9,]+\.\d{2})', full_text)
    if claim_match:
        result["estimated_loss"] = claim_match.group(1).replace(',', '')

    result["incident_cause"] = extract_by_pattern(r'出险原因[：:\s]*([^\n，。]+)', full_text)

    logger.info(f"✅ 系统截图提取结果: {result}")
    return result


# 猪耳标解析
def parse_pig_eartag_number(full_number):
    if not re.fullmatch(r'\d{15}', full_number):
        return None
    species_code = full_number[0]
    region_code = full_number[1:7]
    serial_number = full_number[7:]

    species_map = {"1": "猪", "2": "牛", "3": "羊"}
    region_map = {
        "522624": "贵州省·黔东南州·台江县",
        "522635": "贵州省·黔东南州·剑河县",
        "522601": "贵州省·凯里市",
    }

    return {
        "raw": full_number,
        "species": species_map.get(species_code, "未知"),
        "region_code": region_code,
        "region": region_map.get(region_code, f"贵州省·未知地区（{region_code}）"),
        "serial": serial_number,
        "valid": True
    }

# 提取耳标候选号码（跳过水印）
def extract_pig_eartag_candidates(texts_with_boxes, min_length=6):
    digit_blocks = []
    for block in texts_with_boxes:
        text = block["text"]
        # 跳过明显水印
        if any(kw in text for kw in ["时间", "拍摄", "相机", "客服", "热线", "Logo", "Union", "GZRC", "银联"]):
            continue
        # 保留含数字的文本块
        if re.search(r'\d', text):
            digit_blocks.append(block)

    if not digit_blocks:
        return []

    # === 第一策略：按 Y 坐标分组合并（同一行）===
    rows = {}
    for b in digit_blocks:
        found = False
        for y_key in rows:
            if abs(b["center_y"] - y_key) < 40:  # 容差放宽
                rows[y_key].append(b)
                found = True
                break
        if not found:
            rows[b["center_y"]] = [b]

    candidates = []
    for blocks in rows.values():
        sorted_blocks = sorted(blocks, key=lambda b: b["center_x"])
        merged = ''.join(re.sub(r'\D', '', b["text"]) for b in sorted_blocks)
        if len(merged) >= 8:
            candidates.append(merged)

    # === 第二策略：兜底 —— 所有数字块按 X 排序拼接 ===
    all_sorted = sorted(digit_blocks, key=lambda b: b["center_x"])
    full_merged = ''.join(re.sub(r'\D', '', b["text"]) for b in all_sorted)
    if len(full_merged) >= 12:
        candidates.append(full_merged)

    # 去重 + 按长度排序
    unique_candidates = list(set(candidates))
    unique_candidates.sort(key=len, reverse=True)
    return unique_candidates


# 批量解析接口
@app.post("/parse-docs")
async def parse_docs(request: Request):
    if not request.files:
        return response.json({"error": "No files uploaded"}, status=400)

    files = request.files.getlist("files")
    if len(files) > 20:
        return response.json({"error": "最多上传 20 张图片"}, status=400)

    results = {
        "id_card": None,
        "bank_card": None,
        "system_screenshot": None,
        "pig_eartags": []
    }
    loop = asyncio.get_event_loop()

    for file in files:
        content = file.body
        texts_with_boxes = await loop.run_in_executor(None, ocr_image, content)
        texts = [b["text"] for b in texts_with_boxes]

        if not texts:
            continue

        text_str = "\n".join(texts).upper()

        # 自动分类
        if not results["id_card"] and any(k in text_str for k in ["身份证", "姓名"]):
            results["id_card"] = extract_id_card(texts)
        elif not results["bank_card"] and any(k in text_str for k in ["银行", "卡号", "农信", "信用社"]):
            results["bank_card"] = extract_bank_card(texts)
        elif not results["system_screenshot"] and any(k in text_str for k in ["保单号", "报案号", "系统"]):
            results["system_screenshot"] = extract_system_screenshot(texts)
        else:
            logger.info(f"🐷 处理猪耳标图: {file.name}")
        logger.info(f"📝 OCR结果: {[b['text'] for b in texts_with_boxes]}")

        candidates = extract_pig_eartag_candidates(texts_with_boxes)
        logger.info(f"候选号码: {candidates}")

        found = False
        for raw in candidates:
            raw_clean = re.sub(r'\D', '', raw)
            if not raw_clean:
                continue

            # 补全逻辑
            if len(raw_clean) == 14 and raw_clean.startswith("522624"):
                raw_clean = "1" + raw_clean
            elif len(raw_clean) == 15 and raw_clean[1:].startswith("522624"):
                pass  # 正常
            else:
                continue

            if len(raw_clean) != 15 or not raw_clean.isdigit():
                continue

            parsed = parse_pig_eartag_number(raw_clean)
            if parsed:
                exists = any(t["raw"] == raw_clean for t in results["pig_eartags"])
                if not exists:
                    results["pig_eartags"].append(parsed)
                    logger.info(f"📌 成功添加耳标: {raw_clean}")
                    found = True
        if not found:
            logger.warning(f"❌ 未识别出耳标: {file.name}")

    # 构造返回数据
    form_data = {
        "idNumber": results["id_card"]["id_number"] if results["id_card"] else "未识别",
        "insuredPerson": results["id_card"]["name"] if results["id_card"] else "未识别",
        "bankName": results["bank_card"]["bank_name"] if results["bank_card"] else "未识别",
        "cardNumber": results["bank_card"]["card_number"] if results["bank_card"] else "未识别",
        "policyNumber": results["system_screenshot"].get("policy_number", "未识别") if results["system_screenshot"] else "未识别",
        "claimNumber": results["system_screenshot"].get("claim_number", "未识别") if results["system_screenshot"] else "未识别",
        "incidentLocation": results["system_screenshot"].get("incident_location", "") if results["system_screenshot"] else "",
        "incidentCause": results["system_screenshot"].get("incident_cause", "") if results["system_screenshot"] else "",
        "insuredName": results["system_screenshot"].get("insured_name", "") if results["system_screenshot"] else "",
        "insuranceSubject": results["system_screenshot"].get("insurance_subject", []) if results["system_screenshot"] else [],
        "coveragePeriod": results["system_screenshot"].get("coverage_period", "") if results["system_screenshot"] else "",
        "reportTime": results["system_screenshot"].get("report_time", "") if results["system_screenshot"] else "",
        "inspectionTime": results["system_screenshot"].get("inspection_time", "") if results["system_screenshot"] else "",
        "inspectionMethod": results["system_screenshot"].get("inspection_method", "现场查勘") if results["system_screenshot"] else "现场查勘",
        "estimatedLoss": results["system_screenshot"].get("estimated_loss", "") if results["system_screenshot"] else "",
        "pigEartags": results["pig_eartags"]
    }

    return response.json(form_data)


# 启动服务
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8010, workers=1, debug=True)