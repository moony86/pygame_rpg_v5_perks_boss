import random
from systems.object_catalog import definition as object_definition

from definitions.perk_definitions import PERK_DEFINITIONS, PERK_SYNERGY_PAIRS
from settings import PERK_PICK_LIMIT

OFFICIAL_STARTER_BUILDS = ("Gunslinger", "Ninja", "Engineer", "Vampire")
STARTER_BUILD_CARDS = {
    "Gunslinger": "rapid_fire",
    "Ninja": "phantom_step",
    "Engineer": "impact_drive",
    "Vampire": "sanguine_rounds",
}
PERK_REROLL_GOLD_COST = 150
STARTER_AFFINITY_BONUS = 2


def apply_split_shot(player):
    player.projectile_count = min(7, player.projectile_count + 1)
    player.spread_degrees = min(42, player.spread_degrees + 8)


def apply_legendary_split(player):
    player.projectile_count = min(8, player.projectile_count + 1)
    player.spread_degrees = min(48, player.spread_degrees + 6)
    player.split_damage_multiplier = getattr(player, "split_damage_multiplier", 1.0) + 0.25


def reduce_max_health(player, amount, floor=30):
    player.max_health = max(floor, player.max_health - amount)
    player.health = min(player.health, player.max_health)


def add_attr(attr, amount):
    return lambda player: setattr(player, attr, getattr(player, attr) + amount)


def chain(*functions):
    def apply(player):
        for function in functions:
            function(player)
    return apply


def apply_explosive_rounds(player):
    taken = player.perk_counts.get("explosive_rounds", 0)
    player.explosive_rounds = True
    if taken == 0:
        player.explosion_radius = 95
        player.explosion_splash_ratio = 1 / 3
        player.fire_rate_multiplier = max(0.40, player.fire_rate_multiplier - 0.15)
    elif taken == 1:
        player.explosion_radius = 115
    elif taken == 2:
        player.explosion_splash_ratio = 0.40


def apply_legendary_explosive_rounds(player):
    player.explosive_rounds = True
    player.explosion_radius = 130
    player.explosion_splash_ratio = 0.45
    player.fire_rate_multiplier += 0.15


def refresh_engineer_machines(player):
    gun_level = max(
        getattr(player, "engineer_gun_level", 0),
        getattr(player, "engineer_impact_level", 0),
        getattr(player, "engineer_kinetic_level", 0),
    )
    overclock = getattr(player, "engineer_overclock_level", 0)
    if gun_level > 0:
        player.engineer_helper_enabled = True
        player.engineer_gun_count = 2 if gun_level >= 4 else 1
        player.engineer_helper_damage = [0, 18, 20, 28, 34][min(4, gun_level)]
        player.engineer_helper_projectile_speed = [0, 700, 720, 790, 820][min(4, gun_level)]
        player.engineer_gun_burst_count = 2 if 2 <= gun_level < 4 else 1
        player.engineer_helper_cooldown = max(0.34, [0.0, 1.45, 1.18, 1.05, 0.92][min(4, gun_level)] - 0.12 * overclock)
        player.engineer_gun_range = 500

    blade_level = getattr(player, "engineer_blade_level", 0)
    player.engineer_blade_count = [0, 2, 3, 4, 4][min(4, blade_level)]
    player.engineer_blade_damage = [0, 16, 18, 22, 24][min(4, blade_level)]
    player.engineer_blade_radius = [0, 78, 88, 104, 108][min(4, blade_level)]
    player.engineer_blade_overdrive_radius_bonus = 26 if blade_level >= 4 else 0
    player.engineer_blade_overdrive_damage_bonus = 12 if blade_level >= 4 else 0
    player.engineer_blade_overdrive_duration = 1.8 if blade_level >= 4 else 0.0
    player.engineer_blade_overdrive_cooldown = max(4.8, 6.6 - 0.25 * overclock) if blade_level >= 4 else 0.0
    player.engineer_blade_hit_cooldown = max(0.45, [0.0, 0.62, 0.58, 0.54, 0.50][min(4, blade_level)] - 0.03 * overclock)
    player.engineer_blade_orbit_speed = [0.0, 2.6, 3.0, 3.25, 3.35][min(4, blade_level)] + 0.15 * overclock

    bomber_level = getattr(player, "engineer_bomber_level", 0)
    player.engineer_bomber_count = [0, 1, 2, 2, 2][min(4, bomber_level)]
    player.engineer_bomber_damage = [0, 52, 56, 72, 78][min(4, bomber_level)]
    player.engineer_bomber_radius = [0, 82, 88, 108, 112][min(4, bomber_level)]
    player.engineer_bomber_cooldown = max(3.4, [0.0, 5.8, 5.2, 4.65, 4.35][min(4, bomber_level)] - 0.18 * overclock)
    player.engineer_bomber_speed = [0.0, 420, 470, 535, 560][min(4, bomber_level)]
    player.engineer_bomber_max_runs = player.engineer_bomber_count
    player.engineer_airstrike_unlocked = bomber_level >= 4
    player.engineer_airstrike_cooldown = max(22.0, 28.0 - 0.75 * overclock) if bomber_level >= 4 else 0.0
    player.engineer_airstrike_damage = 125 if bomber_level >= 4 else 0
    player.engineer_airstrike_radius = 172 if bomber_level >= 4 else 0


def add_engineer_helper(player, damage=0, cooldown_delta=0.0):
    player.engineer_helper_enabled = True
    if damage >= 42:
        player.engineer_gun_level = max(getattr(player, "engineer_gun_level", 0), 4)
    elif damage >= 34:
        player.engineer_gun_level = max(getattr(player, "engineer_gun_level", 0), 3)
    elif damage >= 24:
        player.engineer_gun_level = max(getattr(player, "engineer_gun_level", 0), 2)
    elif damage > 0:
        player.engineer_gun_level = max(getattr(player, "engineer_gun_level", 0), 1)
    refresh_engineer_machines(player)


def add_engineer_progress(player, attr):
    setattr(player, attr, max(getattr(player, attr, 0), player.perk_counts.get({
        "engineer_impact_level": "impact_drive",
        "engineer_kinetic_level": "kinetic_rounds",
        "engineer_overclock_level": "overclock",
        "engineer_blade_level": "blade_drone",
        "engineer_bomber_level": "bomber_drone",
    }[attr], 0) + 1))
    refresh_engineer_machines(player)


def add_blood_sustain(player, heal=0, max_heal=0):
    player.vampire_kill_heal = max(getattr(player, "vampire_kill_heal", 0), heal)
    player.vampire_elite_bonus_heal = max(getattr(player, "vampire_elite_bonus_heal", 0), max_heal)


def add_vampire_feed(player, blood=0, hit_feed=0, boss_hit_feed=0, max_blood=0, damage_bonus=0):
    player.vampire_blood_per_kill = max(getattr(player, "vampire_blood_per_kill", 0), blood)
    player.vampire_blood_on_hit = max(getattr(player, "vampire_blood_on_hit", 0), hit_feed)
    player.vampire_blood_on_boss_hit = max(getattr(player, "vampire_blood_on_boss_hit", 0), boss_hit_feed)
    player.vampire_max_blood = max(getattr(player, "vampire_max_blood", 0), max_blood)
    player.vampire_blood_damage_bonus = max(getattr(player, "vampire_blood_damage_bonus", 0), damage_bonus)


def refresh_vampire_ecosystem(player):
    wound_level = getattr(player, "vampire_wound_level", 0)
    player.vampire_wound_stacks_per_hit = 1 if wound_level > 0 else 0
    player.vampire_wound_max_stacks = [0, 2, 2, 3, 3][min(4, wound_level)]
    player.vampire_wound_duration = [0.0, 4.5, 5.0, 5.5, 6.0][min(4, wound_level)]
    player.vampire_orb_drop_chance = [0.0, 0.65, 0.85, 1.0, 1.0][min(4, wound_level)]
    player.vampire_orb_value = [0, 1, 1, 1, 2][min(4, wound_level)]

    sustain_level = getattr(player, "vampire_sustain_level", 0)
    player.vampire_feast_unlocked = sustain_level > 0
    player.vampire_orb_heal = [0, 1, 1, 2, 2][min(4, sustain_level)]
    player.vampire_feast_threshold = max(1, [999, 7, 7, 6, 6][min(4, sustain_level)])
    player.vampire_feast_duration = [0.0, 4.5, 5.0, 5.5, 6.0][min(4, sustain_level)]

    core_level = getattr(player, "vampire_core_level", 0)
    if core_level > 0:
        player.vampire_orb_attract_radius = [0, 112, 126, 138, 150][min(4, core_level)]
        player.vampire_blood_capacity_bonus = [0, 1, 2, 3, 4][min(4, core_level)]

    bat_level = getattr(player, "vampire_bat_level", 0)
    player.vampire_bat_enabled = bat_level > 0
    player.vampire_bat_damage = [0, 18, 24, 30, 38][min(4, bat_level)]
    player.vampire_bat_speed = [0, 620, 720, 820, 900][min(4, bat_level)]
    player.vampire_bat_feed_value = [0, 1, 1, 2, 2][min(4, bat_level)]
    player.vampire_bat_cooldown = [0.0, 2.2, 1.9, 1.6, 1.2][min(4, bat_level)]
    player.vampire_bat_chain_cap = [0, 2, 2, 3, 4][min(4, bat_level)]

    trail_level = getattr(player, "vampire_trail_level", 0)
    player.vampire_trail_enabled = trail_level > 0
    player.vampire_trail_harvest_cap = [0, 1, 1, 2, 3][min(4, trail_level)]
    player.vampire_trail_harvest_value = [0, 1, 1, 1, 2][min(4, trail_level)]
    player.vampire_trail_interval = [0.0, 0.90, 0.80, 0.70, 0.60][min(4, trail_level)]
    player.vampire_trail_radius = [0, 64, 72, 80, 88][min(4, trail_level)]
    player.vampire_blood_moon_unlocked = trail_level >= 4


def add_vampire_progress(player, attr):
    key = {
        "vampire_wound_level": "sanguine_rounds",
        "vampire_sustain_level": "battle_recovery",
        "vampire_core_level": "vital_core",
        "vampire_bat_level": "blood_bat",
        "vampire_trail_level": "blood_trail",
    }[attr]
    setattr(player, attr, max(getattr(player, attr, 0), player.perk_counts.get(key, 0) + 1))
    refresh_vampire_ecosystem(player)


def add_dash_strike(player, damage=0, cooldown_restore=0.0, refund_cap=0.0):
    player.dash_strike_damage = max(getattr(player, "dash_strike_damage", 0), damage)
    player.dash_strike_cooldown_restore = max(getattr(player, "dash_strike_cooldown_restore", 0.0), cooldown_restore)
    player.dash_refund_cap = max(getattr(player, "dash_refund_cap", 0.0), refund_cap)
    player.ninja_momentum_enabled = True
    if hasattr(player, "enable_ninja_dash_charges"):
        player.enable_ninja_dash_charges()


def add_ninja_momentum(player, gain=0.0, max_momentum=0.0):
    player.ninja_momentum_enabled = True
    player.ninja_momentum_gain = max(getattr(player, "ninja_momentum_gain", 0.0), gain)
    player.ninja_momentum_max = max(getattr(player, "ninja_momentum_max", 0.0), max_momentum)


def add_shadow_shuriken(player, damage=0, speed=0, refund_cap=0.0):
    player.ninja_shuriken_damage = max(getattr(player, "ninja_shuriken_damage", 0), damage)
    player.ninja_shuriken_speed = max(getattr(player, "ninja_shuriken_speed", 0), speed)
    add_ninja_momentum(player, gain=0.15, max_momentum=1.0)
    add_dash_strike(player, cooldown_restore=0.22, refund_cap=refund_cap)


def apply_starter_build_loadout(player, build):
    if build == "Ninja" and hasattr(player, "switch_weapon"):
        if hasattr(player, "enable_ninja_dash_charges"):
            player.enable_ninja_dash_charges()
        player.switch_weapon("pistol")
        player.last_upgrade_text = "Ninja: dash charges unlocked (Pistol demo)"


PERK_EFFECTS = {
    "rapid_fire": (add_attr("fire_rate_multiplier", 0.30), add_attr("fire_rate_multiplier", 0.55)),
    "power_rounds": (
        chain(add_attr("damage_bonus", 14), lambda player: setattr(player, "fire_rate_multiplier", max(0.45, player.fire_rate_multiplier - 0.10))),
        chain(add_attr("damage_bonus", 32), add_attr("fire_rate_multiplier", 0.12)),
    ),
    "hollow_point": (
        chain(add_attr("damage_bonus", 20), lambda player: setattr(player, "pierce", 0)),
        chain(add_attr("damage_bonus", 45), lambda player: setattr(player, "pierce", 0), add_attr("crit_multiplier", 0.25)),
    ),
    "glass_cannon": (
        chain(add_attr("damage_bonus", 25), lambda player: add_vampire_feed(player, blood=1, max_blood=8, damage_bonus=0.04), lambda player: reduce_max_health(player, 40)),
        chain(add_attr("damage_bonus", 60), lambda player: add_vampire_feed(player, blood=2, max_blood=12, damage_bonus=0.08), lambda player: reduce_max_health(player, 40)),
    ),
    "split_shot": (apply_split_shot, apply_legendary_split),
    "needle_rounds": (add_attr("pierce", 1), chain(add_attr("pierce", 3), add_attr("damage_bonus", 8))),
    "kinetic_rounds": (
        chain(add_attr("damage_bonus", 8), add_attr("projectile_speed_bonus", 70), lambda player: add_engineer_progress(player, "engineer_kinetic_level")),
        chain(add_attr("damage_bonus", 24), add_attr("projectile_speed_bonus", 180), lambda player: add_engineer_progress(player, "engineer_kinetic_level")),
    ),
    "critical_spark": (add_attr("crit_chance", 0.30), chain(add_attr("crit_chance", 0.80), add_attr("crit_multiplier", 0.35))),
    "overclock": (
        chain(add_attr("fire_rate_multiplier", 0.40), lambda player: add_engineer_progress(player, "engineer_overclock_level"), lambda player: add_ninja_momentum(player, gain=0.13, max_momentum=0.8), lambda player: reduce_max_health(player, 15)),
        chain(add_attr("fire_rate_multiplier", 0.70), lambda player: add_engineer_progress(player, "engineer_overclock_level"), lambda player: add_ninja_momentum(player, gain=0.20, max_momentum=1.0), lambda player: setattr(player, "skill_cooldown_multiplier", max(0.55, getattr(player, "skill_cooldown_multiplier", 1.0) * 0.80))),
    ),
    "explosive_rounds": (apply_explosive_rounds, apply_legendary_explosive_rounds),
    "impact_drive": (
        chain(add_attr("knockback_power", 0.45), lambda player: add_engineer_progress(player, "engineer_impact_level")),
        chain(add_attr("knockback_power", 0.88), add_attr("damage_bonus", 8), lambda player: add_engineer_progress(player, "engineer_impact_level")),
    ),
    "blade_drone": (
        lambda player: add_engineer_progress(player, "engineer_blade_level"),
        lambda player: add_engineer_progress(player, "engineer_blade_level"),
    ),
    "bomber_drone": (
        lambda player: add_engineer_progress(player, "engineer_bomber_level"),
        lambda player: add_engineer_progress(player, "engineer_bomber_level"),
    ),
    "vital_core": (
        chain(add_attr("max_health", 48), lambda player: add_vampire_feed(player, max_blood=8), lambda player: add_vampire_progress(player, "vampire_core_level"), lambda player: player.heal(24)),
        chain(add_attr("max_health", 110), lambda player: add_vampire_feed(player, max_blood=14), lambda player: add_vampire_progress(player, "vampire_core_level"), lambda player: player.heal(9999)),
    ),
    "battle_recovery": (
        chain(add_attr("regen_on_room_clear", 24), lambda player: add_blood_sustain(player, heal=3, max_heal=6), lambda player: add_vampire_feed(player, blood=2, max_blood=10), lambda player: add_vampire_progress(player, "vampire_sustain_level")),
        chain(add_attr("regen_on_room_clear", 70), add_attr("max_health", 35), lambda player: add_blood_sustain(player, heal=8, max_heal=16), lambda player: add_vampire_feed(player, blood=4, max_blood=16), lambda player: add_vampire_progress(player, "vampire_sustain_level"), lambda player: player.heal(35)),
    ),
    "scout_boots": (
        chain(add_attr("speed", 30), lambda player: add_ninja_momentum(player, gain=0.12, max_momentum=0.75), lambda player: add_dash_strike(player, damage=18, refund_cap=0.75)),
        chain(add_attr("speed", 70), lambda player: add_ninja_momentum(player, gain=0.18, max_momentum=1.0), lambda player: add_dash_strike(player, damage=34, cooldown_restore=0.65, refund_cap=1.4), lambda player: setattr(player, "dash_cooldown_timer", 0.0)),
    ),
    "phantom_step": (
        chain(add_attr("speed", 20), lambda player: add_ninja_momentum(player, gain=0.10, max_momentum=0.9), lambda player: add_dash_strike(player, damage=object_definition('sword')['dash_damage'], cooldown_restore=0.18, refund_cap=1.0), lambda player: reduce_max_health(player, 20)),
        chain(add_attr("speed", 50), lambda player: add_ninja_momentum(player, gain=0.16, max_momentum=1.0), lambda player: add_dash_strike(player, damage=48, cooldown_restore=0.85, refund_cap=1.6), lambda player: setattr(player, "dash_invuln_bonus", getattr(player, "dash_invuln_bonus", 0.0) + 0.20)),
    ),
    "shadow_shuriken": (
        lambda player: add_shadow_shuriken(player, damage=16, speed=760, refund_cap=1.1),
        lambda player: add_shadow_shuriken(player, damage=38, speed=920, refund_cap=1.9),
    ),
    "sanguine_rounds": (
        chain(lambda player: add_vampire_feed(player, hit_feed=1, boss_hit_feed=1, max_blood=10, damage_bonus=0.03), lambda player: add_vampire_progress(player, "vampire_wound_level")),
        chain(lambda player: add_vampire_feed(player, hit_feed=2, boss_hit_feed=2, max_blood=16, damage_bonus=0.07), lambda player: add_vampire_progress(player, "vampire_wound_level")),
    ),
    "blood_bat": (
        lambda player: add_vampire_progress(player, "vampire_bat_level"),
        lambda player: add_vampire_progress(player, "vampire_bat_level"),
    ),
    "blood_trail": (
        lambda player: add_vampire_progress(player, "vampire_trail_level"),
        lambda player: add_vampire_progress(player, "vampire_trail_level"),
    ),
}


def _build_perks():
    perks = []
    for definition in PERK_DEFINITIONS:
        perk = dict(definition)
        apply_effect, legendary_effect = PERK_EFFECTS[perk["key"]]
        perk["apply"] = apply_effect
        perk["legendary_apply"] = legendary_effect
        perks.append(perk)
    return perks


PERKS = _build_perks()
_SYNERGY_PAIRS = PERK_SYNERGY_PAIRS


def _owned_build_counts(player):
    build_counts = {}
    if player is None:
        return build_counts
    for definition in PERKS:
        count = player.perk_counts.get(definition["key"], 0)
        if count <= 0:
            continue
        build = definition.get("build", "Shared/Utility")
        if build != "Shared/Utility":
            build_counts[build] = build_counts.get(build, 0) + count
    return build_counts


def _primary_build(perk):
    build = perk.get("build", "Shared/Utility")
    return "Shared" if build == "Shared/Utility" else build


def _hybrid_builds(perk):
    roles = list(perk.get("build_roles", [perk.get("build", "Shared/Utility")]))
    primary = perk.get("build", "Shared/Utility")
    return [("Shared" if role == "Shared/Utility" else role) for role in roles if role != primary]


def _synergy_label(new_perk, player):
    if player is None:
        return ""
    build_counts = _owned_build_counts(player)
    if not build_counts:
        return ""
    preferred_build = max(sorted(build_counts), key=lambda build: build_counts[build])
    roles = new_perk.get("build_roles", [new_perk.get("build", "Shared/Utility")])
    if preferred_build not in roles:
        return ""

    taken_tags = set()
    for perk in PERKS:
        if player.perk_counts.get(perk["key"], 0) > 0:
            taken_tags.update(perk.get("tags", []))

    new_tags = set(new_perk.get("tags", []))
    for tag_a, tag_b, label in _SYNERGY_PAIRS:
        if tag_a <= new_tags and tag_b <= taken_tags:
            return f"{preferred_build.upper()} {label}"
        if tag_b <= new_tags and tag_a <= taken_tags:
            return f"{preferred_build.upper()} {label}"
    return ""


def _build_affinity_score(perk, player):
    if player is None:
        return 0
    build_counts = _owned_build_counts(player)
    starter_build = getattr(player, "starter_build", "")
    taken_tags = set()
    for definition in PERKS:
        count = player.perk_counts.get(definition["key"], 0)
        if count <= 0:
            continue
        taken_tags.update(definition.get("tags", []))
    score = 0
    roles = perk.get("build_roles", [perk.get("build", "Shared/Utility")])
    if build_counts:
        preferred_build = max(sorted(build_counts), key=lambda build: build_counts[build])
        if preferred_build in roles:
            score += 3
    if starter_build:
        if starter_build in roles:
            score += STARTER_AFFINITY_BONUS
        elif "Shared/Utility" in roles:
            score += 1
    if "Shared/Utility" in roles:
        score += 1
    if set(perk.get("tags", [])) & taken_tags:
        score += 1
    return score


def _perk_by_key(key):
    for perk in PERKS:
        if perk["key"] == key:
            return perk
    raise KeyError(f"Missing starter perk definition: {key}")


class PerkSystem:
    def __init__(self):
        self.current_options = []

    def _available_perks(self, player):
        if player is None:
            return PERKS
        return [
            perk for perk in PERKS
            if player.perk_counts.get(perk["key"], 0) < PERK_PICK_LIMIT
        ]

    def _option_for_player(self, perk, player):
        option = dict(perk)
        taken = player.perk_counts.get(perk["key"], 0) if player is not None else 0
        option["taken"] = taken
        option["limit"] = PERK_PICK_LIMIT
        option["legendary"] = taken >= 3
        option["synergy"] = _synergy_label(perk, player) if player is not None else ""
        option["build"] = perk.get("build", "Shared/Utility")
        option["build_label"] = _primary_build(perk).upper()
        option["hybrid_builds"] = _hybrid_builds(perk)
        if option["legendary"]:
            option["name"] = "Legendary " + perk["name"]
            option["desc"] = perk.get("legendary_desc", perk["desc"])
        return option

    def roll_options(self, player=None, count=3):
        available = self._available_perks(player)
        if not available:
            self.current_options = []
            return []

        picked = []
        seen_tag_combos = set()
        shuffled = random.sample(available, k=len(available))
        shuffled.sort(key=lambda perk: _build_affinity_score(perk, player), reverse=True)
        for perk in shuffled:
            tags = frozenset(perk.get("tags", []))
            if tags not in seen_tag_combos:
                picked.append(perk)
                seen_tag_combos.add(tags)
            if len(picked) == count:
                break

        if len(picked) < count:
            picked_ids = {id(perk) for perk in picked}
            remainder = [perk for perk in shuffled if id(perk) not in picked_ids]
            picked.extend(remainder[:count - len(picked)])

        self.current_options = [self._option_for_player(perk, player) for perk in picked]
        return self.current_options

    def roll_starter_options(self, player=None, count=3):
        starters = {build: _perk_by_key(key) for build, key in STARTER_BUILD_CARDS.items()}
        builds = list(OFFICIAL_STARTER_BUILDS)
        shown_builds = random.sample(builds, k=min(count, len(builds)))
        missing = [build for build in builds if build not in shown_builds]
        if player is not None:
            player.starter_choice_active = True
            player.starter_missing_build = missing[0] if missing else ""
            player.starter_free_reroll_used = False
        self.current_options = [self._option_for_player(starters[build], player) for build in shown_builds]
        for option in self.current_options:
            option["starter"] = True
        return self.current_options

    def reroll_labels(self, player):
        labels = []
        for _ in self.current_options:
            if getattr(player, "starter_choice_active", False):
                labels.append("FREE STARTER REROLL" if not getattr(player, "starter_free_reroll_used", False) else "NO REROLL")
            elif getattr(player, "reroll_tokens", 0) > 0:
                labels.append("REROLL: 1 TOKEN")
            elif getattr(player, "gold", 0) >= PERK_REROLL_GOLD_COST:
                labels.append(f"REROLL: {PERK_REROLL_GOLD_COST} GOLD")
            else:
                labels.append("NO REROLL")
        return labels

    def _replacement_option(self, player, index):
        if index < 0 or index >= len(self.current_options):
            return None
        current_key = self.current_options[index]["key"]
        visible_keys = {option["key"] for slot, option in enumerate(self.current_options) if slot != index}
        candidates = [
            perk for perk in self._available_perks(player)
            if perk["key"] != current_key and perk["key"] not in visible_keys
        ]
        if not candidates:
            return None
        shuffled = random.sample(candidates, k=len(candidates))
        shuffled.sort(key=lambda perk: _build_affinity_score(perk, player), reverse=True)
        return self._option_for_player(shuffled[0], player)

    def reroll_option(self, player, index):
        if index < 0 or index >= len(self.current_options):
            return False, "No reroll slot."
        if getattr(player, "starter_choice_active", False):
            if getattr(player, "starter_free_reroll_used", False):
                return False, "Starter reroll already used."
            missing_build = getattr(player, "starter_missing_build", "")
            if not missing_build:
                return False, "No starter replacement available."
            current_build = self.current_options[index].get("build")
            replacement = self._option_for_player(_perk_by_key(STARTER_BUILD_CARDS[missing_build]), player)
            replacement["starter"] = True
            self.current_options[index] = replacement
            player.starter_missing_build = current_build if current_build in OFFICIAL_STARTER_BUILDS else ""
            player.starter_free_reroll_used = True
            player.total_rerolls_used += 1
            return True, f"Starter reroll: {missing_build}"

        replacement = self._replacement_option(player, index)
        if replacement is None:
            return False, "No valid reroll option."

        if getattr(player, "reroll_tokens", 0) > 0:
            player.reroll_tokens -= 1
            paid_by = "token"
        elif getattr(player, "gold", 0) >= PERK_REROLL_GOLD_COST and player.spend_gold(PERK_REROLL_GOLD_COST):
            player.reroll_gold_spent += PERK_REROLL_GOLD_COST
            paid_by = "gold"
        else:
            return False, f"Need 1 token or {PERK_REROLL_GOLD_COST} gold."

        self.current_options[index] = replacement
        player.total_rerolls_used += 1
        return True, f"Rerolled with {paid_by}: {replacement['name']}"

    def apply(self, player, index):
        if index < 0 or index >= len(self.current_options):
            return None
        perk = self.current_options[index]
        key = perk["key"]
        taken = player.perk_counts.get(key, 0)
        if taken >= PERK_PICK_LIMIT:
            return None
        if perk.get("legendary", False):
            perk.get("legendary_apply", perk["apply"])(player)
        else:
            perk["apply"](player)
        player.perk_counts[key] = taken + 1
        player.last_upgrade_text = f"{perk['name']} {player.perk_counts[key]}/{PERK_PICK_LIMIT}"
        if getattr(player, "starter_choice_active", False):
            build = perk.get("build", "")
            player.starter_build = build if build in OFFICIAL_STARTER_BUILDS else ""
            apply_starter_build_loadout(player, player.starter_build)
            player.starter_choice_active = False
            player.starter_missing_build = ""
        player.perk_choices_made = getattr(player, "perk_choices_made", 0) + 1
        self.current_options = []
        return perk
