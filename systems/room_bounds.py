from dataclasses import dataclass

import pygame

from settings import MAP_SIZE


@dataclass(frozen=True)
class RoomBounds:
    x: int = 0
    y: int = 0
    width: int = MAP_SIZE
    height: int = MAP_SIZE

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    @property
    def center(self):
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def centerx(self):
        return self.x + self.width // 2

    @property
    def centery(self):
        return self.y + self.height // 2

    @property
    def left(self):
        return self.x

    @property
    def top(self):
        return self.y

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    def clamp_rect_ip(self, rect):
        rect.clamp_ip(self.rect)
        return rect

    def clamp_center(self, center, half_width=0, half_height=0):
        x, y = center
        return (
            max(self.left + half_width, min(self.right - half_width, x)),
            max(self.top + half_height, min(self.bottom - half_height, y)),
        )


DEFAULT_ROOM_BOUNDS = RoomBounds()
HUB_ROOM_BOUNDS = RoomBounds(0, 0, 1920, 1080)
DEFAULT_ROOM_RECT = DEFAULT_ROOM_BOUNDS.rect
_active_room_bounds = DEFAULT_ROOM_BOUNDS
_active_room_rect = DEFAULT_ROOM_RECT


def current_room_bounds():
    return _active_room_bounds


def current_room_rect():
    return _active_room_rect


def set_room_bounds(bounds):
    global _active_room_bounds, _active_room_rect
    _active_room_bounds = bounds
    _active_room_rect = bounds.rect


def reset_room_bounds():
    set_room_bounds(DEFAULT_ROOM_BOUNDS)
