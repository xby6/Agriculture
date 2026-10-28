"""Generate a field-level variable-rate prescription from a disease class map.

The numerical rules and defaults are carried over from the original
``shp2tiff/datachange.py`` and ``shp2tiff/fieldCut.py`` workflow.  The former
Shapefile round-trip is replaced by equivalent nearest-centre rasterization so
the deployment does not depend on the original project or compiled .pyd files.
"""

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject
from rasterio.windows import Window, bounds as window_bounds
from scipy import ndimage


FINAL_NODATA = -32767.0
VALID_CLASSES = np.array([0, 1, 2, 3], dtype=np.uint8)
VALID_DOSES = np.array([1.5, 2.0, 2.5, 3.0], dtype=np.float32)
DOSE_MAP = {0: 1.5, 1: 2.0, 2: 2.5, 3: 3.0}
DOSE_COLORS = {
    1.5: (0, 255, 0, 255),
    2.0: (0, 0, 255, 255),
    2.5: (255, 255, 0, 255),
    3.0: (255, 0, 0, 255),
}


def shifted_neighbor_any(mask: np.ndarray, valid_mask: np.ndarray, radius: int) -> np.ndarray:
    """Match the original neighborhood test without adding a SciPy dependency here."""
    height, width = mask.shape
    result = np.zeros_like(mask, dtype=bool)
    for delta_row in range(-radius, radius + 1):
        for delta_col in range(-radius, radius + 1):
            if delta_row == 0 and delta_col == 0:
                continue
            src_row0, src_row1 = max(0, -delta_row), min(height, height - delta_row)
            src_col0, src_col1 = max(0, -delta_col), min(width, width - delta_col)
            dst_row0, dst_row1 = max(0, delta_row), min(height, height + delta_row)
            dst_col0, dst_col1 = max(0, delta_col), min(width, width + delta_col)
            result[dst_row0:dst_row1, dst_col0:dst_col1] |= mask[
                src_row0:src_row1, src_col0:src_col1
            ]
    return result & valid_mask


def reduce_moderate_and_severe(
    classes: np.ndarray,
    valid_mask: np.ndarray,
    radius: int = 1,
    reduce_severe_edge: bool = False,
    reduce_moderate_edge: bool = True,
) -> np.ndarray:
    """Preserve the original edge-reduction order and defaults."""
    output = classes.copy()
    if reduce_severe_edge:
        severe = (output == 3) & valid_mask
        not_severe = (output != 3) & valid_mask
        edge = severe & shifted_neighbor_any(not_severe, valid_mask, radius)
        output[edge] = 2
    if reduce_moderate_edge:
        moderate = (output == 2) & valid_mask
        low = ((output == 0) | (output == 1)) & valid_mask
        edge = moderate & shifted_neighbor_any(low, valid_mask, radius)
        output[edge] = 1
    return output


def print_class_stats(title: str, classes: np.ndarray, valid_mask: np.ndarray) -> None:
    total = int(valid_mask.sum())
    print(f"\n[{title}] valid pixels: {total:,}")
    for class_id in range(4):
        count = int(np.sum((classes == class_id) & valid_mask))
        percentage = 100.0 * count / total if total else 0.0
        print(f"  class {class_id}: {count:,} ({percentage:.2f}%)")


def write_world_file(path: Path, transform: rasterio.Affine) -> None:
    path.write_text(
        "\n".join(
            [
                str(transform.a),
                str(transform.d),
                str(transform.b),
                str(transform.e),
                str(transform.c + transform.a / 2.0),
                str(transform.f + transform.e / 2.0),
            ]
        )
        + "\n",
        encoding="ascii",
    )


def rasterize_doses_equivalent(
    classes: np.ndarray,
    valid_mask: np.ndarray,
    source_transform: rasterio.Affine,
    source_crs,
    bounds,
    resolution: int,
) -> Tuple[np.ndarray, rasterio.Affine]:
    """Equivalent to polygonize/dissolve/rasterize with all_touched=False.

    The original polygons partition source pixel footprints. Sampling the
    polygon covering each target-pixel centre is therefore nearest-neighbour
    reprojection of the source categorical dose raster.
    """
    source_dose = np.zeros(classes.shape, dtype=np.float32)
    for class_id, dose in DOSE_MAP.items():
        source_dose[(classes == class_id) & valid_mask] = dose

    target_transform = from_bounds(*bounds, resolution, resolution)
    target = np.zeros((resolution, resolution), dtype=np.float32)
    reproject(
        source=source_dose,
        destination=target,
        src_transform=source_transform,
        src_crs=source_crs,
        dst_transform=target_transform,
        dst_crs=source_crs,
        src_nodata=0.0,
        dst_nodata=0.0,
        resampling=Resampling.nearest,
    )
    return target, target_transform


def neighbor_counts(array: np.ndarray, value: float, radius: int) -> np.ndarray:
    mask = np.isclose(array, value)
    counts = np.zeros(array.shape, dtype=np.uint16)
    height, width = array.shape
    for delta_row in range(-radius, radius + 1):
        for delta_col in range(-radius, radius + 1):
            src_row0, src_row1 = max(0, -delta_row), min(height, height - delta_row)
            src_col0, src_col1 = max(0, -delta_col), min(width, width - delta_col)
            dst_row0, dst_row1 = max(0, delta_row), min(height, height + delta_row)
            dst_col0, dst_col1 = max(0, delta_col), min(width, width + delta_col)
            counts[dst_row0:dst_row1, dst_col0:dst_col1] += mask[
                src_row0:src_row1, src_col0:src_col1
            ]
    return counts


def fill_small_nodata_gaps(
    array: np.ndarray,
    radius: int = 1,
    iterations: int = 3,
    min_valid_neighbors: int = 3,
) -> np.ndarray:
    """Fill small internal holes using the original majority-expansion rule."""
    output = array.astype(np.float32, copy=True)
    output[np.isclose(output, 0.0)] = FINAL_NODATA
    for iteration in range(iterations):
        blank = np.isclose(output, FINAL_NODATA)
        counts = np.stack(
            [neighbor_counts(output, float(value), radius) for value in VALID_DOSES], axis=0
        )
        total = counts.sum(axis=0)
        fill = blank & (total >= min_valid_neighbors)
        best = counts.argmax(axis=0)
        updated = output.copy()
        updated[fill] = VALID_DOSES[best[fill]]
        filled_count = int(fill.sum())
        output = updated
        print(f"[Gap fill] iteration {iteration + 1}: {filled_count:,} pixels")
        if filled_count == 0:
            break
    return output


def label_and_count(
    mask: np.ndarray, structure: np.ndarray, minimum_area: int
) -> Tuple[np.ndarray, List[Dict[str, int]]]:
    labels, number = ndimage.label(mask, structure=structure)
    component_sizes = np.bincount(labels.ravel())
    keep_ids = np.flatnonzero(component_sizes >= minimum_area)
    keep_ids = keep_ids[keep_ids != 0]
    lookup = np.zeros(number + 1, dtype=np.int32)
    lookup[keep_ids] = np.arange(1, keep_ids.size + 1, dtype=np.int32)
    cleaned = lookup[labels]
    fields = [
        {"id": new_id, "area": int(component_sizes[old_id])}
        for new_id, old_id in enumerate(keep_ids, start=1)
    ]
    return cleaned, fields


def auto_make_labels(
    valid_mask: np.ndarray, minimum_area: int = 300, max_erosion: int = 12
) -> Tuple[np.ndarray, Dict]:
    structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8)
    candidates = []
    valid_area = int(valid_mask.sum())
    for iterations in range(max_erosion + 1):
        seed = (
            valid_mask.copy()
            if iterations == 0
            else ndimage.binary_erosion(valid_mask, structure=structure, iterations=iterations)
        )
        seed_labels, seed_fields = label_and_count(seed, structure, minimum_area)
        count = len(seed_fields)
        total_seed_area = sum(field["area"] for field in seed_fields)
        area_ratio = total_seed_area / valid_area
        print(
            f"[Field split] erosion={iterations}: fields={count}, "
            f"seed area ratio={area_ratio:.3f}"
        )
        if count:
            candidates.append(
                {
                    "iterations": iterations,
                    "labels": seed_labels,
                    "count": count,
                    "area_ratio": area_ratio,
                }
            )
    if not candidates:
        raise ValueError("No valid fields found; reduce --minimum-field-area")

    eligible = [candidate for candidate in candidates if candidate["area_ratio"] >= 0.60]
    if not eligible:
        eligible = candidates
    best = sorted(
        eligible,
        key=lambda candidate: (
            candidate["count"],
            -candidate["iterations"],
            candidate["area_ratio"],
        ),
        reverse=True,
    )[0]
    print(
        f"[Field split] selected erosion={best['iterations']}, "
        f"main fields={best['count']}"
    )

    seed_labels = best["labels"]
    seed_mask = seed_labels > 0
    _, indices = ndimage.distance_transform_edt(~seed_mask, return_indices=True)
    labels = np.zeros(seed_labels.shape, dtype=np.int32)
    labels[valid_mask] = seed_labels[indices[0][valid_mask], indices[1][valid_mask]]
    details = {
        "candidates": candidates,
        "selected_iterations": best["iterations"],
        "selected_seed_labels": seed_labels,
        "selected_count": best["count"],
        "selected_area_ratio": best["area_ratio"],
    }
    return labels, details


def calculate_score(values: np.ndarray) -> Optional[float]:
    values = values[np.isin(values, VALID_DOSES)]
    if values.size == 0:
        return None
    weighted = sum(
        np.sum(np.isclose(values, dose)) * level
        for level, dose in enumerate(VALID_DOSES, start=1)
    )
    return float(weighted / values.size)


def nearest_dose(score: float) -> float:
    levels = np.array([1, 2, 3, 4], dtype=np.float32)
    return float(VALID_DOSES[int(np.argmin(np.abs(levels - score)))])


def assign_doses(fields: List[Dict], force_four_levels: bool = True) -> List[Dict]:
    valid_fields = [field for field in fields if field["score"] is not None]
    if force_four_levels and len(valid_fields) >= 4:
        valid_fields.sort(key=lambda field: field["score"])
        count = len(valid_fields)
        for index, field in enumerate(valid_fields):
            ratio = index / (count - 1 + 1e-6)
            if ratio < 0.25:
                field["dose"] = 1.5
            elif ratio < 0.50:
                field["dose"] = 2.0
            elif ratio < 0.75:
                field["dose"] = 2.5
            else:
                field["dose"] = 3.0
    else:
        for field in valid_fields:
            field["dose"] = nearest_dose(field["score"])
    return valid_fields


def save_dose_raster(
    path: Path, array: np.ndarray, transform, crs, nodata: Optional[float]
) -> None:
    profile = {
        "driver": "GTiff",
        "height": array.shape[0],
        "width": array.shape[1],
        "count": 1,
        "dtype": rasterio.float32,
        "crs": crs,
        "transform": transform,
        "compress": "lzw",
    }
    if nodata is not None:
        profile["nodata"] = nodata
    with rasterio.open(path, "w", **profile) as destination:
        destination.write(array.astype(np.float32), 1)
        if nodata is not None:
            destination.update_tags(1, GDAL_NODATA=str(nodata))


def save_prescription_preview(path: Path, array: np.ndarray) -> None:
    rgba = np.zeros((*array.shape, 4), dtype=np.uint8)
    for dose, color in DOSE_COLORS.items():
        rgba[np.isclose(array, dose)] = color
    Image.fromarray(rgba).save(path)


def generate_prescription(
    input_path: Path,
    output_dir: Path,
    resolution: int = 1024,
    shrink_radius: int = 1,
    minimum_field_area: int = 300,
    max_erosion: int = 12,
    save_visual_steps: bool = True,
    visualization_dpi: int = 200,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    pixel_dose_path = output_dir / "pixel_dose_map.tif"
    pixel_dose_tfw = output_dir / "pixel_dose_map.tfw"
    nodata_dose_path = output_dir / "pixel_dose_map_nodata.tif"
    final_path = output_dir / "final_fieldblock_prescription.tif"
    final_tfw = output_dir / "final_fieldblock_prescription.tfw"
    csv_path = output_dir / "field_dose_table.csv"
    preview_path = output_dir / "final_fieldblock_prescription.png"
    visualizer = None
    if save_visual_steps:
        # Keep Matplotlib out of the numerical module unless figures are wanted.
        from prescription_visualization import PrescriptionVisualizer

        visualizer = PrescriptionVisualizer(
            output_dir / "visual_steps", dpi=visualization_dpi
        )

    with rasterio.open(input_path) as source:
        if source.count != 1:
            raise ValueError("Prescription input must be a one-band class GeoTIFF")
        if source.crs is None:
            raise ValueError("Prescription input has no CRS")
        classes = source.read(1)
        valid_mask = np.isin(classes, VALID_CLASSES)
        if not valid_mask.any():
            raise ValueError("Input contains no valid classes 0, 1, 2, or 3")
        source_transform = source.transform
        source_crs = source.crs
        valid_rows = np.flatnonzero(valid_mask.any(axis=1))
        valid_columns = np.flatnonzero(valid_mask.any(axis=0))
        valid_window = Window.from_slices(
            (int(valid_rows[0]), int(valid_rows[-1]) + 1),
            (int(valid_columns[0]), int(valid_columns[-1]) + 1),
        )
        # The original workflow rasterized a Shapefile using its feature bounds,
        # which equal the outer pixel footprints of the valid class region.
        # Do not use source.bounds here: it includes the empty image margins.
        bounds = window_bounds(valid_window, source_transform)

    print(f"[Input] {input_path}")
    print_class_stats("Original classes", classes, valid_mask)
    if visualizer:
        visualizer.save_class_map(
            classes,
            valid_mask,
            "01 Original disease class map",
            "01_original_disease_map.png",
        )
        visualizer.save_mask(
            valid_mask, "02 Valid field mask", "02_valid_mask.png"
        )
    reduced = reduce_moderate_and_severe(classes, valid_mask, radius=shrink_radius)
    print_class_stats("After edge reduction", reduced, valid_mask)
    if visualizer:
        visualizer.save_class_map(
            reduced,
            valid_mask,
            "03 Disease classes after edge reduction",
            "03_reduced_class_map.png",
        )
        visualizer.save_class_compare(
            classes, reduced, valid_mask, "04_before_after_reduce.png"
        )
        visualizer.save_region_view(
            reduced,
            valid_mask,
            "05 Categorical regions used for centre-cell rasterization",
            "05_raster_to_polygon_dissolve.png",
        )

    pixel_dose, target_transform = rasterize_doses_equivalent(
        reduced,
        valid_mask,
        source_transform,
        source_crs,
        bounds,
        resolution,
    )
    save_dose_raster(pixel_dose_path, pixel_dose, target_transform, source_crs, nodata=None)
    write_world_file(pixel_dose_tfw, target_transform)
    if visualizer:
        visualizer.save_dose_map(
            pixel_dose,
            "06 Rasterized pixel-level dose map",
            "06_rasterized_dose_map.png",
        )

    zero_nodata_dose = pixel_dose.astype(np.float32, copy=True)
    zero_nodata_dose[np.isclose(zero_nodata_dose, 0.0)] = FINAL_NODATA
    if visualizer:
        visualizer.save_dose_map(
            zero_nodata_dose,
            "07 Background converted to NoData",
            "07_zero_to_nodata.png",
        )
    nodata_dose = fill_small_nodata_gaps(zero_nodata_dose)
    save_dose_raster(
        nodata_dose_path, nodata_dose, target_transform, source_crs, FINAL_NODATA
    )
    if visualizer:
        visualizer.save_dose_map(
            nodata_dose,
            "08 Pixel-level prescription after gap filling",
            "08_gap_filled_final_prescription.png",
        )

    field_valid = np.isin(nodata_dose, VALID_DOSES)
    print(f"[Field split] valid pixels: {int(field_valid.sum()):,}")
    if visualizer:
        visualizer.save_dose_map(
            nodata_dose,
            "01 Input pixel-level dose map",
            "01_input_dose_map.png",
            field_stage=True,
        )
        visualizer.save_mask(
            field_valid,
            "02 Valid prescription-area mask",
            "02_valid_dose_mask.png",
            field_stage=True,
        )
    labels, field_split = auto_make_labels(
        field_valid, minimum_field_area, max_erosion
    )
    if visualizer:
        visualizer.save_erosion_candidates(
            field_split["candidates"], "03_erosion_candidates.png"
        )
        visualizer.save_labels(
            field_split["selected_seed_labels"],
            "04 Selected eroded seed labels",
            "04_selected_seed_labels.png",
        )
        visualizer.save_labels(
            labels,
            "05 Field labels after nearest-seed backfill",
            "05_backfilled_field_labels.png",
        )

    fields = []
    for label_id in np.unique(labels):
        if label_id == 0:
            continue
        mask = labels == label_id
        area = int(mask.sum())
        if area < minimum_field_area:
            continue
        fields.append(
            {
                "field_id": int(label_id),
                "mask": mask,
                "area": area,
                "score": calculate_score(nodata_dose[mask]),
                "dose": None,
            }
        )

    fields = assign_doses(fields, force_four_levels=True)
    final = np.full(nodata_dose.shape, FINAL_NODATA, dtype=np.float32)
    print(f"\n[Fields] {len(fields)} fields")
    for field in fields:
        final[field["mask"]] = field["dose"]
        print(
            f"  field {field['field_id']}: area={field['area']}, "
            f"score={field['score']:.4f}, dose={field['dose']}"
        )

    if visualizer:
        visualizer.save_field_scores(fields, labels)
        visualizer.save_dose_map(
            final,
            "07 Final field-block prescription",
            "07_final_fieldblock_prescription.png",
            field_stage=True,
        )
        visualizer.save_before_after(
            nodata_dose, final, "08_before_after_compare.png"
        )

    save_dose_raster(final_path, final, target_transform, source_crs, FINAL_NODATA)
    write_world_file(final_tfw, target_transform)
    save_prescription_preview(preview_path, final)
    with csv_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["field_id", "area_pixels", "score", "dose_L_per_mu"])
        for field in fields:
            writer.writerow(
                [field["field_id"], field["area"], round(field["score"], 6), field["dose"]]
            )

    print("\n[Done]")
    print("  pixel dose:", nodata_dose_path)
    print("  final prescription:", final_path)
    print("  field table:", csv_path)
    print("  preview:", preview_path)
    if visualizer:
        print("  visual steps:", output_dir / "visual_steps")


def main() -> None:
    root = Path(__file__).resolve().parent
    default_input = root / "input" / "masked2_cft_disease_heatmap.tif"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=default_input)
    parser.add_argument("--output-dir", type=Path, default=root / "prescription_outputs")
    parser.add_argument("--resolution", type=int, default=1024)
    parser.add_argument("--shrink-radius", type=int, default=1)
    parser.add_argument("--minimum-field-area", type=int, default=300)
    parser.add_argument("--max-erosion", type=int, default=12)
    parser.add_argument(
        "--no-visual-steps",
        action="store_true",
        help="skip Matplotlib process figures; numerical GeoTIFF/CSV outputs are unchanged",
    )
    parser.add_argument("--visualization-dpi", type=int, default=200)
    arguments = parser.parse_args()
    generate_prescription(
        arguments.input,
        arguments.output_dir,
        arguments.resolution,
        arguments.shrink_radius,
        arguments.minimum_field_area,
        arguments.max_erosion,
        not arguments.no_visual_steps,
        arguments.visualization_dpi,
    )


if __name__ == "__main__":
    main()
