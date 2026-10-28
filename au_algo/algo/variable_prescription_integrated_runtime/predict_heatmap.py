"""Generate an argmax disease heat-distribution map from an 8-band GeoTIFF."""

import argparse
import gc
import math
import os
from pathlib import Path
from typing import Tuple

import numpy as np

os.environ.setdefault("GDAL_CACHEMAX", "64")

import rasterio
import torch
from PIL import Image
from rasterio.enums import Resampling
from rasterio.windows import Window

from residual_liquidgate import Predictor


NODATA = 255
COLORMAP = {
    0: (0, 255, 0, 255),
    1: (0, 0, 255, 255),
    2: (255, 0, 0, 255),
    3: (255, 255, 0, 255),
    255: (0, 0, 0, 0),
}


def normalize_if_integer(array: np.ndarray) -> np.ndarray:
    if np.issubdtype(array.dtype, np.integer):
        return array.astype(np.float32) / float(np.iinfo(array.dtype).max)
    return array.astype(np.float32)


def read_with_halo(
    src: rasterio.io.DatasetReader, window: Window, halo: int = 1
) -> Tuple[np.ndarray, np.ndarray]:
    height, width = int(window.height), int(window.width)
    row, col = int(window.row_off), int(window.col_off)
    row0, col0 = max(row - halo, 0), max(col - halo, 0)
    row1 = min(row + height + halo, src.height)
    col1 = min(col + width + halo, src.width)
    data = src.read(window=Window(col0, row0, col1 - col0, row1 - row0), masked=False)
    center = data[:, row - row0 : row - row0 + height, col - col0 : col - col0 + width]
    if src.nodata is None:
        center_mask = np.zeros((height, width), dtype=bool)
    elif np.isnan(src.nodata):
        center_mask = np.any(np.isnan(center), axis=0)
    else:
        center_mask = np.any(center == src.nodata, axis=0)
    padding = (
        (0, 0),
        (row0 - (row - halo), row + height + halo - row1),
        (col0 - (col - halo), col + width + halo - col1),
    )
    if any(value for axis in padding for value in axis):
        data = np.pad(data, padding, mode="reflect")
    return data, center_mask


def save_preview(class_tif: Path, preview_path: Path, max_size: int = 2048) -> None:
    palette = np.asarray([COLORMAP[index][:3] for index in range(4)], dtype=np.uint8)
    with rasterio.open(class_tif) as src:
        scale = min(1.0, max_size / max(src.height, src.width))
        out_h = max(1, round(src.height * scale))
        out_w = max(1, round(src.width * scale))
        levels = src.read(1, out_shape=(out_h, out_w), resampling=Resampling.nearest)
        valid = src.read_masks(1, out_shape=(out_h, out_w), resampling=Resampling.nearest) > 0
    safe_levels = np.where(valid, levels, 0).clip(0, 3).astype(np.uint8)
    rgba = np.empty((out_h, out_w, 4), dtype=np.uint8)
    rgba[..., :3] = palette[safe_levels]
    rgba[..., 3] = np.where(valid, 255, 0).astype(np.uint8)
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(preview_path)


def generate_heatmap(
    input_path: Path,
    output_path: Path,
    model_path: Path,
    preview_path: Path,
    device: str = "auto",
    tile_size: int = 256,
    batch_size: int = 4096,
    stride: int = 3,
) -> None:
    predictor = Predictor(model_path, device=device)
    print(f"[Device] {predictor.device}")
    print(f"[Input] {input_path}")

    with rasterio.open(input_path) as src:
        if src.count != 8:
            raise ValueError(f"expected an 8-band raster, got {src.count} bands")
        profile = src.profile.copy()
        profile.update(count=1, dtype=rasterio.uint8, nodata=NODATA, compress="lzw")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        total = math.ceil(src.height / tile_size) * math.ceil(src.width / tile_size)
        completed = 0

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write_colormap(1, COLORMAP)
            dst.update_tags(
                product="argmax disease heat-distribution map",
                formula="argmax(logits)",
                colors="0=(0,255,0),1=(0,0,255),2=(255,0,0),3=(255,255,0)",
                source_model="ResidualLiquidGateGCN",
            )
            for row in range(0, src.height, tile_size):
                height = min(tile_size, src.height - row)
                for col in range(0, src.width, tile_size):
                    width = min(tile_size, src.width - col)
                    window = Window(col, row, width, height)
                    array, center_mask = read_with_halo(src, window)
                    tensor = torch.from_numpy(normalize_if_integer(array)).unsqueeze(0)
                    patches = torch.nn.functional.unfold(tensor, kernel_size=3, stride=stride)
                    patches = patches.squeeze(0).transpose(0, 1).reshape(-1, 8, 9)

                    out_h, out_w = math.ceil(height / stride), math.ceil(width / stride)
                    patch_classes = np.full(out_h * out_w, NODATA, dtype=np.uint8)
                    grid_r, grid_c = np.meshgrid(
                        np.arange(out_h) * stride, np.arange(out_w) * stride, indexing="ij"
                    )
                    valid = ~center_mask[
                        np.clip(grid_r.ravel(), 0, height - 1),
                        np.clip(grid_c.ravel(), 0, width - 1),
                    ]
                    valid_indices = np.flatnonzero(valid)
                    for start in range(0, valid_indices.size, batch_size):
                        indices = valid_indices[start : start + batch_size]
                        patch_classes[indices] = predictor.heat_level(patches[indices]).astype(np.uint8)

                    class_grid = patch_classes.reshape(out_h, out_w)
                    full = np.repeat(np.repeat(class_grid, stride, axis=0), stride, axis=1)
                    dst.write(full[:height, :width], 1, window=window)
                    completed += 1
                    if completed % 10 == 0 or completed == total:
                        print(
                            f"\r[Progress] {completed}/{total} ({100 * completed / total:.1f}%)",
                            end="",
                            flush=True,
                        )
                    del array, tensor, patches, patch_classes, class_grid, full
                    if completed % 50 == 0:
                        gc.collect()
                        if predictor.device.type == "cuda":
                            torch.cuda.empty_cache()

    print(f"\n[Heatmap] {output_path}")
    save_preview(output_path, preview_path)
    print(f"[Preview] {preview_path}")


def main() -> None:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="input 8-band GeoTIFF")
    parser.add_argument("output", type=Path, help="output indexed heatmap GeoTIFF")
    parser.add_argument("--preview", type=Path, help="output PNG preview")
    parser.add_argument(
        "--model", type=Path, default=root / "exported" / "residual_liquidgate_gcn.pt"
    )
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "cuda"))
    parser.add_argument("--tile-size", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=4096)
    parser.add_argument("--stride", type=int, default=3)
    args = parser.parse_args()
    preview = args.preview or args.output.with_suffix(".png")
    generate_heatmap(
        args.input,
        args.output,
        args.model,
        preview,
        args.device,
        args.tile_size,
        args.batch_size,
        args.stride,
    )


if __name__ == "__main__":
    main()
