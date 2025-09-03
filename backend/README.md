# OCR 服务

本项目提供了一个基于 Sanic 和 PaddleOCR 的光学字符识别（OCR）服务。服务通过 API 接受图像数据并返回识别结果。此项目使用 PaddleOCR 引擎，支持中文的文字识别，并支持 GPU 加速（可配置）。

## 功能

- 接收图像数据并进行 OCR 识别。
- 支持对图像的高效处理。
- 提供 JSON 格式的 OCR 结果输出。

## 环境依赖

- Python 3.7+
- PaddleOCR
- Sanic

## 安装

1. 克隆项目代码：

   git clone <仓库地址>
   cd <项目目录>

2. 安装依赖：

   pip install -r requirements.txt

## 配置

在 `app.py` 文件中，可以根据需要配置是否使用 GPU：

use_gpu = False  # 如果有 GPU 并且希望使用，将其设置为 True

## 运行

在项目目录下运行以下命令以启动服务：

python app.py

服务启动后，会监听 `0.0.0.0:8010` 端口。

## API 使用

### OCR 请求

- **URL**: `/ocr`
- **方法**: `POST`
- **请求体**: 

  请求体应为 JSON 格式，包含以下字段：
  
  {
    "img64": "<base64 编码的图像数据>"
  }

  示例：
  
  {
    "img64": "iVBORw0KGgoAAAANSUhEUgAAA..."
  }

- **响应**:

  成功时，返回 JSON 格式的识别结果：
  
  {
    "results": [
        [
            [[72.0, 13.0], [121.0, 13.0], [121.0, 39.0], [72.0, 39.0]],
            "文本",
            0.9985
        ]
    ]
  }

  如果未上传文件或处理失败，返回错误信息：

  {
    "error": "No file was uploaded."
  }

  或

  {
    "error": "OCR处理失败: 错误详情"
  }

## 日志

服务运行时会输出日志信息，包括 OCR 使用 GPU 的状态、图像解码信息和 OCR 识别结果。日志格式如下：

2024-08-12 12:00:00 - ocr_server - INFO - OCR_USE_GPU parameter is set to False
2024-08-12 12:00:01 - ocr_server - INFO - 图片解码成功，尺寸: (720, 1280, 3)
2024-08-12 12:00:02 - ocr_server - INFO - OCR识别结果: [...]

## 贡献

欢迎提交问题、功能请求或 PR 来帮助改进这个项目。

## 许可证

本项目采用 MIT 许可证。