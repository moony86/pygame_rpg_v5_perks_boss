from dataclasses import dataclass

import pygame

from definitions.sprite_asset_definitions import SPRITE_ANIMATION_DEFINITIONS
from systems.asset_loader import load_image


_SHEET_CACHE = {}
_FRAME_CACHE = {}


@dataclass(frozen=True)
class AnimationSpec:
    character: str
    state: str
    path: str
    frame_size: tuple[int, int]
    expected_frames: int
    fps: float
    loop: bool
    scale: float
    anchor: tuple[float, float]


def _resolve_state_definition(character, state):
    character_def = SPRITE_ANIMATION_DEFINITIONS.get(character)
    if not character_def:
        return None, None
    states = character_def.get("states", {})
    state_def = states.get(state)
    if state_def and "alias" in state_def:
        state_def = states.get(state_def["alias"])
    return character_def, state_def


def animation_spec(character, state):
    character_def, state_def = _resolve_state_definition(character, state)
    if not character_def or not state_def:
        return None
    return AnimationSpec(
        character=character,
        state=state,
        path=state_def["path"],
        frame_size=state_def.get("frame_size", (192, 192)),
        expected_frames=state_def["frames"],
        fps=state_def.get("fps", 8),
        loop=state_def.get("loop", True),
        scale=character_def.get("scale", 1.0),
        anchor=character_def.get("anchor", (0.5, 1.0)),
    )


def load_sprite_sheet(path):
    if path not in _SHEET_CACHE:
        _SHEET_CACHE[path] = load_image(path)
    return _SHEET_CACHE[path]


def load_animation_frames(character, state, scale=None):
    spec = animation_spec(character, state)
    if spec is None:
        return []
    scale = spec.scale if scale is None else scale
    cache_key = (spec.path, spec.frame_size, spec.expected_frames, scale)
    if cache_key in _FRAME_CACHE:
        return _FRAME_CACHE[cache_key]

    sheet = load_sprite_sheet(spec.path)
    if sheet is None:
        _FRAME_CACHE[cache_key] = []
        return []

    frame_w, frame_h = spec.frame_size
    frame_count = min(spec.expected_frames, sheet.get_width() // frame_w)
    frames = []
    target_size = (max(1, round(frame_w * scale)), max(1, round(frame_h * scale)))
    for index in range(frame_count):
        frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), pygame.Rect(index * frame_w, 0, frame_w, frame_h))
        if target_size != (frame_w, frame_h):
            frame = pygame.transform.smoothscale(frame, target_size)
        frames.append(frame)
    _FRAME_CACHE[cache_key] = frames
    return frames


def detected_frame_count(character, state):
    spec = animation_spec(character, state)
    if spec is None:
        return 0
    sheet = load_sprite_sheet(spec.path)
    if sheet is None:
        return 0
    frame_w, _frame_h = spec.frame_size
    return sheet.get_width() // frame_w


class SpriteSheetAnimation:
    def __init__(self, character, state="idle", scale=None, facing_left=False):
        self.character = character
        self.scale = scale
        self.facing_left = facing_left
        self.state = None
        self.elapsed = 0.0
        self.finished = False
        self.set_state(state, restart=True)

    @property
    def spec(self):
        return animation_spec(self.character, self.state)

    @property
    def frames(self):
        return load_animation_frames(self.character, self.state, self.scale)

    def set_state(self, state, restart=False):
        if state == self.state and not restart:
            return
        self.state = state
        self.elapsed = 0.0
        self.finished = False

    def update(self, dt):
        spec = self.spec
        frames = self.frames
        if spec is None or not frames or self.finished:
            return
        self.elapsed += max(0.0, dt)
        if not spec.loop and self.elapsed >= len(frames) / spec.fps:
            self.elapsed = len(frames) / spec.fps
            self.finished = True

    def current_frame_index(self):
        spec = self.spec
        frames = self.frames
        if spec is None or not frames:
            return 0
        index = int(self.elapsed * spec.fps)
        if spec.loop:
            return index % len(frames)
        return min(index, len(frames) - 1)

    def current_frame(self, facing_left=None):
        frames = self.frames
        if not frames:
            return None
        frame = frames[self.current_frame_index()]
        flip = self.facing_left if facing_left is None else facing_left
        if flip:
            frame = pygame.transform.flip(frame, True, False)
        return frame

    def draw(self, surface, feet_pos, camera=None, facing_left=None):
        frame = self.current_frame(facing_left=facing_left)
        spec = self.spec
        if frame is None or spec is None:
            return False
        anchor_x, anchor_y = spec.anchor
        pos = camera.apply_pos(pygame.Vector2(feet_pos)) if camera else pygame.Vector2(feet_pos)
        rect = frame.get_rect()
        rect.x = round(pos.x - rect.width * anchor_x)
        rect.y = round(pos.y - rect.height * anchor_y)
        surface.blit(frame, rect)
        return True


def sprite_animation_report():
    report = {}
    for character, character_def in SPRITE_ANIMATION_DEFINITIONS.items():
        report[character] = {}
        for state, state_def in character_def.get("states", {}).items():
            if "alias" in state_def:
                continue
            spec = animation_spec(character, state)
            detected = detected_frame_count(character, state)
            report[character][state] = {
                "path": spec.path,
                "expected": spec.expected_frames,
                "detected": detected,
                "fps": spec.fps,
                "loop": spec.loop,
                "loaded": len(load_animation_frames(character, state)),
            }
    return report
