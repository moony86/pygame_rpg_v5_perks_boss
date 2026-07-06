import random

from settings import (
    SURVIVAL_ACTIVE_ENEMY_LIMIT,
    COMBAT_SPAWN_DELAY_MIN,
    COMBAT_SPAWN_DELAY_START,
    COMBAT_SPAWN_DELAY_STEP,
    COMBAT_WAVE_BREAK_TIME,
    COMBAT_WAVE_COUNT_PLANS,
    COMBAT_WAVE_INCOMING_TIME,
    COMBAT_WAVE_THREAT_PLANS,
)
from entities.enemy import EnemyType
from definitions.enemy_definitions import enemy_threat_costs
from systems.room_system import RoomType

WAVE_INCOMING_TIME = COMBAT_WAVE_INCOMING_TIME
WAVE_BREAK_TIME = COMBAT_WAVE_BREAK_TIME

THREAT_COSTS = enemy_threat_costs()

BUILD_POWER_INFLUENCE_BY_ROOM = {
    1: 0.10,
    2: 0.25,
    3: 0.45,
    4: 0.60,
    5: 0.75,
    6: 0.90,
}
DEFAULT_BUILD_POWER_INFLUENCE = 1.00
ROOM_1_GROUP_SATURATION_CAP = 24
ROOM_1_GROUP_HARD_CAP = 50
ROOM_1_PRESSURE_RADIUS = 650
ROOM_1_RANGED_PRESSURE_RADIUS = 850
ROOM_1_PRESSURE_FLOOR = 4
ROOM_1_ENEMY_DIFFICULTY = 1.0
ROOM_1_EXPECTED_CLEAR_BUFFER = 2.0
ROOM_1_EXPECTED_CLEAR_MIN = 3.5
ROOM_1_EXPECTED_CLEAR_MAX = 12.0
ROOM_1_ROLE_TIME_COSTS = {
    EnemyType.CHASER: 0.55,
    EnemyType.RANGED: 0.80,
    EnemyType.JUMPER: 1.10,
}

ROOM_THREAT_BUDGETS = {
    1: 125,
    2: 260,
    3: 70,
    4: 88,
    5: 160,
    7: 440,
    8: 560,
    10: 820,
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

FLAVOUR_POOLS = {
    "early": ["mixed", "mixed", "rush", "volley", "swarm"],
    "mid": ["mixed", "rush", "volley", "ambush", "armoured", "swarm"],
    "late": ["mixed", "rush", "volley", "ambush", "armoured", "elite_escort"],
}

FLAVOUR_AFFINITY = {
    "mixed": {},
    "rush": {EnemyType.CHASER: 3.5, EnemyType.CHASER_FAST: 3.0},
    "volley": {
        EnemyType.RANGED: 2.5,
        EnemyType.RANGED_THREE: 2.5,
        EnemyType.RANGED_FIVE: 2.0,
        EnemyType.RANGED_RAIN: 1.8,
    },
    "ambush": {EnemyType.JUMPER: 2.8, EnemyType.JUMPER_FAST: 2.5, EnemyType.HUNTER: 2.5},
    "armoured": {EnemyType.CHASER_TANK: 3.0, EnemyType.BRUTE: 2.8, EnemyType.JUMPER_HEAVY: 2.0},
    "swarm": {EnemyType.CHASER: 4.0, EnemyType.CHASER_FAST: 3.0},
    "elite_escort": {EnemyType.CHASER: 2.5, EnemyType.CHASER_FAST: 2.0, EnemyType.HUNTER: 1.6},
}

FLAVOUR_LABELS = {
    "mixed": "",
    "rush": " - RUSH",
    "volley": " - VOLLEY",
    "ambush": " - AMBUSH",
    "armoured": " - ARMOURED",
    "swarm": " - SWARM",
    "elite_escort": " - ELITE ESCORT",
}


def _pick_flavour(room_number, wave_index, room_type):
    if room_type in (RoomType.ELITE, RoomType.SURVIVAL, RoomType.TREASURE):
        return "mixed"

    if room_number <= 3:
        pool = FLAVOUR_POOLS["early"]
    elif room_number <= 6:
        pool = FLAVOUR_POOLS["mid"]
    else:
        pool = FLAVOUR_POOLS["late"]

    if room_number < 9 or wave_index < 3:
        pool = [flavour for flavour in pool if flavour != "elite_escort"]

    return random.choice(pool)


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
        self.build_power_influence = DEFAULT_BUILD_POWER_INFLUENCE
        self.room_type = RoomType.COMBAT
        self.wave_state = "idle"
        self.wave_timer = 0.0
        self.wave_message = ""
        self.current_group_index = 0
        self.current_group_state = "-"
        self.current_group_elapsed = 0.0
        self.current_group_spawned = 0
        self.current_group_living = 0
        self.current_group_expected_clear_time = "-"
        self.current_group_max_time = "-"
        self.current_group_number = 0
        self.current_group_total = 0
        self.wave_mode = "legacy"
        self.legacy_clearing_gate_active = False
        self.old_spawn_queue_length = 0
        self.nearby_pressure_count = 0
        self.current_group_saturation_cap = "-"
        self.current_group_hard_cap = "-"
        self.release_blocked_reason = "-"
        self.current_group_id = "-"
        self.current_group_name = "-"
        self.next_group_release_reason = "-"

    def reset(self, room_number, room_type, player=None):
        self.current_wave_index = 0
        self.spawn_timer = 0.0
        self.active = True
        self.finished_spawning = False
        self.room_type = room_type
        self.build_power_influence = self._build_power_influence(room_number)
        self.player_pressure = self._player_pressure(player)
        self.difficulty = self._base_difficulty(room_number, room_type)
        self.wave_timer = 0.0
        self.wave_message = ""
        self.current_group_index = 0
        self._clear_group_debug()

        self.waves = self._build_waves(room_number, room_type)
        self._start_current_wave()

    def _player_pressure(self, player):
        if player is None:
            return 0.0
        level_pressure = max(0, player.level - 1) * 0.18
        build_pressure = player.build_power_score() * 0.12 * self.build_power_influence
        return level_pressure + build_pressure

    def _build_power_influence(self, room_number):
        return BUILD_POWER_INFLUENCE_BY_ROOM.get(int(room_number), DEFAULT_BUILD_POWER_INFLUENCE)

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
                    "spawn_queue": [EnemyType.ELITE] * count,
                    "difficulty_bonus": 0.45 + index * 0.14,
                    "delay": 0.08,
                    "burst": count,
                    "label": f"ELITE SPLIT {index + 1}",
                    "flavour": "mixed",
                }
                for index, count in enumerate((1, 2, 4))
            ]

        if room_type == RoomType.COMBAT and room_number == 1:
            return self._build_room_one_grouped_waves()

        return self._build_budget_waves(room_number, room_type)

    def _build_group(self, group_id, name, enemies, burst=3, interval=0.34, max_release_time=None, alive_threshold=2, pressure_floor=2, saturation_cap=ROOM_1_GROUP_SATURATION_CAP, start_delay=0.0, expected_clear_time=None):
        expected_clear_time = expected_clear_time or self._expected_clear_time(enemies)
        max_release_time = max_release_time if max_release_time is not None else expected_clear_time + 2.0
        return {
            "id": group_id,
            "name": name,
            "spawn_queue": list(enemies),
            "count": len(enemies),
            "burst": burst,
            "interval": interval,
            "max_release_time": max_release_time,
            "expected_clear_time": expected_clear_time,
            "alive_threshold": alive_threshold,
            "pressure_floor": pressure_floor,
            "saturation_cap": saturation_cap,
            "hard_cap": ROOM_1_GROUP_HARD_CAP,
            "pressure_radius": ROOM_1_PRESSURE_RADIUS,
            "ranged_pressure_radius": ROOM_1_RANGED_PRESSURE_RADIUS,
            "start_delay": start_delay,
            "state": "not_started",
            "spawned_count": 0,
            "living_ids": set(),
            "elapsed": 0.0,
            "spawn_timer": start_delay,
        }

    def _expected_clear_time(self, enemies):
        total = ROOM_1_EXPECTED_CLEAR_BUFFER
        for enemy_type in enemies:
            total += ROOM_1_ROLE_TIME_COSTS.get(enemy_type, 0.70)
        return max(ROOM_1_EXPECTED_CLEAR_MIN, min(ROOM_1_EXPECTED_CLEAR_MAX, total))

    def _build_grouped_wave(self, label, groups, difficulty_bonus=0.0):
        return {
            "count": sum(group["count"] for group in groups),
            "groups": groups,
            "types": sorted({enemy_type for group in groups for enemy_type in group["spawn_queue"]}, key=lambda enemy_type: enemy_type.name),
            "spawn_queue": [],
            "threat_budget": None,
            "threat_spent": sum(THREAT_COSTS.get(enemy_type, 0) for group in groups for enemy_type in group["spawn_queue"]),
            "threat_remaining": 0,
            "difficulty_bonus": difficulty_bonus,
            "enemy_difficulty_override": ROOM_1_ENEMY_DIFFICULTY,
            "delay": 0.0,
            "burst": 0,
            "active_limit": ROOM_1_GROUP_SATURATION_CAP,
            "label": label,
            "flavour": "grouped",
        }

    def _build_room_one_grouped_waves(self):
        c = EnemyType.CHASER
        r = EnemyType.RANGED
        j = EnemyType.JUMPER
        return [
            self._build_grouped_wave("Room 1 Encounter Groups", [
                self._build_group("r1w1a", "Small Chaser Burst", [c, c, c, c], burst=4, alive_threshold=1),
                self._build_group("r1w1b", "Bigger Chaser Burst", [c, c, c, c, c, c], burst=3, alive_threshold=2),
                self._build_group("r1w1c", "First Support", [c, c, c, r, r], burst=3, alive_threshold=1),
                self._build_group("r1w2a", "Chaser Pack", [c, c, c, c, c, c, r, r], burst=4, alive_threshold=3),
                self._build_group("r1w2b", "Chaser + Ranged", [c, c, c, c, c, c, r, r], burst=3, alive_threshold=3),
                self._build_group("r1w2c", "Push Through", [c, c, c, c, c, r], burst=3, alive_threshold=2),
                self._build_group("r1w3a", "Line Pressure", [c, c, c, c, c, c, r, r, r], burst=4, alive_threshold=3),
                self._build_group("r1w3b", "Jumper Intro", [c, c, c, c, c, r, r, j, j], burst=3, alive_threshold=3),
                self._build_group("r1w3c", "Final Push", [c, c, c, c, c, r, r, r, j, j], burst=4, alive_threshold=3),
            ], difficulty_bonus=0.0),
        ]

    def _room_threat_budget(self, room_number, room_type):
        budget = ROOM_THREAT_BUDGETS.get(room_number)
        if budget is None:
            if room_number > 6:
                budget = 440 + max(0, room_number - 7) * 135
            else:
                budget = ROOM_THREAT_BUDGETS[max(key for key in ROOM_THREAT_BUDGETS if key <= 5)]
        if room_type == RoomType.CURSE:
            budget = int(budget * 1.45)
        return budget

    def _enemy_pool_for_wave(self, room_number, wave_index, room_type=RoomType.COMBAT):
        pool = [EnemyType.CHASER, EnemyType.RANGED]
        if room_number >= 2 or wave_index >= 2:
            pool += [EnemyType.RANGED_THREE, EnemyType.JUMPER]
        if room_number >= 3:
            pool += [EnemyType.CHASER_FAST, EnemyType.HUNTER]
        if room_number >= 4 or wave_index >= 5:
            pool += [EnemyType.RANGED_FIVE, EnemyType.JUMPER_FAST]
        if room_number >= 6:
            pool += [EnemyType.CHASER_TANK, EnemyType.BRUTE, EnemyType.JUMPER_HEAVY]
        if room_number >= 7:
            pool += [EnemyType.HUNTER]
        if room_number >= 8 or room_type == RoomType.CURSE:
            pool += [EnemyType.RANGED_RAIN]
        if room_number >= 9 and wave_index >= 3:
            pool += [EnemyType.ELITE]
        return pool

    def _survival_threat_budget(self, room_number):
        budget = SURVIVAL_THREAT_BUDGETS.get(room_number)
        if budget is None:
            budget = SURVIVAL_THREAT_BUDGETS[max(SURVIVAL_THREAT_BUDGETS)] + max(0, room_number - 5) * 180
        pressure_bonus = int(self.player_pressure * 85)
        return budget + pressure_bonus

    def _survival_pool(self, room_number):
        if room_number <= 2:
            return [EnemyType.CHASER, EnemyType.CHASER, EnemyType.RANGED, EnemyType.RANGED_THREE, EnemyType.JUMPER]
        if room_number <= 4:
            return [EnemyType.CHASER, EnemyType.CHASER_FAST, EnemyType.RANGED, EnemyType.RANGED_THREE, EnemyType.JUMPER, EnemyType.HUNTER]
        return [
            EnemyType.CHASER,
            EnemyType.CHASER_FAST,
            EnemyType.RANGED_THREE,
            EnemyType.RANGED_FIVE,
            EnemyType.JUMPER,
            EnemyType.JUMPER_FAST,
            EnemyType.HUNTER,
            EnemyType.BRUTE,
        ]

    def _build_survival_wave(self, room_number):
        budget = self._survival_threat_budget(room_number)
        pool = self._survival_pool(room_number)
        spawn_queue, remaining_budget = self._build_budget_composition(budget, pool, "mixed")
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
            "flavour": "mixed",
        }

    def _build_budget_composition(self, budget, pool, flavour="mixed"):
        remaining = budget
        composition = []
        affinity = FLAVOUR_AFFINITY.get(flavour, {})
        elite_reserved = False

        if flavour == "elite_escort" and EnemyType.ELITE in pool and remaining >= THREAT_COSTS[EnemyType.ELITE]:
            composition.append(EnemyType.ELITE)
            remaining -= THREAT_COSTS[EnemyType.ELITE]
            elite_reserved = True

        while remaining > 0:
            affordable = [enemy_type for enemy_type in pool if THREAT_COSTS[enemy_type] <= remaining]
            if elite_reserved:
                affordable = [enemy_type for enemy_type in affordable if enemy_type != EnemyType.ELITE]
            if not affordable:
                break
            weights = [max(1, 8 - THREAT_COSTS[enemy_type]) * affinity.get(enemy_type, 1.0) for enemy_type in affordable]
            enemy_type = random.choices(affordable, weights=weights, k=1)[0]
            cost = THREAT_COSTS[enemy_type]
            composition.append(enemy_type)
            remaining -= cost

        return composition, remaining

    def _build_budget_waves(self, room_number, room_type):
        if room_type == RoomType.COMBAT and room_number in COMBAT_WAVE_THREAT_PLANS:
            return self._build_planned_threat_waves(room_number, room_type, COMBAT_WAVE_THREAT_PLANS[room_number])
        if room_type == RoomType.COMBAT and room_number in COMBAT_WAVE_COUNT_PLANS:
            return self._build_planned_count_waves(room_number, room_type, COMBAT_WAVE_COUNT_PLANS[room_number])

        budget = self._room_threat_budget(room_number, room_type)
        wave_count = min(6, max(3, (budget + 19) // 20))
        base_budget = budget // wave_count
        remainder = budget % wave_count
        budgets = [base_budget + (1 if index < remainder else 0) for index in range(wave_count)]
        return self._build_planned_threat_waves(room_number, room_type, budgets)

    def _combat_spawn_delay(self, wave_index):
        return max(COMBAT_SPAWN_DELAY_MIN, COMBAT_SPAWN_DELAY_START - wave_index * COMBAT_SPAWN_DELAY_STEP)

    def _build_planned_threat_waves(self, room_number, room_type, budgets):
        waves = []
        for index, wave_budget in enumerate(budgets):
            pool = self._enemy_pool_for_wave(room_number, index, room_type)
            flavour = _pick_flavour(room_number, index, room_type)
            spawn_queue, remaining_budget = self._build_budget_composition(wave_budget, pool, flavour)
            random.shuffle(spawn_queue)
            waves.append({
                "count": len(spawn_queue),
                "types": pool,
                "spawn_queue": spawn_queue,
                "threat_budget": wave_budget,
                "threat_spent": wave_budget - remaining_budget,
                "threat_remaining": remaining_budget,
                "difficulty_bonus": index * 0.22,
                "delay": self._combat_spawn_delay(index),
                "burst": 1,
                "label": f"Wave {index + 1}",
                "flavour": flavour,
            })
        return waves

    def _build_planned_count_waves(self, room_number, room_type, counts):
        waves = []
        for index, enemy_count in enumerate(counts):
            pool = self._enemy_pool_for_wave(room_number, index, room_type)
            flavour = _pick_flavour(room_number, index, room_type)
            spawn_queue = self._build_count_composition(enemy_count, pool, flavour)
            random.shuffle(spawn_queue)
            waves.append({
                "count": len(spawn_queue),
                "types": pool,
                "spawn_queue": spawn_queue,
                "threat_budget": None,
                "threat_spent": None,
                "threat_remaining": None,
                "difficulty_bonus": index * 0.22,
                "delay": self._combat_spawn_delay(index),
                "burst": 1,
                "label": f"Wave {index + 1}",
                "flavour": flavour,
            })
        return waves

    def _build_count_composition(self, enemy_count, pool, flavour):
        affinity = FLAVOUR_AFFINITY.get(flavour, {})
        composition = []
        elite_reserved = False

        if flavour == "elite_escort" and EnemyType.ELITE in pool and enemy_count > 0:
            composition.append(EnemyType.ELITE)
            elite_reserved = True

        while len(composition) < enemy_count:
            choices = pool
            if elite_reserved:
                choices = [enemy_type for enemy_type in pool if enemy_type != EnemyType.ELITE]
            weights = [max(1, 8 - THREAT_COSTS[enemy_type]) * affinity.get(enemy_type, 1.0) for enemy_type in choices]
            composition.append(random.choices(choices, weights=weights, k=1)[0])

        return composition

    def _start_current_wave(self):
        if self.current_wave_index >= len(self.waves):
            self.finished_spawning = True
            self.active = False
            self.wave_state = "done"
            self._clear_group_debug()
            return

        wave = self.waves[self.current_wave_index]
        self.enemies_left_to_spawn = wave["count"]
        self.wave_timer = 0.0
        flavour_tag = FLAVOUR_LABELS.get(wave.get("flavour", "mixed"), "")
        if wave.get("groups"):
            self.wave_mode = "grouped"
            self.old_spawn_queue_length = len(wave.get("spawn_queue", []))
            self.legacy_clearing_gate_active = False
            self.current_group_index = 0
            for group in wave["groups"]:
                group["state"] = "not_started"
                group["spawned_count"] = 0
                group["living_ids"] = set()
                group["elapsed"] = 0.0
                group["spawn_timer"] = group.get("start_delay", 0.0)
            self.wave_state = "group_spawning"
            self.next_group_release_reason = "wave_start"
            self._start_group(wave, 0)
            self.wave_message = f"{wave['label']}: {wave['count']} enemies in {len(wave['groups'])} groups."
            return

        self.spawn_delay = wave["delay"]
        self.spawn_burst_size = wave["burst"]
        self.spawn_timer = 0.1
        self.wave_state = "spawning"
        self.wave_mode = "legacy"
        self.old_spawn_queue_length = len(wave.get("spawn_queue", []))
        self.legacy_clearing_gate_active = False
        self._clear_group_debug()
        self.wave_message = f"{wave['label']}{flavour_tag}: {wave['count']} enemies."

    def update(self, dt, spawn_position_func, enemies_alive=0, enemy_factory=None, prefab_registry=None, living_enemies=None, player_rect=None):
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
            self.legacy_clearing_gate_active = True
            if enemies_alive <= 0:
                self._finish_current_wave_after_clear()
            return spawned

        if self.wave_state == "group_clearing":
            self.legacy_clearing_gate_active = False
            if enemies_alive <= 0:
                self._finish_current_wave_after_clear()
            return spawned

        wave = self.waves[self.current_wave_index] if 0 <= self.current_wave_index < len(self.waves) else None
        if wave is not None and wave.get("groups"):
            return self._update_grouped_wave(dt, wave, spawn_position_func, enemies_alive, enemy_factory, prefab_registry, living_enemies, player_rect)

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
            if enemy_factory is not None:
                spawned.append(enemy_factory(x, y, enemy_type, wave_difficulty))
            elif prefab_registry is not None:
                spawned.append(prefab_registry.spawn_prefab(
                    f"enemy_{enemy_type.name.lower()}",
                    x=x,
                    y=y,
                    difficulty=wave_difficulty,
                ))
            else:
                from entities.enemy import Enemy
                spawned.append(Enemy(x, y, enemy_type=enemy_type, difficulty=wave_difficulty))

        self.enemies_left_to_spawn -= spawn_count
        self.spawn_timer = self.spawn_delay

        if self.enemies_left_to_spawn <= 0:
            self.wave_state = "clearing"

        return spawned

    def _start_group(self, wave, index):
        if index >= len(wave.get("groups", [])):
            self.wave_state = "group_clearing"
            self._clear_group_debug()
            return
        self.current_group_index = index
        group = wave["groups"][index]
        group["state"] = "spawning"
        group["elapsed"] = 0.0
        group["spawn_timer"] = group.get("start_delay", 0.0)
        self.current_group_id = group["id"]
        self.current_group_name = group["name"]
        self.current_group_state = group["state"]
        self.current_group_elapsed = 0.0
        self.current_group_spawned = group["spawned_count"]
        self.current_group_living = 0
        self.current_group_number = index + 1
        self.current_group_total = len(wave.get("groups", []))
        self.wave_mode = "grouped"
        self.old_spawn_queue_length = len(wave.get("spawn_queue", []))
        self.legacy_clearing_gate_active = False

    def _update_grouped_wave(self, dt, wave, spawn_position_func, enemies_alive, enemy_factory, prefab_registry, living_enemies, player_rect):
        spawned = []
        groups = wave.get("groups", [])
        if not groups:
            self.wave_state = "clearing"
            return spawned

        self.wave_timer += dt
        self._refresh_group_living(groups, living_enemies)

        if self.current_group_index >= len(groups):
            self.wave_state = "clearing"
            self._clear_group_debug()
            return spawned

        group = groups[self.current_group_index]
        group["elapsed"] += dt
        self.nearby_pressure_count = self._nearby_pressure_count(living_enemies, player_rect, group)
        self.current_group_saturation_cap = group.get("saturation_cap", ROOM_1_GROUP_SATURATION_CAP)
        self.current_group_hard_cap = group.get("hard_cap", ROOM_1_GROUP_HARD_CAP)
        self.current_group_state = group["state"]
        self.current_group_elapsed = group["elapsed"]
        self.current_group_spawned = group["spawned_count"]
        self.current_group_living = len(group["living_ids"])
        self.current_group_expected_clear_time = group.get("expected_clear_time", "-")
        self.current_group_max_time = group.get("max_release_time", "-")

        if group["state"] == "spawning":
            group["spawn_timer"] -= dt
            if group["spawn_timer"] <= 0 and group["spawned_count"] < group["count"]:
                hard_cap = group.get("hard_cap", ROOM_1_GROUP_HARD_CAP)
                allowed_by_cap = max(0, hard_cap - enemies_alive)
                spawn_count = min(group["burst"], group["count"] - group["spawned_count"], allowed_by_cap)
                if spawn_count <= 0:
                    group["spawn_timer"] = 0.08
                    self.next_group_release_reason = "-"
                    self.release_blocked_reason = "blocked_by_hard_cap"
                else:
                    spawned.extend(self._spawn_group_enemies(spawn_count, group, wave, spawn_position_func, enemy_factory, prefab_registry))
                    enemies_alive += len(spawned)
                    group["spawn_timer"] = group["interval"]
            if group["spawned_count"] >= group["count"]:
                group["state"] = "clearing"

        if group["state"] == "clearing":
            reason = self._group_release_reason(group)
            hard_cap = group.get("hard_cap", ROOM_1_GROUP_HARD_CAP)
            can_release = reason is not None and enemies_alive < hard_cap
            if can_release:
                group["state"] = "done"
                self.next_group_release_reason = reason
                self.release_blocked_reason = "-"
                self._start_group(wave, self.current_group_index + 1)
                return spawned
            elif reason is not None:
                self.next_group_release_reason = "-"
                self.release_blocked_reason = "blocked_by_hard_cap" if enemies_alive >= hard_cap else "-"
            else:
                self.next_group_release_reason = "-"
                self.release_blocked_reason = "-"

        if all(group["state"] == "done" for group in groups):
            self.wave_state = "group_clearing"

        self.enemies_left_to_spawn = sum(max(0, group["count"] - group["spawned_count"]) for group in groups)
        self.current_group_state = group["state"] if self.current_group_index < len(groups) else "-"
        self.current_group_spawned = group["spawned_count"] if self.current_group_index < len(groups) else 0
        self.current_group_living = len(group["living_ids"]) if self.current_group_index < len(groups) else 0
        return spawned

    def _finish_current_wave_after_clear(self):
        if self.current_wave_index >= len(self.waves) - 1:
            self.finished_spawning = True
            self.active = False
            self.wave_state = "done"
            self.wave_message = f"Wave {self.current_wave_index + 1} cleared."
        else:
            self.wave_state = "break"
            self.wave_timer = WAVE_BREAK_TIME
            self.wave_message = f"Wave {self.current_wave_index + 1} cleared."

    def _spawn_group_enemies(self, spawn_count, group, wave, spawn_position_func, enemy_factory, prefab_registry):
        spawned = []
        wave_difficulty = wave.get("enemy_difficulty_override")
        if wave_difficulty is None:
            wave_difficulty = self.difficulty + wave.get("difficulty_bonus", 0.0)
        for _ in range(spawn_count):
            enemy_type = group["spawn_queue"][group["spawned_count"]]
            x, y = spawn_position_func()
            if enemy_factory is not None:
                enemy = enemy_factory(x, y, enemy_type, wave_difficulty)
            elif prefab_registry is not None:
                enemy = prefab_registry.spawn_prefab(
                    f"enemy_{enemy_type.name.lower()}",
                    x=x,
                    y=y,
                    difficulty=wave_difficulty,
                )
            else:
                from entities.enemy import Enemy
                enemy = Enemy(x, y, enemy_type=enemy_type, difficulty=wave_difficulty)
            setattr(enemy, "wave_group_id", group["id"])
            setattr(enemy, "wave_group_name", group["name"])
            group["living_ids"].add(id(enemy))
            group["spawned_count"] += 1
            spawned.append(enemy)
        return spawned

    def _refresh_group_living(self, groups, living_enemies):
        if living_enemies is None:
            return
        living_ids = {id(enemy) for enemy in living_enemies}
        for group in groups:
            group["living_ids"].intersection_update(living_ids)

    def _group_release_reason(self, group):
        living = len(group["living_ids"])
        if group["elapsed"] >= group.get("max_release_time", 999):
            return "max_time"
        if group["elapsed"] >= group.get("expected_clear_time", 999):
            return "expected_time"
        if living <= group.get("alive_threshold", 0):
            return "early_clear"
        return None

    def _nearby_pressure_count(self, living_enemies, player_rect, group):
        if living_enemies is None or player_rect is None:
            return group.get("pressure_floor", ROOM_1_PRESSURE_FLOOR) + 1
        center = getattr(player_rect, "center", None)
        if center is None:
            return group.get("pressure_floor", ROOM_1_PRESSURE_FLOOR) + 1
        px, py = center
        normal_radius_sq = group.get("pressure_radius", ROOM_1_PRESSURE_RADIUS) ** 2
        ranged_radius_sq = group.get("ranged_pressure_radius", ROOM_1_RANGED_PRESSURE_RADIUS) ** 2
        count = 0
        for enemy in living_enemies:
            if not getattr(enemy, "alive", True):
                continue
            rect = getattr(enemy, "rect", None)
            if rect is None:
                continue
            dx = rect.centerx - px
            dy = rect.centery - py
            distance_sq = dx * dx + dy * dy
            enemy_type = getattr(enemy, "type", getattr(enemy, "enemy_type", None))
            type_name = getattr(enemy_type, "name", "")
            radius_sq = ranged_radius_sq if type_name.startswith("RANGED") or type_name == "HUNTER" else normal_radius_sq
            if distance_sq <= radius_sq:
                count += 1
        return count

    def _clear_group_debug(self):
        self.current_group_state = "-"
        self.current_group_elapsed = 0.0
        self.current_group_spawned = 0
        self.current_group_living = 0
        self.current_group_expected_clear_time = "-"
        self.current_group_max_time = "-"
        self.current_group_number = 0
        self.current_group_total = 0
        self.nearby_pressure_count = 0
        self.current_group_saturation_cap = "-"
        self.current_group_hard_cap = "-"
        self.release_blocked_reason = "-"
        self.current_group_id = "-"
        self.current_group_name = "-"
        self.next_group_release_reason = "-"

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
