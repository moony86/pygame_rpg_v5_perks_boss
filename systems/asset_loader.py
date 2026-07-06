from pathlib import Path
import time

import pygame


ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
ASSET_LOAD_STATS = {}


def _record_load(name, path, asset_type, success):
    key = str(name)
    stats = ASSET_LOAD_STATS.setdefault(key, {
        "name": key,
        "path": str(path),
        "asset_type": asset_type,
        "load_count": 0,
        "last_loaded": None,
        "success": False,
    })
    stats["path"] = str(path)
    stats["asset_type"] = asset_type
    stats["load_count"] += 1
    stats["last_loaded"] = time.time()
    stats["success"] = success


def asset_load_stats():
    return {key: value.copy() for key, value in ASSET_LOAD_STATS.items()}


def load_image(name, size=None):
    path = ASSET_ROOT / name
    if not path.exists():
        _record_load(name, path, "image", False)
        return None

    try:
        image = pygame.image.load(str(path))
        if pygame.display.get_surface() is not None:
            image = image.convert_alpha()
    except (pygame.error, OSError):
        _record_load(name, path, "image", False)
        return None

    if size is not None and image.get_size() != size:
        image = pygame.transform.smoothscale(image, size)
    _record_load(name, path, "image", True)
    return image


def load_sheet_frames(name, frame_size, max_frames=None, scale=None):
    sheet = load_image(name)
    if sheet is None:
        return []

    frame_w, frame_h = frame_size
    frames = []
    for y in range(0, sheet.get_height() - frame_h + 1, frame_h):
        for x in range(0, sheet.get_width() - frame_w + 1, frame_w):
            frame = pygame.Surface(frame_size, pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), pygame.Rect(x, y, frame_w, frame_h))
            if scale is not None:
                frame = pygame.transform.smoothscale(frame, scale)
            frames.append(frame)
            if max_frames is not None and len(frames) >= max_frames:
                return frames
    return frames
