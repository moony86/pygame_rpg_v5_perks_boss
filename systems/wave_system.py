import random

from settings import (
    SURVIVAL_ACTIVE_ENEMY_LIMIT,
)
from entities.enemy import Enemy, EnemyType
from systems.room_system import RoomType

WAVE_INCOMING_TIME = 1.15
WAVE_BREAK_TIME = 0.85

THREAT_COSTS = {
    EnemyType.CHASER: 1,
    EnemyType.RANGED: 3,
    EnemyType.JUMPER: 4,
    EnemyType.HUNTER: 5,
    EnemyType.BRUTE: 6,
    EnemyType.ELITE: 10,
}

ROOM_THREAT_BUDGETS = {
    1: 125,
    2: 260,
    3: 70,
    4: 88,
    5: 110,
}

COMBAT_WAVE_COUNTS = {
    1: 5,
    2: 10,
}

SURVIVAL_THREAT_BUDGETS = {
    2: 650,
    3: 800,
    4: 950,
    5: 1100,
}

SURVIVAL_RAMP_CAPS = [
    (0.0, 10),
    (3.0, 20),
    (6.0, 35),
    (10.0, 55),
    (15.0, SURVIVAL_ACTIVE_ENEMY_LIMIT),
]


class WaveSystem:
    def __init__(self):
        self.waves = []
        self.current_wave_index = 0
        self.spawn_timer = 0.0
        self.spawn_delay = 0.24
        self.spawn_burst_size = 1
        self.enemies_left_to_spawn = 0
        self.active = False
        self.finished_spawning = False
        self.difficulty = 1.0
        self.player_pressure = 0.0
        self.room_type = RoomType.COMBAT
        self.wave_state = "idle"
        self.wave_timer = 0.0
        self.wave_message = ""

    def reset(self, room_number, room_type, player=None):
        self.current_wave_index = 0
        self.spawn_timer = 0.0
        self.active = True
        self.finished_spawning = False
        self.room_type = room_type
        self.player_pressure = self._player_pressure(player)
        self.difficulty = self._base_difficulty(room_number, room_type)
        self.wave_timer = 0.0
        self.wave_message = ""

        self.waves = self._build_waves(room_number, room_type)
        self._start_current_wave()

    def _player_pressure(self, player):
        if player is None:
            return 0.0
        level_pressure = max(0, player.level - 1) * 0.18
        build_pressure = player.build_power_score() * 0.12
        return level_pressure + build_pressure

    def _base_difficulty(self, room_number, room_type):
        difficulty = 1.0 + room_number * 0.55 + self.player_pressure
        if room_type == RoomType.SURVIVAL:
            difficulty *= 1.75
        elif room_type == RoomType.CURSE:
            difficulty *= 1.65
        elif room_type == RoomType.ELITE:
            difficulty *= 1.45
        return difficulty

    def _build_waves(self, room_number, room_type):
        if room_type == RoomType.TREASURE:
            return []

        if room_type == RoomType.SURVIVAL:
            return [self._build_survival_wave(room_number)]

        if room_type == RoomType.ELITE:
            return [
                {
                    "count": count,
                    "types": [EnemyType.ELITE],
                    "difficulty_bonus": 0.45 + index * 0.14,
                    "delay": 0.08,
                    "burst": count,
                    "label": f"ELITE SPLIT {index + 1}",
                }
                for index, count in enumerate((1, 2, 4))
            ]

        return self._build_budget_waves(room_number, room_type)

    def _room_threat_budget(self, room_number, room_type):
        budget = ROOM_THREAT_BUDGETS.get(room_number)
        if budget is None:
            budget = ROOM_THREAT_BUDGETS[max(ROOM_THREAT_BUDGETS)] + max(0, room_number - 5) * 20
        if room_type == RoomType.CURSE:
            budget = int(budget * 1.35)
        return budget

    def _enemy_pool_for_wave(self, room_number, wave_index):
        if room_number <= 1 and wave_index == 0:
            return [EnemyType.CHASER, EnemyType.RANGED]
        if room_number <= 2:
            return [EnemyType.CHASER, EnemyType.RANGED, EnemyType.JUMPER]
        if wave_index < 2:
            return [EnemyType.CHASER, EnemyType.RANGED, EnemyType.JUMPER, EnemyType.HUNTER]
        return [EnemyType.CHASER, EnemyType.RANGED, EnemyType.JUMPER, EnemyType.HUNTER, EnemyType.BRUTE]

    def _survival_threat_budget(self, room_number):
        budget = SURVIVAL_THREAT_BUDGETS.get(room_number)
        if budget is None:
            budget = SURVIVAL_THREAT_BUDGETS[max(SURVIVAL_THREAT_BUDGETS)] + max(0, room_number - 5) * 180
        pressure_bonus = int(self.player_pressure * 85)
        return budget + pressure_bonus

    def _survival_pool(self, room_number):
        if room_number <= 2:
            return [EnemyType.CHASER, EnemyType.CHASER, EnemyType.CHASER, EnemyType.RANGED, EnemyType.JUMPER]
        if room_number <= 4:
            return [EnemyType.CHASER, EnemyType.CHASER, EnemyType.RANGED, EnemyType.JUMPER, EnemyType.HUNTER]
        return [EnemyType.CHASER, EnemyType.RANGED, EnemyType.JUMPER, EnemyType.HUNTER, EnemyType.BRUTE]

    def _build_survival_wave(self, room_number):
        budget = self._survival_threat_budget(room_number)
        pool = self._survival_pool(room_number)
        spawn_queue, remaining_budget = self._build_budget_composition(budget, pool)
        random.shuffle(spawn_queue)

        if room_number <= 2:
            burst, delay, difficulty_bonus = 4, 0.20, 0.35
        elif room_number <= 4:
            burst, delay, difficulty_bonus = 5, 0.17, 0.60
        else:
            burst, delay, difficulty_bonus = 6, 0.15, 0.85

        return {
            "count": len(spawn_queue),
            "types": pool,
            "spawn_queue": spawn_queue,
            "threat_budget": budget,
            "threat_spent": budget - remaining_budget,
            "threat_remaining": remaining_budget,
            "difficulty_bonus": difficulty_bonus,
            "delay": delay,
            "burst": burst,
            "active_limit": SURVIVAL_ACTIVE_ENEMY_LIMIT,
            "ramp_caps": SURVIVAL_RAMP_CAPS,
            "label": "SURVIVAL HORDE",
        }

    def _build_budget_composition(self, budget, pool):
        remaining = budget
        composition = []

        while remaining > 0:
            affordable = [enemy_type for enemy_type in pool if THREAT_COSTS[enemy_type] <= remaining]
            if not affordable:
                break
            weights = [max(1, 8 - THREAT_COSTS[enemy_type]) for enemy_type in affordable]
            enemy_type = random.choices(affordable, weights=weights, k=1)[0]
            cost = THREAT_COSTS[enemy_type]
            composition.append(enemy_type)
            remaining -= cost

        return composition, remaining

    def _build_budget_waves(self, room_number, room_type):
        budget = self._room_threat_budget(room_number, room_type)
        if room_type == RoomType.COMBAT and room_number in COMBAT_WAVE_COUNTS:
            wave_count = COMBAT_WAVE_COUNTS[room_number]
        else:
            wave_count = min(6, max(3, (budget + 19) // 20))
        base_budget = budget // wave_count
        remainder = budget % wave_count

        waves = []
        for index in range(wave_count):
            wave_budget = base_budget + (1 if index < remainder else 0)
            pool = self._enemy_pool_for_wave(room_number, index)
            spawn_queue, remaining_budget = self._build_budget_composition(wave_budget, pool)
            random.shuffle(spawn_queue)

            waves.append({
                "count": len(spawn_queue),
                "types": pool,
                "spawn_queue": spawn_queue,
                "threat_budget": wave_budget,
                "threat_spent": wave_budget - remaining_budget,
                "threat_remaining": remaining_budget,
                "difficulty_bonus": index * 0.22,
                "delay": max(0.08, 0.24 - index * 0.025),
                "burst": 2 + index // 2,
                "label": f"Wave {index + 1}",
            })
        return waves

    def _start_current_wave(self):
        if self.current_wave_index >= len(self.waves):
            self.finished_spawning = True
            self.active = False
            self.wave_state = "done"
            return

        wave = self.waves[self.current_wave_index]
        self.enemies_left_to_spawn = wave["count"]
        self.spawn_delay = wave["delay"]
        self.spawn_burst_size = wave["burst"]
        self.spawn_timer = 0.1
        self.wave_timer = 0.0
        self.wave_state = "spawning"
        self.wave_message = f"{wave['label']} started: {wave['count']} enemies."

    def update(self, dt, spawn_position_func, enemies_alive=0):
        spawned = []

        if not self.active and self.wave_state == "done":
            return spawned

        if self.wave_state == "break":
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self.current_wave_index += 1
                if self.current_wave_index >= len(self.waves):
                    self.finished_spawning = True
                    self.active = False
                    self.wave_state = "done"
                    return spawned
                self.wave_state = "incoming"
                self.wave_timer = WAVE_INCOMING_TIME
                self.wave_message = f"Wave {self.current_wave_index + 1} incoming..."
            return spawned

        if self.wave_state == "incoming":
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self._start_current_wave()
            return spawned

        if self.wave_state == "clearing":
            if enemies_alive <= 0:
                if self.current_wave_index >= len(self.waves) - 1:
                    self.finished_spawning = True
                    self.active = False
                    self.wave_state = "done"
                    self.wave_message = f"Wave {self.current_wave_index + 1} cleared."
                else:
                    self.wave_state = "break"
                    self.wave_timer = WAVE_BREAK_TIME
                    self.wave_message = f"Wave {self.current_wave_index + 1} cleared."
            return spawned

        if self.wave_state != "spawning" or self.enemies_left_to_spawn <= 0:
            self.wave_state = "clearing"
            return spawned

        self.wave_timer += dt
        self.spawn_timer -= dt
        if self.spawn_timer > 0:
            return spawned

        wave = self.waves[self.current_wave_index]
        active_limit = self._current_active_limit(wave)
        if active_limit is not None and enemies_alive >= active_limit:
            self.spawn_timer = 0.08
            return spawned

        allowed_by_cap = self.enemies_left_to_spawn
        if active_limit is not None:
            allowed_by_cap = min(allowed_by_cap, max(0, active_limit - enemies_alive))

        spawn_count = min(self.spawn_burst_size, allowed_by_cap)
        if spawn_count <= 0:
            self.spawn_timer = 0.08
            return spawned

        wave_difficulty = self.difficulty + wave.get("difficulty_bonus", 0.0)

        for _ in range(spawn_count):
            spawn_queue = wave.get("spawn_queue")
            if spawn_queue:
                enemy_type = spawn_queue.pop(0)
            else:
                enemy_type = random.choice(wave["types"])
            x, y = spawn_position_func()
            spawned.append(Enemy(x, y, enemy_type=enemy_type, difficulty=wave_difficulty))

        self.enemies_left_to_spawn -= spawn_count
        self.spawn_timer = self.spawn_delay

        if self.enemies_left_to_spawn <= 0:
            self.wave_state = "clearing"

        return spawned

    def _current_active_limit(self, wave):
        active_limit = wave.get("active_limit")
        ramp_caps = wave.get("ramp_caps")
        if not ramp_caps:
            return active_limit

        cap = ramp_caps[0][1]
        for starts_at, ramp_cap in ramp_caps:
            if self.wave_timer >= starts_at:
                cap = ramp_cap
            else:
                break
        if active_limit is None:
            return cap
        return min(active_limit, cap)

    def all_waves_spawned(self):
        return self.finished_spawning

    def current_wave_number(self):
        if not self.waves:
            return 0
        return min(self.current_wave_index + 1, len(self.waves))

    def consume_wave_message(self):
        message = self.wave_message
        self.wave_message = ""
        return message
