# Courtesy of ChatGPT

from pathlib import Path
import numpy as np
import cv2

def load_image(path, mode="color"):
    """
    path: str or Path
    mode: "color" | "grayscale" | "unchanged"
    returns a NumPy array in BGR (3-channel) for 'color', 1-channel for 'grayscale'
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No file at {p.resolve()}")

    flag_map = {
        "color": cv2.IMREAD_COLOR,
        "grayscale": cv2.IMREAD_GRAYSCALE,
        "unchanged": cv2.IMREAD_UNCHANGED,
    }
    flags = flag_map[mode]

    img = cv2.imread(str(p), flags)

    # Fallback for unusual/unicode paths
    if img is None:
        data = np.fromfile(str(p), dtype=np.uint8)
        img = cv2.imdecode(data, flags)

    if img is None:
        raise ValueError(f"OpenCV could not read {p}")

    # Normalize to 3-channel BGR for drawing if needed
    if mode != "grayscale":
        if img.ndim == 2:  # grayscale loaded via 'unchanged'
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.ndim == 3 and img.shape[2] == 4:  # BGRA -> BGR
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    return img
