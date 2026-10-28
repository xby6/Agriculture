import csv
import io
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
DEFAULT_MODEL_NAME = "pyramid_yolov8_rice_disease_best.pt"


def _as_float(value: Any, default: float) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "是"}


def _safe_extract(zip_path: Path, target_dir: Path) -> None:
    with zipfile.ZipFile(zip_path) as zip_in:
        for index, member in enumerate((item for item in zip_in.infolist() if not item.is_dir()), start=1):
            suffix = Path(member.filename.replace("\\", "/")).suffix.lower()
            if suffix not in IMAGE_EXTENSIONS:
                suffix = ".bin"
            destination = (target_dir / f"input_{index:04d}{suffix}").resolve()
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(zip_in.read(member))


def _iter_images(root: Path) -> Iterable[Path]:
    for current_root, _, files in os.walk(root):
        for filename in files:
            file_path = Path(current_root) / filename
            if file_path.suffix.lower() in IMAGE_EXTENSIONS:
                yield file_path


def _copy_to_ascii_path(image_path: Path, target_dir: Path, index: int) -> Path:
    suffix = image_path.suffix.lower() if image_path.suffix.lower() in IMAGE_EXTENSIONS else ".jpg"
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_path = target_dir / f"image_{index:04d}{suffix}"
    shutil.copyfile(image_path, safe_path)
    return safe_path


def _ensure_pyramid_runtime() -> None:
    runtime_dir = Path(__file__).resolve().parent / "pyramid_yolov8_runtime"
    if not runtime_dir.exists():
        raise FileNotFoundError(f"Pyramid-YOLOv8 runtime not found: {runtime_dir}")

    runtime_path = str(runtime_dir)
    if runtime_path not in sys.path:
        sys.path.insert(0, runtime_path)

    loaded = sys.modules.get("ultralytics")
    if loaded is not None:
        loaded_file = Path(getattr(loaded, "__file__", "")).resolve()
        if runtime_dir.resolve() not in loaded_file.parents:
            for module_name in list(sys.modules):
                if module_name == "ultralytics" or module_name.startswith("ultralytics."):
                    del sys.modules[module_name]


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
            cwd_candidate = configured_path
            if cwd_candidate.exists():
                return cwd_candidate
            return algo_root / configured_path

    candidate = Path(model_name)
    if candidate.exists():
        return candidate

    for candidate in [Path("model") / model_name, algo_root / "model" / model_name]:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f"Model file not found: {model_name}")


def _write_text(zip_out: zipfile.ZipFile, filename: str, content: str) -> None:
    zip_out.writestr(filename, content.encode("utf-8"))


def _box_to_record(image_name: str, model_names: Dict[int, str], box: Any) -> Dict[str, Any]:
    xyxy = box.xyxy[0].tolist()
    cls_id = int(box.cls[0].item()) if box.cls is not None else -1
    conf = float(box.conf[0].item()) if box.conf is not None else 0.0
    return {
        "image": image_name,
        "class_id": cls_id,
        "class_name": model_names.get(cls_id, str(cls_id)),
        "confidence": round(conf, 6),
        "x1": round(float(xyxy[0]), 2),
        "y1": round(float(xyxy[1]), 2),
        "x2": round(float(xyxy[2]), 2),
        "y2": round(float(xyxy[3]), 2),
    }


def algorithm(
    zip_path: Path,
    model_name: str = DEFAULT_MODEL_NAME,
    conf: float = 0.25,
    iou: float = 0.45,
    imgsz: int = 640,
    line_width: int = 3,
    save_txt: bool = True,
    save_conf: bool = True,
    device: str = "",
) -> bytes:
    """
    水稻病害 Pyramid-YOLOv8 检测算法入口。

    平台会传入包含待检测图片的 zip 文件，本函数返回结果 zip：
    - annotated/: 检测框渲染后的图片
    - labels/: YOLO 格式检测结果
    - detections.csv/json: 结构化检测结果
    - summary.json/txt: 任务汇总
    """
    _ensure_pyramid_runtime()

    import cv2
    from ultralytics import YOLO

    conf_value = _as_float(conf, 0.25)
    iou_value = _as_float(iou, 0.45)
    imgsz_value = _as_int(imgsz, 640)
    line_width_value = _as_int(line_width, 3)
    save_txt_value = _as_bool(save_txt, True)
    save_conf_value = _as_bool(save_conf, True)
    device_value = str(device or "").strip()

    model_path = _resolve_model_path(model_name)
    model = YOLO(str(model_path))

    result_buffer = io.BytesIO()
    all_records: List[Dict[str, Any]] = []
    image_summaries: List[Dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="pyramid_yolov8_input_") as temp_dir_name:
        input_dir = Path(temp_dir_name)
        _safe_extract(Path(zip_path), input_dir)
        image_paths = sorted(_iter_images(input_dir), key=lambda p: str(p).lower())
        safe_source_dir = input_dir / "_ascii_sources"

        with zipfile.ZipFile(result_buffer, "w", zipfile.ZIP_DEFLATED) as zip_out:
            if not image_paths:
                _write_text(zip_out, "README.txt", "未发现可检测的图片文件，请上传 jpg/png/bmp/tif/webp 等格式图片。")
            for image_index, image_path in enumerate(image_paths, start=1):
                relative_name = image_path.relative_to(input_dir).as_posix()
                safe_source_path = _copy_to_ascii_path(image_path, safe_source_dir, image_index)
                predict_kwargs = {
                    "source": str(safe_source_path),
                    "conf": conf_value,
                    "iou": iou_value,
                    "imgsz": imgsz_value,
                    "save": False,
                    "verbose": False,
                    "line_width": line_width_value,
                    "show_labels": True,
                    "show_conf": True,
                }
                if device_value:
                    predict_kwargs["device"] = device_value

                prediction = model.predict(**predict_kwargs)[0]
                boxes = [] if prediction.boxes is None else list(prediction.boxes)
                image_records = [_box_to_record(relative_name, model.names, box) for box in boxes]
                all_records.extend(image_records)
                image_summaries.append(
                    {
                        "image": relative_name,
                        "detections": len(image_records),
                        "max_confidence": max((item["confidence"] for item in image_records), default=0),
                    }
                )

                plotted = prediction.plot()
                ok, encoded = cv2.imencode(".jpg", plotted)
                if ok:
                    output_name = Path(relative_name).with_suffix(".jpg").as_posix()
                    zip_out.writestr(f"annotated/{output_name}", encoded.tobytes())

                if save_txt_value:
                    label_lines: List[str] = []
                    for item in image_records:
                        line = [
                            str(item["class_id"]),
                            str(item["x1"]),
                            str(item["y1"]),
                            str(item["x2"]),
                            str(item["y2"]),
                        ]
                        if save_conf_value:
                            line.append(str(item["confidence"]))
                        label_lines.append(" ".join(line))
                    label_name = Path(relative_name).with_suffix(".txt").as_posix()
                    _write_text(zip_out, f"labels/{label_name}", "\n".join(label_lines))

            csv_buffer = io.StringIO()
            fieldnames = ["image", "class_id", "class_name", "confidence", "x1", "y1", "x2", "y2"]
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_records)
            _write_text(zip_out, "detections.csv", csv_buffer.getvalue())
            _write_text(zip_out, "detections.json", json.dumps(all_records, ensure_ascii=False, indent=2))

            summary = {
                "algorithm": "水稻病害PyramidYOLOv8检测算法",
                "model": str(model_path),
                "input_images": len(image_paths),
                "total_detections": len(all_records),
                "parameters": {
                    "conf": conf_value,
                    "iou": iou_value,
                    "imgsz": imgsz_value,
                    "line_width": line_width_value,
                },
                "images": image_summaries,
            }
            _write_text(zip_out, "summary.json", json.dumps(summary, ensure_ascii=False, indent=2))
            _write_text(
                zip_out,
                "summary.txt",
                "\n".join(
                    [
                        "水稻病害 Pyramid-YOLOv8 检测结果",
                        f"输入图片数: {len(image_paths)}",
                        f"检测目标数: {len(all_records)}",
                        f"模型文件: {model_path}",
                    ]
                ),
            )

    result_buffer.seek(0)
    return result_buffer.read()
