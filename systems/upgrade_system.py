UPGRADES = {
    "blacksmith": [
        ("Sharpen Blade", 18, "damage"),
        ("Piercing Tips", 28, "pierce"),
        ("Rapid Trigger", 28, "firerate"),
    ],
    "healer": [
        ("Heal", 10, "heal"),
        ("Max Health", 24, "maxhp"),
        ("Room Regen", 22, "regen"),
    ],
}


MAX_LEVELS = {
    "damage": 6,
    "pierce": 3,
    "firerate": 4,
    "maxhp": 6,
    "regen": 4,
}


BASE_COSTS = {
    "damage": 18,
    "pierce": 28,
    "firerate": 28,
    "maxhp": 24,
    "regen": 22,
}


class UpgradeSystem:
    def __init__(self):
        self.levels = {
            "damage": 0,
            "pierce": 0,
            "firerate": 0,
            "maxhp": 0,
            "regen": 0,
        }

    def reset(self):
        for key in self.levels:
            self.levels[key] = 0

    def get_level(self, key):
        return self.levels.get(key, 0)

    def get_max_level(self, key):
        return MAX_LEVELS.get(key, 1)

    def get_cost(self, key, base_cost):
        if key == "heal":
            return base_cost

        level = self.get_level(key)
        return int(base_cost * (1.55 ** level))

    def buy(self, player, npc_role, index):
        options = UPGRADES.get(npc_role, [])

        if index < 0 or index >= len(options):
            return "No upgrade."

        name, base_cost, key = options[index]
        cost = self.get_cost(key, base_cost)

        if key != "heal":
            level = self.get_level(key)
            max_level = self.get_max_level(key)

            if level >= max_level:
                return f"{name} is maxed."

        if not player.spend_gold(cost):
            return f"Need {cost} gold."

        if key == "damage":
            player.damage_bonus += 5

        elif key == "pierce":
            player.pierce += 1

        elif key == "firerate":
            player.fire_rate_multiplier += 0.12

        elif key == "heal":
            player.heal(45)
            player.last_upgrade_text = name
            return f"Healed for {cost} gold."

        elif key == "maxhp":
            player.max_health += 18
            player.heal(18)

        elif key == "regen":
            player.regen_on_room_clear += 8

        if key != "heal":
            self.levels[key] += 1
            level = self.levels[key]
            max_level = self.get_max_level(key)
            player.last_upgrade_text = f"{name} {level}/{max_level}"
            return f"Bought {name} {level}/{max_level} for {cost} gold."

        player.last_upgrade_text = name
        return f"Bought {name} for {cost} gold."