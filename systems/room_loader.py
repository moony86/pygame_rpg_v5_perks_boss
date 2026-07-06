import json
from dataclasses import dataclass
from pathlib import Path

import pygame

from settings import DEV_TOOLS_ENABLED
from systems.room_bounds import current_room_bounds
from systems.room_authoring import AuthoringObject, SCHEMA_VERSION, SUPPORTED_TYPES


DEFAULT_LAYOUT_PATH = Path("room_layout.json")


@dataclass
class RoomLoadResult:
    ok: bool
    errors: list
    warnings: list
    payload: dict | None = None
    objects: list | None = None


class RoomLoader:
    def __init__(self, game, authoring=None):
        self.game = game
        self.authoring = authoring
        self.preview_objects = []
        self.last_result = None
        self.message = "Room loader ready"

    def load(self, path=DEFAULT_LAYOUT_PATH):
        if not DEV_TOOLS_ENABLED:
            return RoomLoadResult(False, ["Dev tools are disabled"], [])
        layout_path = Path(path)
        try:
            payload = json.loads(layout_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            result = RoomLoadResult(False, [f"Layout file not found: {layout_path}"], [])
            self._store_result(result)
            return result
        except json.JSONDecodeError as error:
            result = RoomLoadResult(False, [f"Invalid JSON: {error}"], [])
            self._store_result(result)
            return result

        result = self.validate(payload)
        self._store_result(result)
        return result

    def validate(self, payload):
        errors = []
        warnings = []
        objects = []

        if not isinstance(payload, dict):
            return RoomLoadResult(False, ["Root JSON value must be an object"], warnings)

        if payload.get("schema") != SCHEMA_VERSION:
            errors.append(f"Invalid schema: expected {SCHEMA_VERSION!r}, got {payload.get('schema')!r}")

        map_size = payload.get("map_size")
        if not isinstance(map_size, int) or map_size <= 0:
            errors.append("map_size must be a positive integer")

        raw_objects = payload.get("objects")
        if not isinstance(raw_objects, list):
            errors.append("objects must be a list")
            raw_objects = []

        seen_ids = set()
        for index, raw in enumerate(raw_objects):
            obj = self._validate_object(raw, index, seen_ids, errors, warnings)
            if obj is not None:
                objects.append(obj)

        return RoomLoadResult(not errors, errors, warnings, payload=payload, objects=objects)

    def preview_current_room(self, path=DEFAULT_LAYOUT_PATH):
        result = self.load(path)
        if not result.ok:
            self.message = "preview failed"
            return result
        self.preview_objects = [self._copy_object(obj) for obj in result.objects]
        if self.authoring is not None:
            self.authoring.active = True
            self.authoring.set_preview_objects(self.preview_objects)
        self.message = f"preview loaded: {len(self.preview_objects)} objects"
        return result

    def clear_preview_state(self):
        self.preview_objects = []
        self.last_result = None
        self.message = "room loader preview cleared"

    def apply_to_current_room(self):
        if not DEV_TOOLS_ENABLED:
            self.message = "dev tools disabled"
            return False
        if not self.preview_objects:
            self.message = "no preview to apply"
            return False

        obstacles = []
        npcs = []
        for obj in self.preview_objects:
            if obj.type == "Obstacle":
                obstacles.append(obj.rect.copy())
            elif obj.type == "Portal":
                self.game.portal_rect = obj.rect.copy()
            elif obj.type == "Room Exit":
                self.game.room_exit_rect = obj.rect.copy()
            elif obj.type == "NPC":
                npcs.append(self._npc_from_object(obj))

        if obstacles:
            self.game.room_obstacles = obstacles
        if npcs:
            self.game.npcs = npcs

        self.game.collision.clear()
        self.game.collision.add_entities(getattr(self.game, "npcs", []))
        if getattr(self.game, "portal_rect", None) is not None:
            self.game.collision.add_rect(self.game.portal_rect)
        for obstacle in getattr(self.game, "room_obstacles", []):
            self.game.collision.add_rect(obstacle)
        self.message = "preview applied to current room"
        return True

    def report_lines(self):
        result = self.last_result
        if result is None:
            return ["No layout loaded"]
        return [
            f"ok: {result.ok}",
            f"errors: {len(result.errors)}",
            f"warnings: {len(result.warnings)}",
            f"objects: {len(result.objects or [])}",
            f"message: {self.message}",
        ] + [f"error: {error}" for error in result.errors[:4]]

    def _validate_object(self, raw, index, seen_ids, errors, warnings):
        if not isinstance(raw, dict):
            errors.append(f"objects[{index}] must be an object")
            return None

        object_id = raw.get("id")
        if not isinstance(object_id, str) or not object_id.strip():
            errors.append(f"objects[{index}] has invalid id")
            return None
        if object_id in seen_ids:
            errors.append(f"Duplicate object id: {object_id!r}")
        seen_ids.add(object_id)

        object_type = raw.get("type")
        if object_type not in SUPPORTED_TYPES:
            errors.append(f"Unknown object type for {object_id!r}: {object_type!r}")
            return None

        coords = {}
        for key in ("x", "y", "width", "height"):
            value = raw.get(key)
            if not isinstance(value, int):
                errors.append(f"{object_id!r}.{key} must be an integer")
                return None
            coords[key] = value

        if coords["width"] <= 0 or coords["height"] <= 0:
            errors.append(f"{object_id!r} size must be positive")
            return None
        if coords["x"] < 0 or coords["y"] < 0:
            errors.append(f"{object_id!r} coordinates must be non-negative")
        bounds = current_room_bounds()
        if coords["x"] + coords["width"] > bounds.width or coords["y"] + coords["height"] > bounds.height:
            warnings.append(f"{object_id!r} extends outside room bounds")

        metadata = raw.get("metadata", {})
        if not isinstance(metadata, dict):
            errors.append(f"{object_id!r}.metadata must be an object")
            return None

        rect = pygame.Rect(coords["x"], coords["y"], coords["width"], coords["height"])
        return AuthoringObject(object_id, object_type, rect, metadata.copy())

    def _npc_from_object(self, obj):
        metadata = obj.metadata
        return self.game.spawn_prefab(
            "npc_gatekeeper",
            x=obj.rect.x,
            y=obj.rect.y,
            name=metadata.get("name", "NPC"),
            role=metadata.get("role", "npc"),
            dialogue_id=metadata.get("dialogue_id", ""),
        )

    def _copy_object(self, obj):
        return AuthoringObject(obj.id, obj.type, obj.rect.copy(), obj.metadata.copy())

    def _store_result(self, result):
        self.last_result = result
        if result.ok:
            self.message = f"loaded {len(result.objects or [])} objects"
        else:
            self.message = f"load failed: {len(result.errors)} errors"
