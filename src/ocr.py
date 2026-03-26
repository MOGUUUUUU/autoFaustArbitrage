from paddleocr import PaddleOCR
import cv2
import numpy as np
import os

# 禁用模型下载检查，加速启动
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
# 禁用 OneDNN 以避免兼容性问题
os.environ['FLAGS_use_mkldnn'] = '0'

# 使用新版API
ocr = PaddleOCR(lang="ch")


def text_detection_only(image_path):
    """OCR识别并显示结果"""
    result = ocr.ocr(image_path, cls=False)

    # 可视化检测结果
    image = cv2.imread(image_path)

    if result is not None and len(result) > 0:
        for res in result:
            if res:
                print(f"检测到 {len(res)} 个文本区域:")
                for item in res:
                    box = item[0]
                    text = item[1][0]
                    confidence = item[1][1]
                    print(f"文本: {text} (置信度: {confidence:.2f})")
                    print(f"坐标: {box}")

                    # 绘制检测框（绿色）
                    pts = np.array(box, dtype=np.int32)
                    cv2.polylines(image, [pts], True, (0, 255, 0), 2)
                    # 绘制文本（红色） - box[0] 是左上角坐标
                    cv2.putText(image, text, (int(box[0][0]), int(box[0][1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    else:
        print("未检测到文本")

    # 显示结果
    cv2.imshow('Detection Result', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    img = "test.png"
    text_detection_only(img)