from definitions.upgrade_definitions import (
    UPGRADE_BASE_COSTS,
    UPGRADE_MAX_LEVELS,
    UPGRADE_OPTIONS,
)


UPGRADES = UPGRADE_OPTIONS
MAX_LEVELS = UPGRADE_MAX_LEVELS
BASE_COSTS = UPGRADE_BASE_COSTS


class UpgradeSystem:
    def __init__(self):
        self.levels = {
            "power_rounds": 0,
            "needle_rounds": 0,
            "rapid_fire": 0,
            "vital_core": 0,
            "battle_recovery": 0,
            "weapon_double": 0,
            "impact_drive": 0,
        }

    def reset(self):
        for key in self.levels:
            self.levels[key] = 0

    def get_level(self, key):
        return self.levels.get(key, 0)

    def get_max_level(self, key):
        return MAX_LEVELS.get(key, 1)

    def get_cost(self, key, base_cost):
        if key == "heal" or key.startswith("skill_"):
            return base_cost

        level = self.get_level(key)
        return int(base_cost * (1.72 ** level))

    def buy(self, player, npc_role, index):
        options = UPGRADES.get(npc_role, [])

        if index < 0 or index >= len(options):
            return "No upgrade."

        name, base_cost, key = options[index]
        cost = self.get_cost(key, base_cost)

        if key != "heal" and not key.startswith("skill_"):
            level = self.get_level(key)
            max_level = self.get_max_level(key)

            if level >= max_level:
                return f"{name} is maxed."

        if not player.spend_gold(cost):
            return f"Need {cost} gold."

        if key == "power_rounds":
            player.damage_bonus += 5

        elif key == "needle_rounds":
            player.pierce += 1

        elif key == "rapid_fire":
            player.fire_rate_multiplier += 0.12

        elif key == "heal":
            player.heal(45)
            player.last_upgrade_text = name
            return f"Healed for {cost} gold."

        elif key == "vital_core":
            player.max_health += 18
            player.heal(18)

        elif key == "battle_recovery":
            player.regen_on_room_clear += 12

        elif key == "weapon_double":
            player.weapon_damage_multiplier = max(player.weapon_damage_multiplier, 2.0)

        elif key == "impact_drive":
            player.knockback_power += 0.55

        elif key == "skill_blast":
            player.active_skill = "blast"
            player.last_upgrade_text = "Skill: Blast"
            return "Equipped Blast skill."

        elif key == "skill_surge":
            player.active_skill = "surge"
            player.last_upgrade_text = "Skill: Surge"
            return "Equipped Surge skill."

        elif key == "skill_ghost":
            player.active_skill = "ghost"
            player.last_upgrade_text = "Skill: Ghost"
            return "Equipped Ghost skill."

        if key != "heal" and not key.startswith("skill_"):
            self.levels[key] += 1
            level = self.levels[key]
            max_level = self.get_max_level(key)
            player.last_upgrade_text = f"{name} {level}/{max_level}"
            return f"Bought {name} {level}/{max_level} for {cost} gold."

        player.last_upgrade_text = name
        return f"Bought {name} for {cost} gold."
