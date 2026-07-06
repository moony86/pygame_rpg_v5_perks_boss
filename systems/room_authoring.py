import json
from dataclasses import dataclass, field
from pathlib import Path

import pygame

from settings import DEV_TOOLS_ENABLED, SCREEN_HEIGHT, SCREEN_WIDTH
from systems.room_bounds import current_room_bounds, current_room_rect


SCHEMA_VERSION = "bluecube.room_layout.v1"
DEFAULT_EXPORT_PATH = Path("room_layout.json")
SUPPORTED_TYPES = ("Obstacle", "Portal", "NPC", "Spawn Zone", "Room Exit")


@dataclass
class AuthoringObject:
    id: str
    type: str
    rect: pygame.Rect
    metadata: dict = field(default_factory=dict)


class RoomAuthoring:
    def __init__(self, game):
        self.game = game
        self.active = False
        self.grid_visible = False
        self.snap_enabled = True
        self.grid_size = 32
        self.objects = []
        self.selected_id = None
        self.message = "Room authoring ready"
        self._next_id = 1
        self._draft_source_key = None

    def toggle(self):
        if not DEV_TOOLS_ENABLED:
            return
        self.active = not self.active
        if self.active and not self.objects:
            self.refresh_from_runtime()
        self.message = f"authoring {'on' if self.active else 'off'}"

    def refresh_from_runtime(self):
        self.objects = []
        self.selected_id = None
        self._next_id = 1
        for rect in getattr(self.game, "room_obstacles", []):
            self._append("Obstacle", rect.copy())
        if hasattr(self.game, "portal_rect"):
            self._append("Portal", self.game.portal_rect.copy(), {"portal_type": "hub_portal", "target_scene": "room"})
        for npc in getattr(self.game, "npcs", []):
            self._append("NPC", npc.rect.copy(), {
                "role": getattr(npc, "role", "npc"),
                "name": getattr(npc, "name", "NPC"),
                "dialogue_id": getattr(npc, "dialogue_id", ""),
            })
        if hasattr(self.game, "room_exit_rect"):
            self._append("Room Exit", self.game.room_exit_rect.copy(), {"opens_from": "room_clear"})
        self._draft_source_key = (self.game.state.name, self.game.room_number)
        self.message = f"draft refreshed: {len(self.objects)} objects"

    def clear_authoring_context(self):
        self.objects = []
        self.selected_id = None
        self._next_id = 1
        self._draft_source_key = None
        self.message = "authoring context cleared"

    def set_preview_objects(self, objects):
        self.objects = [self._copy_authoring_object(obj) for obj in objects]
        self.selected_id = self.objects[0].id if self.objects else None
        self._draft_source_key = (self.game.state.name, self.game.room_number)
        self.message = f"preview loaded: {len(self.objects)} objects"

    def context_matches_current_scene(self):
        if self._draft_source_key is None:
            return not self.objects
        return self._draft_source_key == (self.game.state.name, self.game.room_number)

    def create(self, object_type):
        if not self.active or object_type not in SUPPORTED_TYPES:
            return None
        rect = self._default_rect(object_type)
        obj = self._append(object_type, rect, self._default_metadata(object_type))
        self.selected_id = obj.id
        self.message = f"created {object_type}"
        return obj

    def delete_selected(self):
        selected = self.selected()
        if selected is None:
            return False
        self.objects = [obj for obj in self.objects if obj.id != selected.id]
        self.selected_id = None
        self.message = f"deleted {selected.id}"
        return True

    def duplicate_selected(self):
        selected = self.selected()
        if selected is None:
            return None
        rect = selected.rect.copy()
        rect.move_ip(self.grid_size, self.grid_size)
        rect.clamp_ip(current_room_rect())
        obj = self._append(selected.type, rect, selected.metadata.copy())
        self.selected_id = obj.id
        self.message = f"duplicated {selected.id}"
        return obj

    def select_at_screen_pos(self, screen_pos):
        if not self.active:
            return False
        world_pos = self.game.camera.screen_to_world(screen_pos)
        for obj in reversed(self.objects):
            if obj.rect.collidepoint(round(world_pos.x), round(world_pos.y)):
                self.selected_id = obj.id
                self.message = f"selected {obj.id}"
                return True
        self.selected_id = None
        self.message = "authoring selection cleared"
        return True

    def selected(self):
        for obj in self.objects:
            if obj.id == self.selected_id:
                return obj
        return None

    def selected_lines(self):
        obj = self.selected()
        if obj is None:
            return ["No authoring selection", "Create or click a supported object"]
        lines = [
            f"ID: {obj.id}",
            f"Type: {obj.type}",
            f"Position: {obj.rect.x}, {obj.rect.y}",
            f"Size: {obj.rect.w} x {obj.rect.h}",
        ]
        for key, value in obj.metadata.items():
            lines.append(f"{key}: {value}")
        return lines

    def move_selected(self, dx, dy):
        obj = self.selected()
        if obj is None:
            return
        obj.rect.x += dx
        obj.rect.y += dy
        self._finalize_rect(obj.rect)

    def resize_selected(self, dx, dy):
        obj = self.selected()
        if obj is None:
            return
        obj.rect.w = max(self.grid_size, obj.rect.w + dx)
        obj.rect.h = max(self.grid_size, obj.rect.h + dy)
        self._finalize_rect(obj.rect)

    def drag_selected_to(self, world_pos, grab_offset):
        obj = self.selected()
        if obj is None:
            return
        obj.rect.x = round(world_pos.x - grab_offset[0])
        obj.rect.y = round(world_pos.y - grab_offset[1])
        self._finalize_rect(obj.rect)

    def resize_selected_to(self, world_pos):
        obj = self.selected()
        if obj is None:
            return
        obj.rect.w = max(self.grid_size, round(world_pos.x - obj.rect.x))
        obj.rect.h = max(self.grid_size, round(world_pos.y - obj.rect.y))
        self._finalize_rect(obj.rect)

    def cycle_grid_size(self):
        sizes = (16, 32, 64)
        self.grid_size = sizes[(sizes.index(self.grid_size) + 1) % len(sizes)]
        self.message = f"grid {self.grid_size}"

    def toggle_snap(self):
        self.snap_enabled = not self.snap_enabled
        self.message = f"snap {'on' if self.snap_enabled else 'off'}"

    def toggle_grid(self):
        self.grid_visible = not self.grid_visible
        self.message = f"grid {'on' if self.grid_visible else 'off'}"

    def export(self, path=DEFAULT_EXPORT_PATH):
        payload = self.to_payload()
        export_path = Path(path)
        export_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.message = f"exported {export_path}"
        return export_path

    def to_payload(self):
        return {
            "schema": SCHEMA_VERSION,
            "map_size": current_room_bounds().width,
            "source": {
                "state": self.game.state.name,
                "room_number": self.game.room_number,
                "room_type": getattr(getattr(self.game.rooms, "room_type", None), "name", None),
            },
            "objects": [self._serialize(obj) for obj in self.objects],
        }

    def _append(self, object_type, rect, metadata=None):
        obj = AuthoringObject(
            id=f"{object_type.lower().replace(' ', '_')}_{self._next_id:03d}",
            type=object_type,
            rect=rect.copy(),
            metadata=metadata.copy() if metadata else {},
        )
        self._next_id += 1
        self._finalize_rect(obj.rect)
        self.objects.append(obj)
        return obj

    def _default_rect(self, object_type):
        center = self.game.camera.offset + pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        sizes = {
            "Obstacle": (160, 96),
            "Portal": (90, 55),
            "NPC": (46, 46),
            "Spawn Zone": (220, 160),
            "Room Exit": (170, 170),
        }
        w, h = sizes[object_type]
        rect = pygame.Rect(round(center.x - w / 2), round(center.y - h / 2), w, h)
        self._finalize_rect(rect)
        return rect

    def _default_metadata(self, object_type):
        if object_type == "Portal":
            return {"portal_type": "hub_portal", "target_scene": "room"}
        if object_type == "NPC":
            return {"role": "portal", "name": "Portal Guide", "dialogue_id": "portal_intro"}
        if object_type == "Spawn Zone":
            return {"spawn_type": "enemy", "enabled": True}
        if object_type == "Room Exit":
            return {"opens_from": "room_clear"}
        return {}

    def _finalize_rect(self, rect):
        if self.snap_enabled:
            rect.x = self._snap(rect.x)
            rect.y = self._snap(rect.y)
            rect.w = max(self.grid_size, self._snap(rect.w))
            rect.h = max(self.grid_size, self._snap(rect.h))
        rect.clamp_ip(current_room_rect())

    def _snap(self, value):
        return round(value / self.grid_size) * self.grid_size

    def _serialize(self, obj):
        return {
            "id": obj.id,
            "type": obj.type,
            "x": obj.rect.x,
            "y": obj.rect.y,
            "width": obj.rect.w,
            "height": obj.rect.h,
            "metadata": obj.metadata.copy(),
        }

    def _copy_authoring_object(self, obj):
        return AuthoringObject(obj.id, obj.type, obj.rect.copy(), obj.metadata.copy())
