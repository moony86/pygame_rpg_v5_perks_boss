from settings import BOSS_XP_REWARD
from systems.xp_progression import cumulative_xp_for_level


ROOM_TARGET_LEVELS = {
    1: 4,
    2: 7,
    3: 10,
    4: 13,
    5: 16,
    6: 20,
    7: 22,
    8: 24,
}

# Conservative expected kill/treasure XP after the lower enemy XP reward.
# These estimates are for budget validation only; actual earned enemy XP still
# comes from CombatSystem and current room wave contents.
ROOM_EXPECTED_ENEMY_XP = {
    1: 320,
    2: 750,
    3: 120,
    4: 175,
    5: 300,
    6: 275,
    7: 650,
    8: 175,
}


def _build_room_completion_xp():
    room_xp = {}
    previous_target_xp = 0
    for room_number in sorted(ROOM_TARGET_LEVELS):
        target_xp = cumulative_xp_for_level(ROOM_TARGET_LEVELS[room_number])
        segment_budget = target_xp - previous_target_xp
        enemy_estimate = ROOM_EXPECTED_ENEMY_XP.get(room_number, 0)
        room_xp[room_number] = max(0, segment_budget - enemy_estimate)
        previous_target_xp = target_xp
    return room_xp


ROOM_COMPLETION_XP = _build_room_completion_xp()


def room_completion_xp(room_number):
    return ROOM_COMPLETION_XP.get(int(room_number), 0)


def expected_cumulative_xp_after_room(room_number):
    total = 0
    for current_room in range(1, int(room_number) + 1):
        total += ROOM_EXPECTED_ENEMY_XP.get(current_room, 0)
        total += ROOM_COMPLETION_XP.get(current_room, 0)
    return total


def expected_cumulative_xp_after_boss():
    return expected_cumulative_xp_after_room(8) + BOSS_XP_REWARD


def award_room_completion_xp(game, position=None):
    room_number = int(getattr(game, "room_number", 0))
    amount = room_completion_xp(room_number)
    if amount <= 0:
        return 0

    awarded = getattr(game, "room_completion_xp_awarded", None)
    if awarded is None:
        awarded = set()
        game.room_completion_xp_awarded = awarded
    if room_number in awarded:
        return 0

    awarded.add(room_number)
    if position is None:
        position = game.player.rect.center

    loot = getattr(game, "loot", None)
    if loot is not None:
        loot.spawn_xp(position, amount)
    else:
        game.player.add_xp(amount)

    events = getattr(game, "events", None)
    if events is not None:
        events.emit("room_completion_xp", {"room_number": room_number, "xp": amount})

    return amount
