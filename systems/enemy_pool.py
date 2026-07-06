from collections import defaultdict

from settings import (
    ENEMY_POOL_MAX_PER_TYPE,
    ENEMY_POOL_PREWARM_PER_TYPE,
    ENEMY_STAGING_X,
    ENEMY_STAGING_Y,
)
from entities.enemy import Enemy, EnemyType


class EnemyPool:
    """Keeps enemy objects staged off-map so waves activate existing objects."""

    def __init__(self):
        self._available = defaultdict(list)
        self._created = defaultdict(int)
        self.prewarm()

    def prewarm(self):
        for enemy_type in EnemyType:
            if enemy_type in (EnemyType.BOSS, EnemyType.LOOT):
                continue
            self.ensure(enemy_type, ENEMY_POOL_PREWARM_PER_TYPE)
        self._warm_special_enemy_assets()

    def _warm_special_enemy_assets(self):
        Enemy(ENEMY_STAGING_X, ENEMY_STAGING_Y, EnemyType.BOSS, difficulty=1.0)
        Enemy(ENEMY_STAGING_X, ENEMY_STAGING_Y, EnemyType.LOOT, difficulty=1.0)

    def ensure(self, enemy_type, count):
        available = self._available[enemy_type]
        while len(available) < count and self._created[enemy_type] < ENEMY_POOL_MAX_PER_TYPE:
            available.append(Enemy(ENEMY_STAGING_X, ENEMY_STAGING_Y, enemy_type, difficulty=1.0))
            self._created[enemy_type] += 1

    def acquire(self, x, y, enemy_type, difficulty=1.0):
        available = self._available[enemy_type]
        if not available:
            self.ensure(enemy_type, 1)
        if available:
            enemy = available.pop()
            enemy.__init__(x, y, enemy_type=enemy_type, difficulty=difficulty)
            return enemy
        return Enemy(x, y, enemy_type=enemy_type, difficulty=difficulty)

    def release(self, enemy):
        enemy_type = getattr(enemy, "type", None)
        if enemy_type in (None, EnemyType.BOSS, EnemyType.LOOT):
            return
        enemy.alive = False
        enemy.rect.center = (ENEMY_STAGING_X, ENEMY_STAGING_Y)
        enemy.last_player_center = None
        enemy.windup_timer = 0.0
        enemy.windup_action = None
        enemy.leap_timer = 0.0
        if len(self._available[enemy_type]) < ENEMY_POOL_MAX_PER_TYPE:
            self._available[enemy_type].append(enemy)

    def release_many(self, enemies):
        for enemy in enemies:
            self.release(enemy)

    def stats(self):
        return {
            enemy_type.name: {
                "available": len(self._available[enemy_type]),
                "created": self._created[enemy_type],
            }
            for enemy_type in self._created
        }
