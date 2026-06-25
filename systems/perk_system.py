import random

from settings import PERK_PICK_LIMIT


PERKS = [
    {
        "key": "rapid_fire",
        "name": "Rapid Fire",
        "desc": "+30% Fire Rate",
        "apply": lambda p: setattr(p, "fire_rate_multiplier", p.fire_rate_multiplier + 0.30),
    },
    {
        "key": "heavy_rounds",
        "name": "Heavy Rounds",
        "desc": "+14 Damage, -10% Fire Rate",
        "apply": lambda p: (setattr(p, "damage_bonus", p.damage_bonus + 14), setattr(p, "fire_rate_multiplier", max(0.45, p.fire_rate_multiplier - 0.10))),
    },
    {
        "key": "split_shot",
        "name": "Split Shot",
        "desc": "+1 Projectile, wider spread",
        "apply": lambda p: (setattr(p, "projectile_count", min(7, p.projectile_count + 1)), setattr(p, "spread_degrees", min(42, p.spread_degrees + 8))),
    },
    {
        "key": "needle_rounds",
        "name": "Needle Rounds",
        "desc": "+1 Pierce",
        "apply": lambda p: setattr(p, "pierce", p.pierce + 1),
    },
    {
        "key": "scout_boots",
        "name": "Scout Boots",
        "desc": "+30 Move Speed",
        "apply": lambda p: setattr(p, "speed", p.speed + 30),
    },
    {
        "key": "vital_core",
        "name": "Vital Core",
        "desc": "+48 Max HP and heal 24",
        "apply": lambda p: (setattr(p, "max_health", p.max_health + 48), p.heal(24)),
    },
    {
        "key": "critical_spark",
        "name": "Critical Spark",
        "desc": "+30% Critical Chance",
        "apply": lambda p: setattr(p, "crit_chance", p.crit_chance + 0.30),
    },
    {
        "key": "kinetic_rounds",
        "name": "Kinetic Rounds",
        "desc": "+8 Damage, +70 Shot Speed",
        "apply": lambda p: (
            setattr(p, "damage_bonus", p.damage_bonus + 8),
            setattr(p, "projectile_speed_bonus", p.projectile_speed_bonus + 70),
        ),
    },
    {
        "key": "battle_recovery",
        "name": "Battle Recovery",
        "desc": "+24 Heal after clearing rooms",
        "apply": lambda p: setattr(p, "regen_on_room_clear", p.regen_on_room_clear + 24),
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

    def roll_options(self, player=None, count=3):
        available = self._available_perks(player)
        options = random.sample(available, k=min(count, len(available))) if available else []
        if player is not None:
            for perk in options:
                perk["taken"] = player.perk_counts.get(perk["key"], 0)
                perk["limit"] = PERK_PICK_LIMIT
        self.current_options = options
        return self.current_options

    def apply(self, player, index):
        if index < 0 or index >= len(self.current_options):
            return None
        perk = self.current_options[index]
        key = perk["key"]
        if player.perk_counts.get(key, 0) >= PERK_PICK_LIMIT:
            return None
        perk["apply"](player)
        player.perk_counts[key] = player.perk_counts.get(key, 0) + 1
        player.last_upgrade_text = f"{perk['name']} {player.perk_counts[key]}/{PERK_PICK_LIMIT}"
        self.current_options = []
        return perk
