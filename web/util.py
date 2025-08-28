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

def annotate_points_with_crosshairs(
    img, points, size=21, color=(0, 255, 0), thickness=2, alpha=0.75
):
    """
    img: np.ndarray, BGR (grayscale ok too)
    points: iterable of (x, y) in pixel coords (floats or ints)
    size: diameter of the marker in pixels
    color: BGR
    alpha: blend factor for a softer overlay
    """
    # Ensure 3-channel BGR for consistent drawing
    base = img.copy()
    if len(base.shape) == 2:
        base = cv2.cvtColor(base, cv2.COLOR_GRAY2BGR)

    overlay = base.copy()
    for (x, y) in points:
        cv2.drawMarker(
            overlay,
            (int(round(x)), int(round(y))),
            color,
            markerType=cv2.MARKER_CROSS,  # or cv2.MARKER_TILTED_CROSS / STAR
            markerSize=int(size),
            thickness=thickness,
            line_type=cv2.LINE_AA
        )
    # Alpha blend to avoid heavy, opaque drawings
    out = cv2.addWeighted(overlay, alpha, base, 1 - alpha, 0)
    return out