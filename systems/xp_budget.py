from settings import BOSS_XP_REWARD, ENEMY_XP_REWARD
from systems.room_system import RoomType
from systems.xp_progression import cumulative_xp_for_level, xp_required_for_level


STAGE_ROOM_TYPES = {
    1: RoomType.COMBAT,
    2: RoomType.COMBAT,
    3: RoomType.TREASURE,
    4: RoomType.ELITE,
    5: RoomType.COMBAT,
    6: RoomType.COMBAT,
    7: RoomType.ELITE,
    8: RoomType.ELITE,
}

STAGE_ROOM_TARGET_LEVELS = {
    1: 5,
    2: 8,
    3: 8,
    4: 12,
    5: 14,
    6: 16,
    7: 18,
    8: 19,
}
STAGE_BOSS_TARGET_LEVEL = STAGE_ROOM_TARGET_LEVELS[8]

ELITE_STAGE_SLOTS = (8, 19, 30, 43, 55)


def stage_room_index(room_index):
    return int(room_index)


def stage_spawn_count(room_index, room_type=None, boss=False):
    if boss:
        return 1
    room_index = stage_room_index(room_index)
    room_type = room_type or STAGE_ROOM_TYPES.get(room_index)
    if room_type == RoomType.TREASURE:
        return 0
    target_count = 34 + room_index * 5
    if room_type == RoomType.ELITE:
        target_count += 10
    return target_count


def stage_elite_spawn_count(room_index, room_type=None, boss=False):
    if boss:
        return 0
    room_index = stage_room_index(room_index)
    room_type = room_type or STAGE_ROOM_TYPES.get(room_index)
    if room_type != RoomType.ELITE:
        return 0
    target_count = stage_spawn_count(room_index, room_type)
    return sum(1 for slot in ELITE_STAGE_SLOTS if slot < target_count)


def stage_expected_enemy_xp(room_index, room_type=None, boss=False):
    if boss:
        return BOSS_XP_REWARD
    total_count = stage_spawn_count(room_index, room_type)
    elite_count = stage_elite_spawn_count(room_index, room_type)
    normal_count = total_count - elite_count
    return normal_count * ENEMY_XP_REWARD + elite_count * ENEMY_XP_REWARD * 5


def _build_stage_expected_enemy_xp():
    return {
        room_index: stage_expected_enemy_xp(
            room_index,
            STAGE_ROOM_TYPES[room_index],
            boss=room_index == 8,
        )
        for room_index in sorted(STAGE_ROOM_TYPES)
    }


STAGE_EXPECTED_ENEMY_XP = _build_stage_expected_enemy_xp()


def _build_stage_completion_xp():
    room_xp = {}
    previous_target_xp = 0
    for room_index in sorted(STAGE_ROOM_TARGET_LEVELS):
        target_xp = cumulative_xp_for_level(STAGE_ROOM_TARGET_LEVELS[room_index])
        segment_budget = target_xp - previous_target_xp
        enemy_estimate = STAGE_EXPECTED_ENEMY_XP.get(room_index, 0)
        room_xp[room_index] = max(0, segment_budget - enemy_estimate)
        previous_target_xp = target_xp
    return room_xp


STAGE_COMPLETION_XP = _build_stage_completion_xp()

# Backwards-compatible names for the quarantined legacy route and older checks.
ROOM_TARGET_LEVELS = STAGE_ROOM_TARGET_LEVELS
ROOM_EXPECTED_ENEMY_XP = STAGE_EXPECTED_ENEMY_XP
ROOM_COMPLETION_XP = STAGE_COMPLETION_XP


def stage_room_completion_xp(room_or_index, room_type=None, boss=None):
    if hasattr(room_or_index, "index"):
        room = room_or_index
        room_index = stage_room_index(room.index)
        boss = bool(getattr(room, "boss", False)) if boss is None else boss
        room_type = getattr(room, "room_type", room_type)
    else:
        room_index = stage_room_index(room_or_index)
        boss = room_index == 8 if boss is None else boss
    if boss and room_index != 8:
        return 0
    return STAGE_COMPLETION_XP.get(room_index, 0)


def room_completion_xp(room_number):
    return stage_room_completion_xp(room_number)


def expected_stage_cumulative_xp_after_room(room_index):
    total = 0
    for current_room in range(1, stage_room_index(room_index) + 1):
        total += STAGE_EXPECTED_ENEMY_XP.get(current_room, 0)
        total += STAGE_COMPLETION_XP.get(current_room, 0)
    return total


def expected_stage_cumulative_xp_after_boss():
    return expected_stage_cumulative_xp_after_room(8)


def expected_cumulative_xp_after_room(room_number):
    return expected_stage_cumulative_xp_after_room(room_number)


def expected_cumulative_xp_after_boss():
    return expected_stage_cumulative_xp_after_boss()


def level_for_cumulative_xp(total_xp):
    level = 1
    remaining = int(total_xp)
    while remaining >= xp_required_for_level(level):
        remaining -= xp_required_for_level(level)
        level += 1
    return level


def expected_stage_level_after_room(room_index):
    return level_for_cumulative_xp(expected_stage_cumulative_xp_after_room(room_index))


def stage_budget_rows():
    rows = []
    for room_index in sorted(STAGE_ROOM_TARGET_LEVELS):
        rows.append(
            {
                "room_index": room_index,
                "room_type": STAGE_ROOM_TYPES[room_index].name,
                "target_level": STAGE_ROOM_TARGET_LEVELS[room_index],
                "enemy_xp": STAGE_EXPECTED_ENEMY_XP[room_index],
                "completion_xp": STAGE_COMPLETION_XP[room_index],
                "expected_total_xp": expected_stage_cumulative_xp_after_room(room_index),
                "expected_level": expected_stage_level_after_room(room_index),
            }
        )
    return rows


def _award_completion_xp(game, key, amount, position, event_payload):
    if amount <= 0:
        return 0

    awarded = getattr(game, "room_completion_xp_awarded", None)
    if awarded is None:
        awarded = set()
        game.room_completion_xp_awarded = awarded
    if key in awarded:
        return 0

    awarded.add(key)
    if position is None:
        position = game.player.rect.center

    loot = getattr(game, "loot", None)
    if loot is not None:
        loot.spawn_xp(position, amount)
    else:
        game.player.add_xp(amount)

    events = getattr(game, "events", None)
    if events is not None:
        events.emit("room_completion_xp", event_payload)

    return amount


def award_stage_room_completion_xp(game, stage_room, position=None):
    room_index = stage_room_index(stage_room.index)
    amount = stage_room_completion_xp(stage_room)
    stage = getattr(game, "stage", None)
    stage_number = getattr(stage, "stage_number", 1)
    key = ("stage", stage_number, room_index)
    payload = {
        "stage_number": stage_number,
        "stage_room_index": room_index,
        "room_type": getattr(stage_room.room_type, "name", str(stage_room.room_type)),
        "boss": bool(getattr(stage_room, "boss", False)),
        "xp": amount,
    }
    return _award_completion_xp(game, key, amount, position, payload)


def award_room_completion_xp(game, position=None):
    stage = getattr(game, "stage", None)
    current_room = getattr(stage, "current_room", None) if stage and getattr(stage, "active", False) else None
    if current_room is not None:
        return award_stage_room_completion_xp(game, current_room, position)

    room_number = int(getattr(game, "room_number", 0))
    amount = room_completion_xp(room_number)
    key = ("legacy", room_number)
    payload = {"room_number": room_number, "xp": amount}
    return _award_completion_xp(game, key, amount, position, payload)
