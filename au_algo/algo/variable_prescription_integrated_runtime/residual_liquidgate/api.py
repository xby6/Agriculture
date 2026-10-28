"""Small, stable API for loading and calling the exported model."""

from pathlib import Path
from typing import Sequence, Union

import numpy as np
import torch


ArrayLike = Union[np.ndarray, torch.Tensor, Sequence]


class Predictor:
    """Callable classifier backed by a portable TorchScript model."""

    def __init__(self, model_path: Union[str, Path], device: str = "auto") -> None:
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        self.model = torch.jit.load(str(model_path), map_location=self.device)
        self.model.eval()

    def _tensor(self, patches: ArrayLike) -> torch.Tensor:
        x = torch.as_tensor(patches, dtype=torch.float32, device=self.device)
        if x.ndim == 2:
            x = x.unsqueeze(0)
        if tuple(x.shape[1:]) != (8, 9):
            raise ValueError(f"expected [B, 8, 9] or [8, 9], got {tuple(x.shape)}")
        return x.contiguous()

    @torch.inference_mode()
    def heat_level(self, patches: ArrayLike) -> np.ndarray:
        """Return predicted heat-map classes in the range 0..3."""
        return self.model(self._tensor(patches)).cpu().numpy()

    def __call__(self, patches: ArrayLike) -> np.ndarray:
        return self.heat_level(patches)
