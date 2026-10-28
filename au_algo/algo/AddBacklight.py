import cv2
import numpy as np
import os
import glob


class BacklightEffectCreator:
    def __init__(self):
        self.default_light_source = (0.3, 0.2)  # 默认光源位置（相对坐标）
        self.backlight_strength = 0.4  # 逆光强度

    def load_image(self, path):
        img = cv2.imread(path)
        if img is None:
            return None
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def save_image(self, img, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

    def create_backlight_effect(self, img, light_position=None, strength=0.4,
                                halo_radius=0.7, contrast_reduction=0.8):
        """
        创建逆光效果

        参数:
        - light_position: 光源位置 (x, y) 0-1之间
        - strength: 逆光强度 0-1
        - halo_radius: 光晕半径
        - contrast_reduction: 对比度降低程度
        """
        h, w = img.shape[:2]

        if light_position is None:
            light_position = self.default_light_source

        # 创建亮度渐变图
        lx, ly = int(light_position[0] * w), int(light_position[1] * h)

        # 生成径向渐变掩码
        y_coords, x_coords = np.indices((h, w))
        distance = np.sqrt((x_coords - lx) ** 2 + (y_coords - ly) ** 2)
        max_dist = np.sqrt(w ** 2 + h ** 2) * halo_radius
        gradient = 1.0 - np.clip(distance / max_dist, 0, 1)

        # 增加光晕效果
        gradient = np.power(gradient, 0.7)  # 更自然的光晕衰减

        # 应用光晕
        img_float = img.astype(np.float32) / 255.0

        # 创建光晕颜色（温暖的阳光色）
        halo_color = np.array([1.1, 1.0, 0.85])  # 轻微偏暖

        # 应用逆光效果
        for c in range(3):
            img_float[:, :, c] = img_float[:, :, c] + gradient * strength * halo_color[c]

        img_float = np.clip(img_float, 0, 1)

        # 降低主体区域的对比度（模拟逆光下的阴影效果）
        mask_inverse = 1.0 - gradient * 0.7
        img_float = img_float * 0.8 + 0.2 * img_float * mask_inverse[:, :, np.newaxis]

        # 降低整体对比度
        img_float = img_float * contrast_reduction + 0.1 * (1 - contrast_reduction)

        # 添加轻微的模糊效果
        gradient_mask_3d = np.repeat(gradient[:, :, np.newaxis], 3, axis=2)
        blurred = cv2.GaussianBlur(img_float, (5, 5), 2)
        img_float = img_float * (1 - gradient_mask_3d * 0.3) + blurred * gradient_mask_3d * 0.3

        result = np.clip(img_float * 255, 0, 255).astype(np.uint8)

        return result

    def enhance_backlight_details(self, img, backlight_img):
        """
        增强逆光图片的细节
        """
        # 将图片转为HSV空间
        hsv = cv2.cvtColor(backlight_img, cv2.COLOR_RGB2HSV)
        h, s, v = cv2.split(hsv)

        # 提高阴影区域的亮度
        v_float = v.astype(np.float32)
        v_float = np.power(v_float / 255.0, 0.9) * 255.0

        # 增强饱和度
        s_float = s.astype(np.float32) * 1.1
        s_float = np.clip(s_float, 0, 255)

        # 合并
        hsv_enhanced = cv2.merge((h, s_float.astype(np.uint8), v_float.astype(np.uint8)))
        result = cv2.cvtColor(hsv_enhanced, cv2.COLOR_HSV2RGB)

        return result

    def process_image(self, img_path, output_path=None, strength=0.4):
        """
        处理单张图片
        """
        img = self.load_image(img_path)
        if img is None:
            print(f"无法加载图片: {img_path}")
            return None

        # 创建逆光效果
        backlight_img = self.create_backlight_effect(img, strength=strength)

        # 增强细节
        result = self.enhance_backlight_details(img, backlight_img)

        if output_path:
            self.save_image(result, output_path)

        return result


def batch_add_backlight(input_dir, output_dir, strength=0.4):
    """
    批量添加逆光效果
    """
    creator = BacklightEffectCreator()

    # 支持的文件格式
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']

    os.makedirs(output_dir, exist_ok=True)

    all_files = []
    for ext in extensions:
        all_files.extend(glob.glob(os.path.join(input_dir, f"**/{ext}"), recursive=True))

    print(f"找到 {len(all_files)} 张图片")

    for i, img_path in enumerate(all_files, 1):
        filename = os.path.basename(img_path)
        name, ext = os.path.splitext(filename)

        print(f"处理 [{i}/{len(all_files)}]: {filename}")

        output_filename = f"{name}_backlight{ext}"
        output_path = os.path.join(output_dir, output_filename)

        # 处理并保存
        result = creator.process_image(img_path, output_path, strength=strength)

        if result is not None:
            print(f"  ✓ 已保存: {output_filename}")
        else:
            print(f"  ✗ 处理失败: {filename}")


# 使用示例
if __name__ == "__main__":
    # 单个图片处理示例
    creator = BacklightEffectCreator()

    # 1. 处理单张图片
    result = creator.process_image(
        "input.jpg",
        "output_backlight.jpg",
        strength=0.4  # 可调整强度
    )

    # 2. 批量处理示例
    input_folder = r"D:\ImgProcess\before"
    output_folder = r"D:\ImgProcess\clean"

    # 批量处理（强度范围：0.3-0.6 比较自然）
    batch_add_backlight(input_folder, output_folder, strength=0.4)