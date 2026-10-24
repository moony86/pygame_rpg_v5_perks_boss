# systems/projectile_pool.py
from collections import deque
import pygame
from entities.projectile import Projectile

class ProjectilePool:
    """يقوم بتوليد الرصاص مسبقاً وإعادة استخدامه لتجنب استهلاك الذاكرة والمعالج"""
    def __init__(self, prewarm_count=250):
        self._available = deque()
        self._available_ids = set()
        self._items = {}
        self._created_count = 0
        self.prewarm(prewarm_count)

    def prewarm(self, count):
        for _ in range(count):
            # Inactive objects never enter world update/draw lists.
            projectile = Projectile(0, 0, pygame.Vector2(1, 0), damage=0, speed=0)
            projectile.alive = False
            self._available.append(projectile)
            self._available_ids.add(id(projectile))
            self._items[id(projectile)] = projectile
            self._created_count += 1

    def acquire(self, x, y, direction, damage, speed, **kwargs):
        if not self._available:
            # إذا نفذ الرصاص الجاهز أثناء المعارك العنيفة، ننشئ رصاصة جديدة فوراً
            projectile = Projectile(x, y, direction, damage, speed, **kwargs)
            projectile.alive = True
            self._items[id(projectile)] = projectile
            self._created_count += 1
            return projectile

        projectile = self._available.popleft()
        self._available_ids.remove(id(projectile))

        projectile.__init__(x, y, direction, damage, speed, **kwargs)
        projectile.alive = True

        return projectile

    def release(self, projectile):
        identity=id(projectile)
        if identity not in self._items or identity in self._available_ids:
            return
        projectile.alive = False
        projectile.visual_trail.clear()
        self._available.append(projectile)
        self._available_ids.add(identity)

    def reset(self):
        self._available.clear()
        self._available_ids.clear()
        for projectile in self._items.values():
            projectile.alive=False
            projectile.visual_trail.clear()
            self._available.append(projectile)
            self._available_ids.add(id(projectile))


def clear_world_projectiles(game):
    pool=getattr(getattr(game,'shooting',None),'projectile_pool',None)
    if pool is not None:
        pool.reset()
    game.projectiles.clear()
