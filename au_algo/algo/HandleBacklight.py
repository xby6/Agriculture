import cv2
import numpy as np
import os
import glob
import time


class CleanExposureCorrector:
    """
    干净型曝光校正器
    目标：逆光清晰、不过曝、不产生脏点
    """

    def __init__(self):
        self.min_brightness = 60
        self.max_brightness = 200

    # ----------------------------
    # 基础IO
    # ----------------------------
    def load_image(self, path):
        img = cv2.imread(path)
        if img is None:
            return None
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def save_image(self, img, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

    # ----------------------------
    # 曝光分析
    # ----------------------------
    def analyze_exposure(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        mean = np.mean(gray)
        dark_ratio = np.mean(gray < self.min_brightness)
        bright_ratio = np.mean(gray > self.max_brightness)

        if dark_ratio > 0.35 and bright_ratio > 0.15:
            t = "backlight"
        elif bright_ratio > 0.3:
            t = "overexposed"
        elif mean < 90:
            t = "underexposed"
        else:
            t = "normal"

        return {
            "type": t,
            "mean": float(mean),
            "dark_ratio": float(dark_ratio),
            "bright_ratio": float(bright_ratio)
        }

    # ----------------------------
    # 核心算法
    # ----------------------------
    def adjust_gamma(self, img, gamma):
        inv = 1.0 / gamma
        table = np.array([(i / 255.0) ** inv * 255 for i in range(256)]).astype("uint8")
        return cv2.LUT(img, table)

    def clahe_luminance(self, img):
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l2 = clahe.apply(l)
        lab = cv2.merge((l2, a, b))
        return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    def compress_highlights(self, img, strength=1.1):
        f = img.astype(np.float32) / 255.0
        f = f ** strength
        return np.clip(f * 255, 0, 255).astype(np.uint8)

    def enhance_saturation(self, img, factor=1.05):
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        h, s, v = cv2.split(hsv)
        s = np.clip(s.astype(np.float32) * factor, 0, 255).astype(np.uint8)
        hsv = cv2.merge((h, s, v))
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    # ----------------------------
    # 各曝光类型处理
    # ----------------------------
    def process_backlight(self, img):
        img = self.adjust_gamma(img, 0.85)
        img = self.clahe_luminance(img)
        img = self.compress_highlights(img, 1.12)
        img = self.enhance_saturation(img, 1.05)
        return img

    def process_overexposed(self, img):
        img = self.adjust_gamma(img, 1.2)
        img = self.compress_highlights(img, 1.15)
        img = self.clahe_luminance(img)
        return img

    def process_underexposed(self, img):
        img = self.adjust_gamma(img, 0.75)
        img = self.clahe_luminance(img)
        img = self.enhance_saturation(img, 1.08)
        return img

    def process_normal(self, img):
        img = self.adjust_gamma(img, 0.95)
        img = self.clahe_luminance(img)
        return img

    # ----------------------------
    # 主处理接口
    # ----------------------------
    def process_image(self, path):
        img = self.load_image(path)
        if img is None:
            return None

        info = self.analyze_exposure(img)
        t = info["type"]

        if t == "backlight":
            out = self.process_backlight(img)
        elif t == "overexposed":
            out = self.process_overexposed(img)
        elif t == "underexposed":
            out = self.process_underexposed(img)
        else:
            out = self.process_normal(img)

        return out, info


# ==============================
# 批量处理
# ==============================
class BatchProcessor:
    def __init__(self):
        self.corrector = CleanExposureCorrector()

    def find_images(self, folder):
        exts = ["*.jpg", "*.jpeg", "*.png", "*.bmp"]
        imgs = []
        for e in exts:
            imgs += glob.glob(os.path.join(folder, "**", e), recursive=True)
        return sorted(set(imgs))

    def run(self, input_dir, output_dir):
        imgs = self.find_images(input_dir)
        print(f"找到 {len(imgs)} 张图片")

        start = time.time()
        ok = 0

        for i, p in enumerate(imgs, 1):
            name = os.path.basename(p)
            print(f"[{i}/{len(imgs)}] {name}")

            out, info = self.corrector.process_image(p)
            if out is None:
                print("  ✗ 失败")
                continue

            save_name = os.path.splitext(name)[0] + "_fixed.jpg"
            save_path = os.path.join(output_dir, save_name)

            self.corrector.save_image(out, save_path)
            ok += 1
            print(f"  ✓ {info['type']}")

        print("-" * 40)
        print(f"完成 {ok}/{len(imgs)}")
        print(f"耗时 {time.time() - start:.1f}s")


def main():
    INPUT = r"D:\ImgProcess\before"
    OUTPUT = r"D:\ImgProcess\after"

    os.makedirs(OUTPUT, exist_ok=True)

    BatchProcessor().run(INPUT, OUTPUT)


if __name__ == "__main__":
    main()
