import random

from settings import PERK_PICK_LIMIT


def apply_split_shot(player):
    player.projectile_count = min(7, player.projectile_count + 1)
    player.spread_degrees = min(42, player.spread_degrees + 8)


def apply_legendary_split(player):
    player.projectile_count = min(8, player.projectile_count + 1)
    player.spread_degrees = min(48, player.spread_degrees + 6)
    player.split_damage_multiplier = getattr(player, "split_damage_multiplier", 1.0) + 0.25


PERKS = [
    {
        "key": "rapid_fire",
        "name": "Rapid Fire",
        "desc": "+30% Fire Rate",
        "legendary_desc": "+55% Fire Rate, no downside",
        "apply": lambda p: setattr(p, "fire_rate_multiplier", p.fire_rate_multiplier + 0.30),
        "legendary_apply": lambda p: setattr(p, "fire_rate_multiplier", p.fire_rate_multiplier + 0.55),
    },
    {
        "key": "heavy_rounds",
        "name": "Heavy Rounds",
        "desc": "+14 Damage, -10% Fire Rate",
        "legendary_desc": "+32 Damage, restores fire rate",
        "apply": lambda p: (setattr(p, "damage_bonus", p.damage_bonus + 14), setattr(p, "fire_rate_multiplier", max(0.45, p.fire_rate_multiplier - 0.10))),
        "legendary_apply": lambda p: (setattr(p, "damage_bonus", p.damage_bonus + 32), setattr(p, "fire_rate_multiplier", p.fire_rate_multiplier + 0.12)),
    },
    {
        "key": "power_core",
        "name": "Power Core",
        "desc": "+12 Damage",
        "legendary_desc": "+35 Damage",
        "apply": lambda p: setattr(p, "damage_bonus", p.damage_bonus + 12),
        "legendary_apply": lambda p: setattr(p, "damage_bonus", p.damage_bonus + 35),
    },
    {
        "key": "split_shot",
        "name": "Split Shot",
        "desc": "+1 Projectile, lower per-shot damage",
        "legendary_desc": "+1 Projectile, restores split damage",
        "apply": apply_split_shot,
        "legendary_apply": apply_legendary_split,
    },
    {
        "key": "needle_rounds",
        "name": "Needle Rounds",
        "desc": "+1 Pierce",
        "legendary_desc": "+3 Pierce, +8 Damage",
        "apply": lambda p: setattr(p, "pierce", p.pierce + 1),
        "legendary_apply": lambda p: (setattr(p, "pierce", p.pierce + 3), setattr(p, "damage_bonus", p.damage_bonus + 8)),
    },
    {
        "key": "scout_boots",
        "name": "Scout Boots",
        "desc": "+30 Move Speed",
        "legendary_desc": "+70 Move Speed, faster dash recovery",
        "apply": lambda p: setattr(p, "speed", p.speed + 30),
        "legendary_apply": lambda p: (setattr(p, "speed", p.speed + 70), setattr(p, "dash_cooldown_timer", 0.0)),
    },
    {
        "key": "vital_core",
        "name": "Vital Core",
        "desc": "+48 Max HP and heal 24",
        "legendary_desc": "+110 Max HP and full heal",
        "apply": lambda p: (setattr(p, "max_health", p.max_health + 48), p.heal(24)),
        "legendary_apply": lambda p: (setattr(p, "max_health", p.max_health + 110), p.heal(9999)),
    },
    {
        "key": "critical_spark",
        "name": "Critical Spark",
        "desc": "+30% Critical Chance",
        "legendary_desc": "+80% Critical Chance, +0.35 crit damage",
        "apply": lambda p: setattr(p, "crit_chance", p.crit_chance + 0.30),
        "legendary_apply": lambda p: (setattr(p, "crit_chance", p.crit_chance + 0.80), setattr(p, "crit_multiplier", p.crit_multiplier + 0.35)),
    },
    {
        "key": "kinetic_rounds",
        "name": "Kinetic Rounds",
        "desc": "+8 Damage, +70 Shot Speed",
        "legendary_desc": "+24 Damage, +180 Shot Speed",
        "apply": lambda p: (setattr(p, "damage_bonus", p.damage_bonus + 8), setattr(p, "projectile_speed_bonus", p.projectile_speed_bonus + 70)),
        "legendary_apply": lambda p: (setattr(p, "damage_bonus", p.damage_bonus + 24), setattr(p, "projectile_speed_bonus", p.projectile_speed_bonus + 180)),
    },
    {
        "key": "battle_recovery",
        "name": "Battle Recovery",
        "desc": "+24 Heal after clearing rooms",
        "legendary_desc": "+70 room heal, +35 Max HP",
        "apply": lambda p: setattr(p, "regen_on_room_clear", p.regen_on_room_clear + 24),
        "legendary_apply": lambda p: (setattr(p, "regen_on_room_clear", p.regen_on_room_clear + 70), setattr(p, "max_health", p.max_health + 35), p.heal(35)),
    },
]


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
        if option["legendary"]:
            option["name"] = "Legendary " + perk["name"]
            option["desc"] = perk.get("legendary_desc", perk["desc"])
        return option

    def roll_options(self, player=None, count=3):
        available = self._available_perks(player)
        picked = random.sample(available, k=min(count, len(available))) if available else []
        self.current_options = [self._option_for_player(perk, player) for perk in picked]
        return self.current_options

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
        self.current_options = []
        return perk