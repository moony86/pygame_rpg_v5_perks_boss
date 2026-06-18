import random


PERKS = [
    {
        "name": "Rapid Fire",
        "desc": "+20% Fire Rate",
        "apply": lambda p: setattr(p, "fire_rate_multiplier", p.fire_rate_multiplier + 0.20),
    },
    {
        "name": "Heavy Rounds",
        "desc": "+7 Damage, -5% Fire Rate",
        "apply": lambda p: (setattr(p, "damage_bonus", p.damage_bonus + 7), setattr(p, "fire_rate_multiplier", max(0.45, p.fire_rate_multiplier - 0.05))),
    },
    {
        "name": "Split Shot",
        "desc": "+1 Projectile, wider spread",
        "apply": lambda p: (setattr(p, "projectile_count", min(7, p.projectile_count + 1)), setattr(p, "spread_degrees", min(42, p.spread_degrees + 8))),
    },
    {
        "name": "Needle Rounds",
        "desc": "+1 Pierce",
        "apply": lambda p: setattr(p, "pierce", p.pierce + 1),
    },
    {
        "name": "Scout Boots",
        "desc": "+18 Move Speed",
        "apply": lambda p: setattr(p, "speed", p.speed + 18),
    },
    {
        "name": "Vital Core",
        "desc": "+24 Max HP and heal 24",
        "apply": lambda p: (setattr(p, "max_health", p.max_health + 24), p.heal(24)),
    },
    {
        "name": "Critical Spark",
        "desc": "+8% Critical Chance",
        "apply": lambda p: setattr(p, "crit_chance", min(0.55, p.crit_chance + 0.08)),
    },
    {
        "name": "Light Ammo",
        "desc": "+90 Projectile Speed",
        "apply": lambda p: setattr(p, "projectile_speed_bonus", p.projectile_speed_bonus + 90),
    },
    {
        "name": "Battle Recovery",
        "desc": "+12 Heal after clearing rooms",
        "apply": lambda p: setattr(p, "regen_on_room_clear", p.regen_on_room_clear + 12),
    },
]


class PerkSystem:
    def __init__(self):
        self.current_options = []

    def roll_options(self, count=3):
        self.current_options = random.sample(PERKS, k=min(count, len(PERKS)))
        return self.current_options

    def apply(self, player, index):
        if index < 0 or index >= len(self.current_options):
            return None
        perk = self.current_options[index]
        perk["apply"](player)
        player.last_upgrade_text = perk["name"]
        self.current_options = []
        return perk
