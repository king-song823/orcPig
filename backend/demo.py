import cv2
import numpy as np
from paddleocr import PaddleOCR
import os

# 初始化 OCR 模型
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='ch',
    use_gpu=False,
    rec_image_shape="3, 32, 100",
    rec_batch_num=1,
    max_text_length=25,
    drop_score=0.05,
    det_db_thresh=0.1,
    det_db_box_thresh=0.2,
    det_db_unclip_ratio=2.0,
    use_tensorrt=False
)

def recognize_pig_ear_tag(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print("❌ 无法读取图像")
        return None

    # 转灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 高斯模糊 + Canny 边缘检测
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    edges = cv2.Canny(blurred, 50, 150)

    # 霍夫圆检测
    circles = cv2.HoughCircles(
        edges,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=100,
        param1=100,
        param2=30,
        minRadius=100,
        maxRadius=250
    )

    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            print(f"✅ 定位成功：圆心 ({x}, {y}), 半径 {r}")

            margin = int(r * 0.15)
            left = max(x - r - margin, 0)
            top = max(y - r - margin, 0)
            right = min(x + r + margin, image.shape[1])
            bottom = min(y + r + margin, image.shape[0])

            cropped = image[top:bottom, left:right]
            print(f"   裁剪区域: ({left},{top}) ~ ({right},{bottom})")

            # --- 图像预处理 ---
            gray_cropped = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

            # 1. 非局部均值去噪
            denoised = cv2.fastNlMeansDenoising(gray_cropped, h=10, templateWindowSize=7, searchWindowSize=21)

            # 2. 锐化增强
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            sharpened = cv2.filter2D(denoised, -1, kernel)

            # 3. 直方图均衡化
            equalized = cv2.equalizeHist(sharpened)

            # 4. 自适应二值化（保留灰字）
            binary_inv = cv2.adaptiveThreshold(equalized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

            # 5. 关键步骤：使用 Canny 边缘提取耳标轮廓
            canny_edges = cv2.Canny(equalized, 50, 150)
            kernel_morph = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            canny_closed = cv2.morphologyEx(canny_edges, cv2.MORPH_CLOSE, kernel_morph)

            # 6. 找轮廓并填充
            contours, _ = cv2.findContours(canny_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                mask = np.zeros_like(equalized)
                cv2.drawContours(mask, [largest_contour], -1, 255, thickness=cv2.FILLED)

                # 7. 在轮廓内做局部二值化
                masked_img = cv2.bitwise_and(equalized, mask)
                _, text_mask = cv2.threshold(masked_img, 80, 255, cv2.THRESH_BINARY)

                # 8. 形态学操作：先开后闭，修复文字
                # 开运算：去除毛刺
                text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_OPEN, kernel_morph, iterations=1)
                # 闭运算：连接断开的字符
                text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_CLOSE, kernel_morph, iterations=2)

                # 9. 放大图像
                resized = cv2.resize(text_mask, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

                # 【调试】保存中间结果
                cv2.imwrite("debug_denoised.png", denoised)
                cv2.imwrite("debug_equalized.png", equalized)
                cv2.imwrite("debug_binary_inv.png", binary_inv)
                cv2.imwrite("debug_canny_closed.png", canny_closed)
                cv2.imwrite("debug_mask.png", mask)
                cv2.imwrite("debug_text_mask.png", text_mask)
                cv2.imwrite("debug_resized.png", resized)
                print("✅ 已保存所有中间图像，请打开 debug_text_mask.png 查看效果")

                # --- OCR 识别 ---
                result = ocr.ocr(resized, rec=True)

                if result is None or result[0] is None:
                    print("❌ OCR 未检测到任何文本")
                    return None

                texts = []
                for line in result[0]:
                    text = line[1][0].strip()
                    score = line[1][1]
                    if score >= 0.05 and text.isdigit() and len(text) >= 6:
                        texts.append(text)
                        print(f"🔍 识别到数字: {text} (置信度: {score:.3f})")

                if len(texts) >= 2:
                    left_num = next((t for t in texts if len(t) == 7), "")
                    right_num = next((t for t in texts if len(t) == 8), "")
                    if left_num and right_num:
                        full_id = left_num + right_num
                        print(f"✅ 成功拼接: {full_id}")
                        return full_id

                combined = ''.join(sorted(set(texts), key=texts.index))
                if len(combined) >= 14:
                    print(f"✅ 合并识别结果: {combined}")
                    return combined

                print("❌ 未找到有效数字组合")
                return None

    else:
        print("❌ 未检测到圆形耳标")
        return None


if __name__ == "__main__":
    image_file = 'eartag.JPG'
    if not os.path.exists(image_file):
        print("❌ 图像文件不存在")
    else:
        result = recognize_pig_ear_tag(image_file)
        if result:
            print(f"\n🎉 最终识别结果: {result}")
        else:
            print("\n❌ 识别失败，请检查 debug_text_mask.png 是否有清晰文字")