import os
import cv2
import numpy as np
from glob import glob


def adaptive_rain_removal(input_folder, output_folder, strength=0.3):
    """
    自适应去雨，根据图片情况调整处理强度
    """
    os.makedirs(output_folder, exist_ok=True)

    image_files = glob(os.path.join(input_folder, "*.*"))
    image_files = [f for f in image_files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]

    for img_path in image_files:
        try:
            img = cv2.imread(img_path)
            if img is None:
                continue

            filename = os.path.basename(img_path)
            print(f"处理: {filename}")

            # 分析图片亮度
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            avg_brightness = np.mean(gray)

            # 根据亮度调整参数
            if avg_brightness < 80:  # 暗图
                denoise_strength = 5
                contrast_strength = 1.3
                sharpen_strength = 0.1
            elif avg_brightness > 200:  # 过亮
                denoise_strength = 7
                contrast_strength = 1.1
                sharpen_strength = 0.05
            else:  # 正常亮度
                denoise_strength = 6
                contrast_strength = 1.2
                sharpen_strength = 0.08

            # 1. 自适应去噪
            denoised = cv2.fastNlMeansDenoisingColored(
                img, None,
                h=denoise_strength * strength,
                hColor=denoise_strength * strength,
                templateWindowSize=7,
                searchWindowSize=21
            )

            # 2. 自适应对比度增强
            lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)

            # 轻度CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)

            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

            # 3. 锐化（轻微）
            if sharpen_strength > 0:
                blurred = cv2.GaussianBlur(enhanced, (0, 0), 3)
                result = cv2.addWeighted(enhanced, 1 + sharpen_strength,
                                         blurred, -sharpen_strength, 0)
            else:
                result = enhanced

            output_path = os.path.join(output_folder, filename)
            cv2.imwrite(output_path, result)

        except Exception as e:
            print(f"错误: {e}")

    print(f"处理完成！保存到: {output_folder}")


# 使用（从小强度开始尝试）
INPUT = r"D:\ImgProcess\after"
OUTPUT = r"D:\ImgProcess\clean"
adaptive_rain_removal(INPUT, OUTPUT, strength=0.2)