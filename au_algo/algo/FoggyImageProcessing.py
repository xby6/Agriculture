import cv2
import numpy as np
import os
from pathlib import Path
import time


def dark_channel(img, size=15):
    """计算暗通道图像"""
    b, g, r = cv2.split(img)
    min_img = cv2.min(cv2.min(r, g), b)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (size, size))
    dark = cv2.erode(min_img, kernel)
    return dark


def estimate_atmospheric_light(img, dark):
    """估计大气光值A"""
    h, w = img.shape[:2]
    img_size = h * w
    num_px = max(int(img_size * 0.001), 1)  # 取前0.1%的像素
    dark_flat = dark.ravel()
    img_flat = img.reshape(-1, 3)
    indices = np.argpartition(dark_flat, -num_px)[-num_px:]
    atmos_light = np.max(img_flat[indices], axis=0)
    return atmos_light


def estimate_transmission(img, A, omega=0.95, size=15):
    """估计初始透射率"""
    img_norm = img.astype(np.float32) / A
    dark = dark_channel(img_norm, size)
    trans = 1 - omega * dark
    return np.clip(trans, 0.1, 1.0)  # 设定下限t0=0.1


def guided_filter(I, p, radius=40, eps=1e-3):
    """导向滤波实现"""
    I = I.astype(np.float32) / 255.0
    p = p.astype(np.float32)

    # 均值滤波
    mean_I = cv2.boxFilter(I, -1, (radius, radius))
    mean_p = cv2.boxFilter(p, -1, (radius, radius))
    mean_Ip = cv2.boxFilter(I * p, -1, (radius, radius))

    # 计算协方差
    cov_Ip = mean_Ip - mean_I * mean_p
    mean_II = cv2.boxFilter(I * I, -1, (radius, radius))
    var_I = mean_II - mean_I * mean_I

    # 计算a和b
    a = cov_Ip / (var_I + eps)
    b = mean_p - a * mean_I

    # 计算均值
    mean_a = cv2.boxFilter(a, -1, (radius, radius))
    mean_b = cv2.boxFilter(b, -1, (radius, radius))

    # 输出
    q = mean_a * I + mean_b
    return q


def dehaze_single_image(img, omega=0.95, size=15, refine=True):
    """处理单张图片的去雾"""
    dark = dark_channel(img, size)
    A = estimate_atmospheric_light(img, dark)
    trans = estimate_transmission(img, A, omega, size)

    # 使用导向滤波细化透射率图
    if refine:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        trans = guided_filter(gray, trans, radius=40, eps=1e-3)

    # 图像复原
    J = np.zeros_like(img, dtype=np.float32)
    for i in range(3):
        J[:, :, i] = (img[:, :, i].astype(np.float32) - A[i]) / np.maximum(trans, 0.1) + A[i]

    # 对比度拉伸
    J = np.clip(J, 0, 255).astype(np.uint8)

    # 后处理：自适应直方图均衡化
    if len(J.shape) == 3:  # 彩色图像
        lab = cv2.cvtColor(J, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # 对L通道进行CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)

        # 合并通道并转换回BGR
        lab = cv2.merge([l, a, b])
        J = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    return J, trans, A


def batch_dehaze(input_folder, output_folder, omega=0.95, size=15):
    """
    批量处理文件夹中的所有图片

    参数:
    input_folder: 输入文件夹路径
    output_folder: 输出文件夹路径
    omega: 去雾强度参数 (0~1, 默认0.95)
    size: 暗通道的窗口大小 (默认15)
    """
    # 创建输出文件夹
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # 支持的图片格式
    supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}

    # 获取所有图片文件
    image_files = []
    for ext in supported_formats:
        image_files.extend(list(Path(input_folder).glob(f'*{ext}')))
        image_files.extend(list(Path(input_folder).glob(f'*{ext.upper()}')))

    if not image_files:
        print(f"在文件夹 {input_folder} 中未找到支持的图片文件！")
        return

    print(f"找到 {len(image_files)} 张图片需要处理")

    # 处理统计
    processed = 0
    failed = 0
    start_time = time.time()

    for img_path in image_files:
        try:
            print(f"正在处理: {img_path.name}")

            # 读取图片
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"  警告: 无法读取图片 {img_path.name}")
                failed += 1
                continue

            # 调整大图片的尺寸（提高处理速度）
            max_size = 1200
            h, w = img.shape[:2]
            if max(h, w) > max_size:
                scale = max_size / max(h, w)
                new_w = int(w * scale)
                new_h = int(h * scale)
                img = cv2.resize(img, (new_w, new_h))
                print(f"  已调整尺寸: {w}x{h} -> {new_w}x{new_h}")

            # 去雾处理
            dehazed_img, trans_map, A_light = dehaze_single_image(
                img, omega=omega, size=size, refine=True
            )

            # 生成输出文件名
            output_name = f"{img_path.stem}_dehazed{img_path.suffix}"
            output_path = Path(output_folder) / output_name

            # 保存处理后的图片
            cv2.imwrite(str(output_path), dehazed_img)

            # 可选：保存透射率图
            trans_map_normalized = (trans_map * 255).astype(np.uint8)
            trans_path = Path(output_folder) / f"{img_path.stem}_transmission.png"
            cv2.imwrite(str(trans_path), trans_map_normalized)

            processed += 1
            print(f"  完成: {output_name}")

        except Exception as e:
            print(f"  错误: 处理 {img_path.name} 时出错 - {str(e)}")
            failed += 1

    # 输出统计信息
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 50)
    print("批量处理完成！")
    print(f"总图片数: {len(image_files)}")
    print(f"成功处理: {processed}")
    print(f"处理失败: {failed}")
    print(f"总耗时: {elapsed_time:.2f} 秒")

    print(f"平均每张: {elapsed_time / max(processed, 1):.2f} 秒")
    print(f"输出文件夹: {output_folder}")
    print("=" * 50)


def main():
    """主函数"""
    # 您的输入输出路径
    INPUT = r"D:\ImgProcess\before"
    OUTPUT = r"D:\ImgProcess\after"

    # 检查输入文件夹是否存在
    if not os.path.exists(INPUT):
        print(f"错误: 输入文件夹不存在: {INPUT}")
        return

    print("=== 雾天图片批量处理程序 ===")
    print(f"输入文件夹: {INPUT}")
    print(f"输出文件夹: {OUTPUT}")
    print("-" * 40)

    # 参数设置
    omega = 0.95  # 去雾强度，值越大去雾越强 (0.8~0.99)
    window_size = 15  # 暗通道窗口大小

    print(f"参数设置: omega={omega}, window_size={window_size}")
    print("开始处理...\n")

    # 执行批量处理
    batch_dehaze(INPUT, OUTPUT, omega=omega, size=window_size)

    print("\n处理完成！按任意键退出...")
    input()


if __name__ == "__main__":
    main()