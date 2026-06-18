UPGRADES = {
    "blacksmith": [
        ("Sharpen Blade", 18, "damage"),
        ("Multi Shot", 34, "multishot"),
        ("Rapid Trigger", 28, "firerate"),
    ],
    "healer": [
        ("Heal", 10, "heal"),
        ("Max Health", 24, "maxhp"),
        ("Room Regen", 22, "regen"),
    ],
}


class UpgradeSystem:
    def buy(self, player, npc_role, index):
        options = UPGRADES.get(npc_role, [])
        if index < 0 or index >= len(options):
            return "No upgrade."

        name, cost, key = options[index]
        if not player.spend_gold(cost):
            return f"Need {cost} gold."

        if key == "damage":
            player.damage_bonus += 5
        elif key == "multishot":
            if player.projectile_count < 7:
                player.projectile_count += 1
                player.spread_degrees = min(42, player.spread_degrees + 8)
            else:
                player.damage_bonus += 4
        elif key == "firerate":
            player.fire_rate_multiplier += 0.16
        elif key == "heal":
            player.heal(45)
        elif key == "maxhp":
            player.max_health += 18
            player.heal(18)
        elif key == "regen":
            player.regen_on_room_clear += 8

        player.last_upgrade_text = name
        return f"Bought {name} for {cost} gold."
