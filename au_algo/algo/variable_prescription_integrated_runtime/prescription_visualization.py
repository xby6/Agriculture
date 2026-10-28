"""Visualization helpers for the prescription-generation workflow.

This module contains only plotting code.  It is intentionally separate from
``generate_prescription.py`` so that the numerical prescription calculation
can be audited or reused without Matplotlib.  All figures are presentation
previews; GeoTIFF files remain the authoritative georeferenced results.
"""

from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import numpy as np


# Disease heatmap colours must match predict_heatmap.py exactly.  Notice that
# class 2 is red and class 3 is yellow because this is the user's final,
# explicitly specified deployment colour table.
CLASS_COLORS = {
    0: "#00ff00",
    1: "#0000ff",
    2: "#ff0000",
    3: "#ffff00",
}
CLASS_LABELS = {
    0: "Class 0",
    1: "Class 1",
    2: "Class 2",
    3: "Class 3",
}

# Prescription colours follow the original dose semantics: 1.5/2.0/2.5/3.0
# L per mu progress from green/blue/yellow/red.
DOSE_VALUES = np.array([1.5, 2.0, 2.5, 3.0], dtype=np.float32)
DOSE_COLORS = {
    1.5: "#00ff00",
    2.0: "#0000ff",
    2.5: "#ffff00",
    3.0: "#ff0000",
}
DOSE_LABELS = {
    1.5: "1.5 L/mu",
    2.0: "2.0 L/mu",
    2.5: "2.5 L/mu",
    3.0: "3.0 L/mu",
}

CLASS_CMAP = ListedColormap([CLASS_COLORS[value] for value in range(4)])
CLASS_NORM = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], CLASS_CMAP.N)
DOSE_CMAP = ListedColormap([DOSE_COLORS[float(value)] for value in DOSE_VALUES])
DOSE_NORM = BoundaryNorm([1.25, 1.75, 2.25, 2.75, 3.25], DOSE_CMAP.N)
SCORE_RED_CMAP = ListedColormap(["#fff7bc", "#fec44f", "#f03b20", "#800026"])


class PrescriptionVisualizer:
    """Save all process figures beneath one portable output directory."""

    def __init__(self, root: Path, dpi: int = 200) -> None:
        self.root = Path(root)
        self.pixel_dir = self.root / "datachange"
        self.field_dir = self.root / "fieldCut"
        self.pixel_dir.mkdir(parents=True, exist_ok=True)
        self.field_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = dpi
        plt.rcParams["font.sans-serif"] = [
            "Microsoft YaHei",
            "SimHei",
            "Arial Unicode MS",
            "DejaVu Sans",
        ]
        plt.rcParams["axes.unicode_minus"] = False

    def _save(self, figure, path: Path, tight: bool = True) -> None:
        if tight:
            figure.tight_layout()
        figure.savefig(path, dpi=self.dpi, bbox_inches="tight", pad_inches=0.05)
        plt.close(figure)
        print(f"[Visualization] {path}")

    @staticmethod
    def _display_sample(*arrays: np.ndarray, max_dimension: int = 1800):
        """Stride-sample only the PNG canvas, never the numerical workflow."""
        if not arrays:
            return tuple()
        height, width = arrays[0].shape
        stride = max(1, int(np.ceil(max(height, width) / max_dimension)))
        return tuple(array[::stride, ::stride] for array in arrays)

    @staticmethod
    def _class_handles():
        return [
            mpatches.Patch(color=CLASS_COLORS[value], label=CLASS_LABELS[value])
            for value in range(4)
        ]

    @staticmethod
    def _dose_handles():
        return [
            mpatches.Patch(color=DOSE_COLORS[float(value)], label=DOSE_LABELS[float(value)])
            for value in DOSE_VALUES
        ]

    @staticmethod
    def _masked_classes(array: np.ndarray, valid_mask: np.ndarray) -> np.ndarray:
        shown = array.astype(np.float32, copy=True)
        shown[~valid_mask] = np.nan
        shown[~np.isin(shown, [0, 1, 2, 3])] = np.nan
        return shown

    @staticmethod
    def _masked_doses(array: np.ndarray) -> np.ndarray:
        shown = array.astype(np.float32, copy=True)
        shown[~np.isin(shown, DOSE_VALUES)] = np.nan
        return shown

    def save_class_map(
        self, array: np.ndarray, valid_mask: np.ndarray, title: str, filename: str
    ) -> None:
        array, valid_mask = self._display_sample(array, valid_mask)
        figure, axis = plt.subplots(figsize=(8, 7))
        axis.imshow(
            self._masked_classes(array, valid_mask),
            cmap=CLASS_CMAP,
            norm=CLASS_NORM,
            interpolation="nearest",
        )
        axis.set_title(title, fontsize=15)
        axis.axis("off")
        axis.legend(handles=self._class_handles(), loc="lower right", fontsize=9)
        self._save(figure, self.pixel_dir / filename)

    def save_mask(
        self, mask: np.ndarray, title: str, filename: str, field_stage: bool = False
    ) -> None:
        (mask,) = self._display_sample(mask)
        figure, axis = plt.subplots(figsize=(8, 7))
        axis.imshow(mask.astype(np.uint8), cmap="gray", interpolation="nearest")
        axis.set_title(title, fontsize=15)
        axis.axis("off")
        destination = self.field_dir if field_stage else self.pixel_dir
        self._save(figure, destination / filename)

    def save_class_compare(
        self,
        before: np.ndarray,
        after: np.ndarray,
        valid_mask: np.ndarray,
        filename: str,
    ) -> None:
        before, after, valid_mask = self._display_sample(before, after, valid_mask)
        figure, axes = plt.subplots(1, 2, figsize=(12, 6))
        for axis, array, title in zip(
            axes, (before, after), ("Before reduction", "After reduction")
        ):
            axis.imshow(
                self._masked_classes(array, valid_mask),
                cmap=CLASS_CMAP,
                norm=CLASS_NORM,
                interpolation="nearest",
            )
            axis.set_title(title)
            axis.axis("off")
        figure.suptitle("Moderate/high-class edge reduction", fontsize=15)
        figure.legend(handles=self._class_handles(), loc="lower center", ncol=4)
        figure.tight_layout(rect=[0, 0.05, 1, 0.95])
        self._save(figure, self.pixel_dir / filename, tight=False)

    def save_region_view(
        self, array: np.ndarray, valid_mask: np.ndarray, title: str, filename: str
    ) -> None:
        """Show categorical regions used by the polygon/raster equivalent step."""
        array, valid_mask = self._display_sample(array, valid_mask)
        shown = self._masked_classes(array, valid_mask)
        boundaries = np.zeros(valid_mask.shape, dtype=bool)
        boundaries[1:, :] |= array[1:, :] != array[:-1, :]
        boundaries[:, 1:] |= array[:, 1:] != array[:, :-1]
        boundaries &= valid_mask
        figure, axis = plt.subplots(figsize=(8, 7))
        axis.imshow(shown, cmap=CLASS_CMAP, norm=CLASS_NORM, interpolation="nearest")
        axis.contour(boundaries.astype(np.uint8), levels=[0.5], colors="black", linewidths=0.15)
        axis.set_title(title, fontsize=15)
        axis.axis("off")
        axis.legend(handles=self._class_handles(), loc="lower right", fontsize=9)
        self._save(figure, self.pixel_dir / filename)

    def save_dose_map(
        self,
        array: np.ndarray,
        title: str,
        filename: str,
        field_stage: bool = False,
    ) -> None:
        (array,) = self._display_sample(array)
        figure, axis = plt.subplots(figsize=(8, 7))
        axis.imshow(
            self._masked_doses(array),
            cmap=DOSE_CMAP,
            norm=DOSE_NORM,
            interpolation="nearest",
        )
        axis.set_title(title, fontsize=15)
        axis.axis("off")
        axis.legend(handles=self._dose_handles(), loc="lower right", fontsize=9)
        destination = self.field_dir if field_stage else self.pixel_dir
        self._save(figure, destination / filename)

    def save_erosion_candidates(self, candidates: List[Dict], filename: str) -> None:
        if not candidates:
            return
        columns = 4
        rows = int(np.ceil(len(candidates) / columns))
        # A moderate DPI avoids multi-gigabyte canvases while retaining readable
        # labels for the original 13-candidate layout.
        figure, axes = plt.subplots(rows, columns, figsize=(4 * columns, 3.3 * rows))
        axes = np.atleast_1d(axes).ravel()
        for axis, candidate in zip(axes, candidates):
            shown = candidate["labels"].astype(np.float32, copy=True)
            shown[shown == 0] = np.nan
            axis.imshow(shown, cmap="tab20", interpolation="nearest")
            axis.set_title(
                f"erosion={candidate['iterations']}, fields={candidate['count']}, "
                f"area={candidate['area_ratio']:.2f}",
                fontsize=8,
            )
            axis.axis("off")
        for axis in axes[len(candidates) :]:
            axis.axis("off")
        figure.suptitle("Erosion candidates for field separation", fontsize=16)
        self._save(figure, self.field_dir / filename)

    def save_labels(self, labels: np.ndarray, title: str, filename: str) -> None:
        shown = labels.astype(np.float32, copy=True)
        shown[shown == 0] = np.nan
        figure, axis = plt.subplots(figsize=(8, 7))
        axis.imshow(shown, cmap="tab20", interpolation="nearest")
        axis.set_title(title, fontsize=15)
        axis.axis("off")
        self._save(figure, self.field_dir / filename)

    def _field_score_array(self, fields: List[Dict], labels: np.ndarray) -> np.ndarray:
        shown = np.full(labels.shape, np.nan, dtype=np.float32)
        for field in fields:
            if field.get("dose") is not None:
                shown[field["mask"]] = float(field["dose"])
        return shown

    def _save_score_variant(
        self, shown: np.ndarray, title: str, filename: str, cmap: ListedColormap
    ) -> None:
        figure, axis = plt.subplots(figsize=(9.5, 7))
        image = axis.imshow(shown, cmap=cmap, norm=DOSE_NORM, interpolation="nearest")
        axis.set_title(title, fontsize=18)
        axis.axis("off")
        colorbar = figure.colorbar(
            image,
            ax=axis,
            ticks=[1.5, 2.0, 2.5, 3.0],
            boundaries=[1.25, 1.75, 2.25, 2.75, 3.25],
            fraction=0.052,
            pad=0.035,
        )
        colorbar.ax.set_yticklabels(
            ["Level 0", "Level 1", "Level 2", "Level 3"]
        )
        colorbar.set_label("Assigned prescription level", fontsize=12)
        self._save(figure, self.field_dir / filename)

    def save_field_scores(self, fields: List[Dict], labels: np.ndarray) -> None:
        shown = self._field_score_array(fields, labels)
        self._save_score_variant(
            shown,
            "Field disease-score classes",
            "06_field_score_map.png",
            DOSE_CMAP,
        )
        self._save_score_variant(
            shown,
            "Field disease-score classes (colour)",
            "06_field_score_map_color.png",
            DOSE_CMAP,
        )
        self._save_score_variant(
            shown,
            "Field disease-score classes (red gradient)",
            "06_field_score_map_red_gradient.png",
            SCORE_RED_CMAP,
        )

    def save_before_after(
        self, before: np.ndarray, after: np.ndarray, filename: str
    ) -> None:
        figure, axes = plt.subplots(1, 2, figsize=(14, 7))
        for axis, array, title in zip(
            axes,
            (before, after),
            ("Pixel-level prescription", "Field-block prescription"),
        ):
            axis.imshow(
                self._masked_doses(array),
                cmap=DOSE_CMAP,
                norm=DOSE_NORM,
                interpolation="nearest",
            )
            axis.set_title(title, fontsize=14)
            axis.axis("off")
        figure.suptitle("Pixel-level to field-block prescription", fontsize=18)
        figure.legend(handles=self._dose_handles(), loc="lower center", ncol=4)
        figure.tight_layout(rect=[0, 0.06, 1, 0.95])
        self._save(figure, self.field_dir / filename, tight=False)
