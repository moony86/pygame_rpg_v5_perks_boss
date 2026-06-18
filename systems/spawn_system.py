import random
from settings import MAP_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, SPAWN_INTERVAL_START, SPAWN_INTERVAL_MIN
from entities.enemy import Enemy, EnemyType
from systems.room_system import RoomType


class SpawnSystem:
    def __init__(self):
        self.timer = 0.0
        self.spawn_interval = SPAWN_INTERVAL_START
        self.room_time = 0.0
        self.room_number = 1
        self.room_type = RoomType.COMBAT
        self.elite_spawned = False

    def reset(self, room_number, room_type):
        self.timer = 0.0
        self.spawn_interval = SPAWN_INTERVAL_START
        self.room_time = 0.0
        self.room_number = room_number
        self.room_type = room_type
        self.elite_spawned = False

    def update(self, dt, camera):
        self.room_time += dt

        if self.room_type == RoomType.TREASURE:
            return None

        if self.room_type == RoomType.ELITE:
            if not self.elite_spawned:
                self.elite_spawned = True
                return self._spawn_around_screen(camera, forced_type=EnemyType.ELITE)
            return None

        self.timer -= dt
        extra = 0.22 if self.room_type == RoomType.CURSE else 0
        self.spawn_interval = max(SPAWN_INTERVAL_MIN, SPAWN_INTERVAL_START - self.room_time * 0.018 - self.room_number * 0.07 - extra)

        if self.timer > 0:
            return None

        self.timer = self.spawn_interval
        return self._spawn_around_screen(camera)

    def _choose_type(self):
        roll = random.random()

        if self.room_number <= 1:
            if roll < 0.18:
                return EnemyType.RANGED
            return EnemyType.CHASER

        if self.room_number == 2:
            if roll < 0.22:
                return EnemyType.JUMPER
            if roll < 0.50:
                return EnemyType.RANGED
            return EnemyType.CHASER

        if roll < 0.28:
            return EnemyType.JUMPER
        if roll < 0.58:
            return EnemyType.RANGED
        return EnemyType.CHASER

    def _spawn_around_screen(self, camera, forced_type=None):
        margin = 145
        side = random.choice(["top", "bottom", "left", "right"])

        if side == "top":
            x = random.randint(int(camera.offset.x) - margin, int(camera.offset.x + SCREEN_WIDTH) + margin)
            y = int(camera.offset.y) - margin
        elif side == "bottom":
            x = random.randint(int(camera.offset.x) - margin, int(camera.offset.x + SCREEN_WIDTH) + margin)
            y = int(camera.offset.y + SCREEN_HEIGHT) + margin
        elif side == "left":
            x = int(camera.offset.x) - margin
            y = random.randint(int(camera.offset.y) - margin, int(camera.offset.y + SCREEN_HEIGHT) + margin)
        else:
            x = int(camera.offset.x + SCREEN_WIDTH) + margin
            y = random.randint(int(camera.offset.y) - margin, int(camera.offset.y + SCREEN_HEIGHT) + margin)

        x = max(0, min(x, MAP_SIZE - 80))
        y = max(0, min(y, MAP_SIZE - 80))

        difficulty = 1.0 + self.room_number * 0.22 + self.room_time / 160.0
        if self.room_type == RoomType.CURSE:
            difficulty *= 1.25

        return Enemy(x, y, enemy_type=forced_type or self._choose_type(), difficulty=difficulty)
