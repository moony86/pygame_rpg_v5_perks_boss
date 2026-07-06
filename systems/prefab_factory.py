import pygame

from entities.enemy import Enemy, EnemyType
from entities.npc import NPC
from entities.projectile import Projectile


class PrefabFactory:
    def __init__(self, game=None):
        self.game = game

    def create(self, definition, **overrides):
        prefab_type = definition.prefab_type
        metadata = definition.metadata.copy()
        metadata.update({key: value for key, value in overrides.items() if value is not None})

        if prefab_type == "Enemy":
            return self._create_enemy(metadata)
        if prefab_type == "NPC":
            return self._create_npc(metadata)
        if prefab_type in ("Portal", "Obstacle", "Room Exit", "Pickup", "Chest"):
            return self._create_rect(metadata)
        if prefab_type == "Projectile":
            return self._create_projectile(metadata)

        raise ValueError(f"Unsupported prefab type: {prefab_type!r}")

    def _create_enemy(self, metadata):
        x = metadata.get("x", 0)
        y = metadata.get("y", 0)
        enemy_type = metadata.get("enemy_type", EnemyType.CHASER)
        difficulty = metadata.get("difficulty", 1.0)
        if self.game is not None and enemy_type not in (EnemyType.BOSS, EnemyType.LOOT):
            return self.game.enemy_pool.acquire(x, y, enemy_type, difficulty)
        return Enemy(x, y, enemy_type=enemy_type, difficulty=difficulty)

    def _create_npc(self, metadata):
        return NPC(
            metadata.get("x", 0),
            metadata.get("y", 0),
            metadata.get("name", "NPC"),
            metadata.get("role", "npc"),
            metadata.get("dialogue_id", ""),
        )

    def _create_rect(self, metadata):
        x = metadata.get("x", 0)
        y = metadata.get("y", 0)
        width = metadata.get("width", 32)
        height = metadata.get("height", 32)
        return pygame.Rect(x, y, width, height)

    def _create_projectile(self, metadata):
        direction = metadata.get("direction", pygame.Vector2(1, 0))
        return Projectile(
            metadata.get("x", 0),
            metadata.get("y", 0),
            direction,
            metadata.get("damage", 1),
            speed=metadata.get("speed"),
            pierce=metadata.get("pierce", 0),
            critical=metadata.get("critical", False),
            knockback=metadata.get("knockback", 0),
            explosive=metadata.get("explosive", False),
            explosion_radius=metadata.get("explosion_radius", 95),
            explosion_splash_ratio=metadata.get("explosion_splash_ratio", 1 / 3),
        )
