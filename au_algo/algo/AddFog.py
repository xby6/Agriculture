import cv2
import numpy as np
import os
from tqdm import tqdm
from scipy.ndimage import gaussian_filter
from typing import Optional, Tuple, Union


def generate_depth_map(height: int,
                       width: int,
                       depth_type: str = "linear",
                       horizon_position: float = 0.3) -> np.ndarray:
    """
    参数：
        depth_type:
            - "linear": 线性渐变
            - "quadratic": 二次渐变
            - "fog_atmospheric": 大气透视（远处更模糊）
            - "custom": 自定义深度
        horizon_position: 地平线位置 (0~1)
    """
    if depth_type == "linear":
        # 线性深度：从下往上渐变
        depth = np.linspace(1.0, 0.0, height).reshape(height, 1)
        depth = np.repeat(depth, width, axis=1)

    elif depth_type == "quadratic":
        # 二次渐变：更自然的深度过渡
        y = np.linspace(0, 1, height)
        depth = 1.0 - y ** 2
        depth = depth.reshape(height, 1)
        depth = np.repeat(depth, width, axis=1)

    elif depth_type == "fog_atmospheric":
        # 大气透视：模拟真实大气效果
        y_coords = np.linspace(0, 1, height)
        x_coords = np.linspace(-0.5, 0.5, width)
        y_grid, x_grid = np.meshgrid(y_coords, x_coords, indexing='ij')

        # 中心更清晰，边缘更模糊
        center_dist = np.sqrt((x_grid - 0.5) ** 2 + (y_grid - horizon_position) ** 2)
        depth = 1.0 - np.exp(-center_dist * 2)
        depth = 1.0 - depth  # 反转

    elif depth_type == "custom":
        # 自定义：添加随机扰动
        depth = np.linspace(1.0, 0.0, height).reshape(height, 1)
        depth = np.repeat(depth, width, axis=1)

        # 添加轻微随机扰动
        noise = np.random.normal(0, 0.05, (height, width))
        depth = np.clip(depth + noise, 0, 1)
        depth = gaussian_filter(depth, sigma=2.0)

    else:
        depth = np.ones((height, width)) * 0.5

    return depth


def get_fog_color_atmosphere(time_of_day: str = "day",
                             weather: str = "clear") -> Tuple[int, int, int]:
    """
    根据时间和天气获取雾的颜色
    """
    fog_colors = {
        "day_clear": (220, 220, 220),  # 白天晴朗
        "day_hazy": (210, 210, 200),  # 白天阴霾
        "day_foggy": (200, 200, 190),  # 白天雾天
        "morning": (240, 220, 180),  # 早晨（偏黄）
        "evening": (255, 200, 150),  # 傍晚（偏橙）
        "night": (180, 180, 200),  # 夜晚（偏蓝）
        "smog": (180, 170, 160),  # 雾霾
        "mist": (230, 230, 240),  # 薄雾
    }

    key = f"{time_of_day}_{weather}" if f"{time_of_day}_{weather}" in fog_colors else "day_clear"
    return fog_colors.get(f"{time_of_day}_{weather}", fog_colors[key])


def add_realistic_fog_effect(image: np.ndarray,
                             fog_intensity: float = 0.6,
                             depth_map: Optional[np.ndarray] = None,
                             fog_color: Optional[Tuple[int, int, int]] = None,
                             time_of_day: str = "day",
                             weather: str = "clear",
                             depth_type: str = "quadratic",
                             apply_blur: bool = True,
                             add_noise: bool = True,
                             light_scattering: float = 0.3) -> np.ndarray:
    """
    参数：
        fog_intensity: 0~1，雾的浓度
        depth_map: 自定义深度图，如果不提供则自动生成
        fog_color: 雾的颜色 (B, G, R)，如果不提供则根据时间和天气自动生成
        time_of_day: 时间段 (day, morning, evening, night)
        weather: 天气类型 (clear, hazy, foggy, smog, mist)
        depth_type: 深度图类型
        apply_blur: 是否应用模糊
        add_noise: 是否添加噪声模拟大气扰动
        light_scattering: 光线散射强度
    """
    h, w = image.shape[:2]

    # 1. 生成深度图
    if depth_map is None:
        depth_map = generate_depth_map(h, w, depth_type)

    # 应用雾浓度
    depth_map = depth_map * fog_intensity
    depth_map = np.clip(depth_map, 0, 1)

    # 2. 获取雾的颜色
    if fog_color is None:
        fog_color_bgr = get_fog_color_atmosphere(time_of_day, weather)
    else:
        fog_color_bgr = fog_color

    # 转换颜色格式用于计算
    fog_color_np = np.array(fog_color_bgr, dtype=np.float32)

    # 3. 基础雾效：I = J * (1 - t) + A * t
    img_float = image.astype(np.float32)
    fogged = img_float * (1 - depth_map[..., None]) + fog_color_np * depth_map[..., None]

    # 4. 光线散射效果（模拟大气散射）
    if light_scattering > 0:
        # 计算亮度图
        brightness = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0

        # 光线散射：亮部区域雾更明显
        scattering_mask = np.clip(brightness * light_scattering, 0, 0.5)
        scattering_factor = scattering_mask[..., None] * depth_map[..., None]

        fogged = fogged + (fog_color_np - fogged) * scattering_factor

    # 5. 添加大气噪声（模拟空气中的微颗粒）
    if add_noise:
        noise_intensity = fog_intensity * 0.1
        noise = np.random.normal(0, noise_intensity * 10, fogged.shape)
        fogged = np.clip(fogged + noise, 0, 255)

    # 转换为uint8
    fogged = np.clip(fogged, 0, 255).astype(np.uint8)

    # 6. 应用模糊（距离相关模糊）
    if apply_blur:
        # 根据深度调整模糊程度
        blur_kernel_base = int(3 + fog_intensity * 5)
        blur_kernel = blur_kernel_base if blur_kernel_base % 2 == 1 else blur_kernel_base + 1

        # 可选项：使用双边滤波保留边缘
        # fogged = cv2.bilateralFilter(fogged, 5, 75, 75)

        fogged = cv2.GaussianBlur(fogged, (blur_kernel, blur_kernel), 0)

    # 7. 对比度降低（雾中对比度降低）
    contrast_reduction = 1.0 - fog_intensity * 0.3
    fogged = cv2.addWeighted(fogged, contrast_reduction,
                             np.zeros_like(fogged), 0, 0)

    return fogged


def batch_add_fog_enhanced(input_folder: str,
                           output_folder: str,
                           fog_intensity: float = 0.6,
                           time_of_day: str = "day",
                           weather: str = "clear",
                           depth_type: str = "quadratic",
                           add_noise: bool = True,
                           allowed_extensions: tuple = ("jpg", "jpeg", "png", "bmp", "tiff")):
    """
    批量处理增强版
    """
    os.makedirs(output_folder, exist_ok=True)

    # 获取图片文件
    image_files = [
        f for f in os.listdir(input_folder)
        if f.lower().endswith(allowed_extensions)
    ]

    if not image_files:
        print(f"❌ 在 {input_folder} 中未找到图片")
        return

    print(f"📸 共发现 {len(image_files)} 张图片")
    print(f"⚙️  参数设置: 强度={fog_intensity}, 时间={time_of_day}, 天气={weather}")

    for file_name in tqdm(image_files, desc="处理进度"):
        try:
            input_path = os.path.join(input_folder, file_name)
            image = cv2.imread(input_path)

            if image is None:
                print(f"⚠ 无法读取: {file_name}")
                continue

            # 处理图片
            fogged_image = add_realistic_fog_effect(
                image,
                fog_intensity=fog_intensity,
                time_of_day=time_of_day,
                weather=weather,
                depth_type=depth_type,
                add_noise=add_noise
            )

            # 保存结果
            output_path = os.path.join(output_folder, file_name)
            cv2.imwrite(output_path, fogged_image)

        except Exception as e:
            print(f"❌ 处理 {file_name} 时出错: {str(e)}")

    print(f"✅ 处理完成！输出目录：{output_folder}")


def preview_effects(image_path: str, output_dir: str = "previews"):
    """
    预览不同参数的雾天效果
    """
    image = cv2.imread(image_path)
    if image is None:
        print("❌ 无法读取图片")
        return

    os.makedirs(output_dir, exist_ok=True)

    # 不同参数的组合
    parameters = [
        {"fog_intensity": 0.3, "time_of_day": "day", "weather": "clear", "desc": "薄雾白天"},
        {"fog_intensity": 0.6, "time_of_day": "day", "weather": "foggy", "desc": "浓雾白天"},
        {"fog_intensity": 0.7, "time_of_day": "morning", "weather": "clear", "desc": "晨雾"},
        {"fog_intensity": 0.8, "time_of_day": "evening", "weather": "hazy", "desc": "傍晚雾霾"},
        {"fog_intensity": 0.9, "time_of_day": "night", "weather": "clear", "desc": "夜雾"},
        {"fog_intensity": 0.5, "time_of_day": "day", "weather": "smog", "desc": "雾霾"},
    ]

    for i, params in enumerate(parameters):
        result = add_realistic_fog_effect(image, **params)

        # 并排显示
        combined = np.hstack([cv2.resize(image, (300, 300)),
                              cv2.resize(result, (300, 300))])

        # 添加文字说明
        text = f"{params['desc']} (强度:{params['fog_intensity']})"
        cv2.putText(combined, text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        output_path = os.path.join(output_dir, f"preview_{i + 1}.jpg")
        cv2.imwrite(output_path, combined)
        print(f"✅ 生成预览: {output_path}")

    print("✨ 预览生成完成！")


def main():
    """主函数"""

    # 基本用法
    input_folder = r"D:\ImgProcess\before"
    output_folder = r"D:\ImgProcess\after"

    # 快速批量处理
    batch_add_fog_enhanced(
        input_folder=input_folder,
        output_folder=output_folder,
        fog_intensity=0.8,  # 雾浓度
        time_of_day="day",  # 时间段
        weather="morning",  # 天气类型
        depth_type="quadratic",  # 深度图类型
        add_noise=True  # 添加噪声
    )


if __name__ == "__main__":
    main()