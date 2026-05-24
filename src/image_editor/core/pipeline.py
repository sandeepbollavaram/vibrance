from __future__ import annotations

import numpy as np

from image_editor.config import EditParams
from image_editor.core.filters import apply_all


def process(image: np.ndarray, params: EditParams) -> np.ndarray:
    """Top-level entry: apply edit params to a BGR uint8 image."""
    return apply_all(image, params)
