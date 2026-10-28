import cv2
import numpy as np
import os
import random
from tqdm import tqdm
import time


def generate_rain_drops(img_height, img_width, num_drops=1000, wind_speed=5.0):
    """
    生成随机雨滴参数
    """
    rain_drops = []

    for _ in range(num_drops):
        x = random.randint(0, img_width)
        y = random.randint(0, img_height)
        size = random.randint(10, 30)
        base_angle = -np.pi / 2
        wind_angle = random.uniform(-0.3, 0.1) * wind_speed
        angle = base_angle + wind_angle
        brightness = random.randint(200, 255)
        thickness = random.choice([1, 2])

        rain_drops.append({
            'position': (x, y),
            'size': size,
            'angle': angle,
            'brightness': brightness,
            'thickness': thickness
        })

    return rain_drops


def add_rain_to_single_image(image, rain_intensity=0.5, wind_strength=3.0, alpha=0.7):
    """
    为单张图片添加雨滴效果

    参数:
        image: 输入图片
        rain_intensity: 雨强度 0.1-1.0
        wind_strength: 风力强度
        alpha: 雨滴透明度
    """
    h, w = image.shape[:2]

    # 1. 调整雨天整体色调（降低饱和度和亮度）
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] *= 0.7  # 降低饱和度
    hsv[:, :, 2] *= 0.8  # 降低亮度
    hsv = np.clip(hsv, 0, 255).astype(np.uint8)
    base_image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    # 2. 创建雨图层
    rain_layer = np.zeros((h, w, 3), dtype=np.uint8)

    # 3. 计算雨滴数量
    max_drops = 5000
    num_drops = int(max_drops * rain_intensity)
    if num_drops < 100:
        num_drops = 100

    # 4. 绘制雨滴
    for _ in range(num_drops):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        length = random.randint(15, 40)
        base_angle = -np.pi / 2
        wind_effect = wind_strength * random.uniform(-0.1, 0.2)
        angle = base_angle + wind_effect
        brightness = 180 + random.randint(0, 50)

        end_x = int(x + length * np.cos(angle))
        end_y = int(y + length * np.sin(angle))

        if 0 <= end_x < w and 0 <= end_y < h:
            color = (brightness, brightness, brightness + 20)  # 偏蓝白色
            cv2.line(rain_layer, (x, y), (end_x, end_y), color, 1)

    # 5. 添加运动模糊
    kernel_size = 3 + int(rain_intensity * 2)
    if kernel_size % 2 == 0:
        kernel_size += 1
    rain_layer = cv2.GaussianBlur(rain_layer, (kernel_size, kernel_size), 0)

    # 6. 混合图层
    result = cv2.addWeighted(base_image, 1 - alpha, rain_layer, alpha, 0)

    return result


def batch_add_rain_effect(input_folder, output_folder, rain_intensity=0.5,
                          wind_strength=3.0, alpha=0.7, overwrite=False):
    """
    批量处理文件夹中的所有图片，添加雨滴效果

    参数:
        input_folder: 输入图片文件夹路径
        output_folder: 输出图片文件夹路径
        rain_intensity: 雨强度 (0.1-1.0)
        wind_strength: 风力强度
        alpha: 雨滴透明度
        overwrite: 是否覆盖已存在的输出文件
    """
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)

    # 支持的图片格式
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp')

    # 获取所有图片文件
    image_files = []
    for file in os.listdir(input_folder):
        if file.lower().endswith(supported_formats):
            image_files.append(file)

    if not image_files:
        print(f"❌ 在文件夹 {input_folder} 中未找到支持的图片文件")
        print(f"   支持的格式: {', '.join(supported_formats)}")
        return

    print(f"📁 输入文件夹: {input_folder}")
    print(f"📁 输出文件夹: {output_folder}")
    print(f"🌧️  雨强度: {rain_intensity}")
    print(f"💨 风力强度: {wind_strength}")
    print(f"🔍 发现 {len(image_files)} 张图片")
    print("=" * 50)

    processed_count = 0
    failed_count = 0

    # 处理每张图片
    for file_name in tqdm(image_files, desc="添加雨滴效果", unit="张"):
        try:
            # 构建完整路径
            input_path = os.path.join(input_folder, file_name)
            output_path = os.path.join(output_folder, file_name)

            # 如果不覆盖且文件已存在，则跳过
            if not overwrite and os.path.exists(output_path):
                print(f"⏭️  跳过 {file_name} (文件已存在)")
                continue

            # 读取图片
            image = cv2.imread(input_path)
            if image is None:
                print(f"❌ 无法读取图片: {file_name}")
                failed_count += 1
                continue

            # 记录原始尺寸
            original_h, original_w = image.shape[:2]

            # 添加雨滴效果
            rain_image = add_rain_to_single_image(
                image,
                rain_intensity=rain_intensity,
                wind_strength=wind_strength,
                alpha=alpha
            )

            # 保存结果
            cv2.imwrite(output_path, rain_image)
            processed_count += 1

            # 显示处理信息
            print(f"✅ 已处理: {file_name} ({original_w}x{original_h})")

        except Exception as e:
            print(f"❌ 处理 {file_name} 时出错: {str(e)}")
            failed_count += 1

    # 输出统计信息
    print("\n" + "=" * 50)
    print("📊 处理完成统计:")
    print(f"   总图片数: {len(image_files)}")
    print(f"   成功处理: {processed_count}")
    print(f"   处理失败: {failed_count}")
    print(f"   跳过/已存在: {len(image_files) - processed_count - failed_count}")

    if processed_count > 0:
        print(f"\n🎉 所有处理完成的图片已保存到: {output_folder}")


def preview_rain_effect(image_path, output_folder="rain_previews"):
    """
    预览不同雨滴效果

    参数:
        image_path: 示例图片路径
        output_folder: 预览图片输出文件夹
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ 无法读取图片: {image_path}")
        return

    os.makedirs(output_folder, exist_ok=True)

    # 不同参数组合
    rain_styles = [
        {"intensity": 0.2, "wind": 1.0, "desc": "细雨", "alpha": 0.5},
        {"intensity": 0.4, "wind": 2.0, "desc": "小雨", "alpha": 0.6},
        {"intensity": 0.6, "wind": 3.0, "desc": "中雨", "alpha": 0.7},
        {"intensity": 0.8, "wind": 4.0, "desc": "大雨", "alpha": 0.8},
        {"intensity": 1.0, "wind": 5.0, "desc": "暴雨", "alpha": 0.9},
    ]

    print(f"🌧️  正在生成雨滴效果预览...")
    print(f"   示例图片: {image_path}")
    print(f"   输出文件夹: {output_folder}")
    print("=" * 50)

    previews = []
    for i, style in enumerate(rain_styles, 1):
        result = add_rain_to_single_image(
            image,
            rain_intensity=style["intensity"],
            wind_strength=style["wind"],
            alpha=style["alpha"]
        )

        # 添加文字标签
        label = f"{style['desc']} (强度:{style['intensity']})"
        cv2.putText(result, label, (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 保存预览
        preview_path = os.path.join(output_folder, f"preview_{i}_{style['desc']}.jpg")
        cv2.imwrite(preview_path, result)
        previews.append(result)

        print(f"✅ 生成预览: {preview_path}")

    # 创建对比图
    h, w = image.shape[:2]
    preview_height = h // 3
    preview_width = w // 3

    # 调整所有预览图到相同尺寸
    previews_resized = [cv2.resize(img, (preview_width, preview_height)) for img in previews]
    original_resized = cv2.resize(image, (preview_width, preview_height))

    # 创建对比网格
    top_row = np.hstack([original_resized, previews_resized[0], previews_resized[1]])
    bottom_row = np.hstack([previews_resized[2], previews_resized[3], previews_resized[4]])
    comparison = np.vstack([top_row, bottom_row])

    # 添加网格线
    cv2.line(comparison, (preview_width, 0), (preview_width, preview_height * 2), (255, 255, 255), 2)
    cv2.line(comparison, (preview_width * 2, 0), (preview_width * 2, preview_height * 2), (255, 255, 255), 2)
    cv2.line(comparison, (0, preview_height), (preview_width * 3, preview_height), (255, 255, 255), 2)

    # 添加标签
    labels = ["原图", "细雨", "小雨", "中雨", "大雨", "暴雨"]
    for i, label in enumerate(labels):
        x = i * preview_width + 10
        y = preview_height - 10 if i < 3 else preview_height * 2 - 10
        cv2.putText(comparison, label, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
        cv2.putText(comparison, label, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # 保存对比图
    comparison_path = os.path.join(output_folder, "雨滴效果对比.jpg")
    cv2.imwrite(comparison_path, comparison)

    print(f"\n✨ 预览完成!")
    print(f"📊 对比图已保存: {comparison_path}")

    # 显示对比图
    cv2.imshow("Rain Effect Comparison", comparison)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def main():
    """主函数"""
    # 设置您的输入输出路径
    input_folder = r"D:\ImgProcess\before"
    output_folder = r"D:\ImgProcess\after"

    # 批量处理参数设置
    rain_intensity = 0.01  # 雨强度: 0.1(细雨) ~ 1.0(暴雨)
    wind_strength = 0.6  # 风力: 0.0(无风) ~ 5.0(强风)
    alpha = 0.3  # 雨滴透明度: 0.1 ~ 1.0
    overwrite = False  # 是否覆盖已存在的输出文件

    print("=" * 50)
    print("🌧️  批量雨滴效果处理程序")
    print("=" * 50)

    # 检查输入文件夹是否存在
    if not os.path.exists(input_folder):
        print(f"❌ 输入文件夹不存在: {input_folder}")
        print("请检查路径是否正确！")
        return

    # 询问用户选择模式
    print("\n请选择处理模式:")
    print("1. 批量处理所有图片")
    print("2. 生成效果预览（需要指定一张示例图片）")

    try:
        choice = input("\n请输入选择 (1 或 2): ").strip()

        if choice == "1":
            # 批量处理模式
            start_time = time.time()
            batch_add_rain_effect(
                input_folder=input_folder,
                output_folder=output_folder,
                rain_intensity=rain_intensity,
                wind_strength=wind_strength,
                alpha=alpha,
                overwrite=overwrite
            )
            end_time = time.time()
            print(f"⏱️  总耗时: {end_time - start_time:.2f} 秒")

        elif choice == "2":
            # 预览模式
            print("\n请指定一张用于预览的示例图片:")
            print("支持的格式: .jpg, .jpeg, .png, .bmp")

            # 查找示例图片
            supported_formats = ('.jpg', '.jpeg', '.png', '.bmp')
            example_images = []
            for file in os.listdir(input_folder):
                if file.lower().endswith(supported_formats):
                    example_images.append(file)

            if not example_images:
                print("❌ 未找到示例图片")
                return

            # 显示找到的图片
            print(f"\n在输入文件夹中找到 {len(example_images)} 张图片:")
            for i, img in enumerate(example_images[:10], 1):  # 显示前10张
                print(f"  {i}. {img}")
            if len(example_images) > 10:
                print(f"  ... 还有 {len(example_images) - 10} 张")

            # 让用户选择
            try:
                choice = input(f"\n请选择一张图片 (1-{len(example_images)}) 或输入文件名: ").strip()

                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(example_images):
                        example_image = example_images[idx]
                    else:
                        print("❌ 选择无效")
                        return
                else:
                    # 用户直接输入文件名
                    if choice in example_images:
                        example_image = choice
                    else:
                        print("❌ 文件名不存在")
                        return

                image_path = os.path.join(input_folder, example_image)
                preview_folder = os.path.join(output_folder, "previews")
                preview_rain_effect(image_path, preview_folder)

            except ValueError:
                print("❌ 输入无效")
                return

        else:
            print("❌ 无效选择，请输入 1 或 2")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")

    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")

    finally:
        print("\n" + "=" * 50)
        print("👋 程序结束")
        print("=" * 50)


if __name__ == "__main__":
    # 检查依赖库
    try:
        import cv2
        import numpy as np
        from tqdm import tqdm
    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("请安装以下依赖:")
        print("pip install opencv-python numpy tqdm")
        exit(1)

    main()