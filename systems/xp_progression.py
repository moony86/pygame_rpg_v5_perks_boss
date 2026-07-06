EARLY_XP_BASE = 100
EARLY_XP_STEP = 40
EARLY_LINEAR_LEVELS = 9
LATE_XP_MULTIPLIER = 1.10


def xp_required_for_level(current_level):
    """Return XP needed to advance from current_level to current_level + 1."""
    current_level = int(current_level)
    if current_level <= 0:
        raise ValueError("current_level must be positive")
    if current_level <= EARLY_LINEAR_LEVELS:
        return EARLY_XP_BASE + (current_level - 1) * EARLY_XP_STEP

    requirement = EARLY_XP_BASE + (EARLY_LINEAR_LEVELS - 1) * EARLY_XP_STEP
    for _level in range(EARLY_LINEAR_LEVELS + 1, current_level + 1):
        requirement = int(requirement * LATE_XP_MULTIPLIER)
    return requirement


def cumulative_xp_for_level(target_level):
    """Return total XP required to reach target_level from level 1."""
    target_level = int(target_level)
    if target_level <= 1:
        return 0
    return sum(xp_required_for_level(level) for level in range(1, target_level))


def xp_curve_rows(max_level):
    rows = []
    for level in range(1, int(max_level) + 1):
        previous_requirement = 0 if level == 1 else xp_required_for_level(level - 1)
        rows.append((level, previous_requirement, cumulative_xp_for_level(level)))
    return rows
