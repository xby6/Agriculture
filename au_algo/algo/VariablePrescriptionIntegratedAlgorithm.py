import csv
import importlib.util
import io
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List


RASTER_EXTENSIONS = {".tif", ".tiff"}
ZIP_EXTENSIONS = {".zip"}
DEFAULT_MODEL_NAME = "variable_prescription_residual_liquidgate_gcn.pt"


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_int(value: Any, default: int) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_extract(zip_path: Path, target_dir: Path) -> None:
    target_root = target_dir.resolve()
    with zipfile.ZipFile(zip_path) as zip_in:
        for member in zip_in.infolist():
            if member.is_dir():
                continue
            destination = (target_dir / member.filename).resolve()
            if not str(destination).startswith(str(target_root)):
                raise ValueError(f"Unsafe zip path: {member.filename}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(zip_in.read(member))


def _expand_nested_archives(root: Path, max_depth: int = 3) -> None:
    """Extract zip files uploaded inside the platform-generated task package."""
    for _ in range(max_depth):
        archives = sorted(
            path for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in ZIP_EXTENSIONS
        )
        if not archives:
            return
        for archive in archives:
            target = archive.with_suffix("")
            target.mkdir(parents=True, exist_ok=True)
            _safe_extract(archive, target)
            archive.unlink(missing_ok=True)


def _iter_rasters(root: Path) -> Iterable[Path]:
    for current_root, _, files in os.walk(root):
        for filename in files:
            file_path = Path(current_root) / filename
            if file_path.suffix.lower() in RASTER_EXTENSIONS:
                yield file_path


def _find_8band_raster(root: Path) -> Path:
    import rasterio

    candidates = sorted(_iter_rasters(root), key=lambda p: str(p).lower())
    last_error = None
    for candidate in candidates:
        try:
            with rasterio.open(candidate) as dataset:
                if dataset.count == 8:
                    return candidate
        except Exception as exc:  # Keep scanning if an uploaded tif is not a raster.
            last_error = exc
    if candidates and last_error:
        raise ValueError(f"No 8-band GeoTIFF found. Last raster error: {last_error}")
    raise ValueError("No 8-band GeoTIFF found in uploaded zip")


def _resolve_model_path(model_name: str) -> Path:
    import yaml

    algo_root = Path(__file__).resolve().parents[1]
    config_candidates = [Path("model_config.yaml"), algo_root / "model_config.yaml"]
    config_path = next((path for path in config_candidates if path.exists()), None)
    if config_path:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {"models": {}}
        model_info = config.get("models", {}).get(model_name)
        if model_info and model_info.get("file"):
            configured_path = Path(model_info["file"])
            if configured_path.is_absolute():
                return configured_path
            if configured_path.exists():
                return configured_path
            return algo_root / configured_path

    for candidate in [Path(model_name), Path("model") / model_name, algo_root / "model" / model_name]:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Model file not found: {model_name}")


def _runtime_dir() -> Path:
    runtime = Path(__file__).resolve().parent / "variable_prescription_integrated_runtime"
    if not runtime.exists():
        raise FileNotFoundError(f"Variable prescription runtime not found: {runtime}")
    runtime_path = str(runtime)
    if runtime_path not in sys.path:
        sys.path.insert(0, runtime_path)
    return runtime


def _load_runtime_module(module_name: str, filename: str):
    runtime = _runtime_dir()
    module_path = runtime / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load runtime module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_text(zip_out: zipfile.ZipFile, filename: str, content: str) -> None:
    zip_out.writestr(filename, content.encode("utf-8"))


def _add_file_tree(zip_out: zipfile.ZipFile, root: Path, prefix: str) -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        arcname = f"{prefix.rstrip('/')}/{rel}"
        zip_out.write(path, arcname)
        files.append({"path": arcname, "size": path.stat().st_size})
    return files


def _read_field_table(csv_path: Path) -> List[Dict[str, Any]]:
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def algorithm(
    zip_path: Path,
    model_name: str = DEFAULT_MODEL_NAME,
    device: str = "cpu",
    tile_size: int = 256,
    batch_size: int = 4096,
    stride: int = 3,
    resolution: int = 1024,
    shrink_radius: int = 1,
    minimum_field_area: int = 300,
    max_erosion: int = 12,
    save_visual_steps: bool = True,
    visualization_dpi: int = 120,
) -> bytes:
    """Integrated heatmap and variable-rate prescription algorithm entry."""
    predict_heatmap = _load_runtime_module(
        "variable_prescription_predict_heatmap", "predict_heatmap.py"
    )
    generate_prescription = _load_runtime_module(
        "variable_prescription_generate_prescription", "generate_prescription.py"
    )

    device_value = str(device or "cpu").strip() or "cpu"
    tile_size_value = _as_int(tile_size, 256)
    batch_size_value = _as_int(batch_size, 4096)
    stride_value = _as_int(stride, 3)
    resolution_value = _as_int(resolution, 1024)
    shrink_radius_value = _as_int(shrink_radius, 1)
    minimum_field_area_value = _as_int(minimum_field_area, 300)
    max_erosion_value = _as_int(max_erosion, 12)
    save_visual_steps_value = _as_bool(save_visual_steps, True)
    visualization_dpi_value = _as_int(visualization_dpi, 120)
    model_path = _resolve_model_path(model_name)

    result_buffer = io.BytesIO()
    with tempfile.TemporaryDirectory(prefix="variable_prescription_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "outputs"
        prescription_dir = temp_dir / "prescription_outputs"
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        prescription_dir.mkdir(parents=True, exist_ok=True)

        _safe_extract(Path(zip_path), input_dir)
        _expand_nested_archives(input_dir)
        input_raster = _find_8band_raster(input_dir)
        input_name = input_raster.relative_to(input_dir).as_posix()

        heatmap_tif = output_dir / f"{input_raster.stem}_disease_heatmap.tif"
        heatmap_png = output_dir / f"{input_raster.stem}_disease_heatmap.png"
        predict_heatmap.generate_heatmap(
            input_raster,
            heatmap_tif,
            model_path,
            heatmap_png,
            device=device_value,
            tile_size=tile_size_value,
            batch_size=batch_size_value,
            stride=stride_value,
        )

        generate_prescription.generate_prescription(
            heatmap_tif,
            prescription_dir,
            resolution=resolution_value,
            shrink_radius=shrink_radius_value,
            minimum_field_area=minimum_field_area_value,
            max_erosion=max_erosion_value,
            save_visual_steps=save_visual_steps_value,
            visualization_dpi=visualization_dpi_value,
        )

        field_table = _read_field_table(prescription_dir / "field_dose_table.csv")
        summary = {
            "algorithm": "VariablePrescriptionIntegratedAlgorithm",
            "model": str(model_path),
            "input_raster": input_name,
            "heatmap": {
                "tif": "heatmap/" + heatmap_tif.name,
                "preview": "heatmap/" + heatmap_png.name,
            },
            "prescription": {
                "final_tif": "prescription/final_fieldblock_prescription.tif",
                "final_preview": "prescription/final_fieldblock_prescription.png",
                "field_table": "prescription/field_dose_table.csv",
                "field_count": len(field_table),
            },
            "parameters": {
                "device": device_value,
                "tile_size": tile_size_value,
                "batch_size": batch_size_value,
                "stride": stride_value,
                "resolution": resolution_value,
                "shrink_radius": shrink_radius_value,
                "minimum_field_area": minimum_field_area_value,
                "max_erosion": max_erosion_value,
                "save_visual_steps": save_visual_steps_value,
                "visualization_dpi": visualization_dpi_value,
            },
            "fields": field_table,
        }

        with zipfile.ZipFile(result_buffer, "w", zipfile.ZIP_DEFLATED) as zip_out:
            output_files = []
            output_files.extend(_add_file_tree(zip_out, output_dir, "heatmap"))
            output_files.extend(_add_file_tree(zip_out, prescription_dir, "prescription"))
            summary["files"] = output_files
            _write_text(zip_out, "summary.json", json.dumps(summary, ensure_ascii=False, indent=2))
            _write_text(
                zip_out,
                "summary.txt",
                "\n".join(
                    [
                        "变量施药处方图一体化生成结果",
                        f"输入影像: {input_name}",
                        f"热力图: heatmap/{heatmap_tif.name}",
                        "最终处方图: prescription/final_fieldblock_prescription.tif",
                        f"田块数量: {len(field_table)}",
                    ]
                ),
            )

    result_buffer.seek(0)
    return result_buffer.read()
