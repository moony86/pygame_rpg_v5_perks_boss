import random

from entities.pickup import Pickup
from systems.object_catalog import definition


COIN_UNIT_VALUE = 10
MAX_XP_DROPS_PER_ENEMY = 4
DEFAULT_MAGNET_RADIUS = 100
HEAL_POTION_DROP_CHANCE = 0.035
TIME_STOP_DROP_CHANCE = 0.025
ELITE_SPECIAL_DROP_MULTIPLIER = 2.0
HEAL_POTION_AMOUNTS = (15, 25, 35)
HEAL_POTION_WEIGHTS = (0.46, 0.34, 0.20)
HEAL_POTION_AMOUNT = 35
TIME_STOP_DURATION = 2.0
XP_TIER_DEFINITIONS = {
    "xp_tier_1": {"anchor": 5, "name": "Tiny XP Shard", "color": "pale_cyan"},
    "xp_tier_2": {"anchor": 25, "name": "Small XP Crystal", "color": "cyan"},
    "xp_tier_3": {"anchor": 75, "name": "Medium XP Crystal", "color": "blue"},
    "xp_tier_4": {"anchor": 200, "name": "Large XP Crystal", "color": "purple"},
    "xp_tier_5": {"anchor": 500, "name": "Huge XP Crystal", "color": "gold"},
}
XP_TIER_ORDER = tuple(
    sorted(XP_TIER_DEFINITIONS.items(), key=lambda item: item[1]["anchor"], reverse=True)
)


class LootSystem:
    def __init__(self, magnet_radius=DEFAULT_MAGNET_RADIUS):
        self.pickups = []
        self.magnet_radius = magnet_radius

    def reset(self):
        self.pickups.clear()

    def force_collect_remaining(self):
        for pickup in self.pickups:
            pickup.force_collect = True

    def collect_remaining(self, player, effects=None, audio=None):
        collected = {"gold": 0, "xp": 0}
        for pickup in self.pickups:
            if not pickup.alive or pickup.pickup_type not in ("gold", "xp", "heal_potion", "time_stop"):
                continue
            value = pickup.value
            self._collect(pickup, player, effects, audio)
            collected[pickup.pickup_type] = collected.get(pickup.pickup_type, 0) + value
            pickup.alive = False
        self.pickups = [pickup for pickup in self.pickups if pickup.alive]
        return collected

    def spawn_enemy_rewards(self, position, gold, xp, enemy_type=None):
        self.spawn_gold(position, gold)
        self.spawn_xp(position, xp)
        self.spawn_special_enemy_drop(position, enemy_type)

    def spawn_gold(self, position, amount):
        for value in self._split_amount(amount, COIN_UNIT_VALUE):
            self.pickups.append(Pickup(position[0], position[1], "gold", value))

    def spawn_xp(self, position, amount, tier_hint=None):
        for value, tier_id in self._split_xp_pickups(amount, tier_hint=tier_hint):
            self.pickups.append(Pickup(position[0], position[1], "xp", value, tier_id=tier_id))

    def spawn_special_enemy_drop(self, position, enemy_type=None):
        type_name = getattr(enemy_type, "name", str(enemy_type or ""))
        multiplier = ELITE_SPECIAL_DROP_MULTIPLIER if type_name == "ELITE" else 1.0
        potion = definition('heal_potion')
        time_stop = definition('time_stop')
        if random.random() < potion['drop_chance'] * multiplier:
            heal_amount = random.choices((potion['small'], potion['medium'], potion['large']), weights=HEAL_POTION_WEIGHTS, k=1)[0]
            self.pickups.append(Pickup(position[0], position[1], "heal_potion", heal_amount))
            return
        if random.random() < time_stop['drop_chance'] * multiplier:
            self.pickups.append(Pickup(position[0], position[1], "time_stop", time_stop['duration']))

    def update(self, dt, player, effects=None, audio=None):
        for pickup in self.pickups:
            if not pickup.alive:
                continue
            if pickup.update(dt, player, self.magnet_radius):
                self._collect(pickup, player, effects, audio)
        self.pickups = [pickup for pickup in self.pickups if pickup.alive]

    def draw(self, surface, camera):
        for pickup in self.pickups:
            pickup.draw(surface, camera)

    def _collect(self, pickup, player, effects, audio):
        feedback_value=pickup.value
        if pickup.pickup_type == "gold":
            player.add_gold(pickup.value)
            label = f"+{pickup.value}g"
            sound_key = "coin_pickup"
        elif pickup.pickup_type == "xp":
            player.add_xp(pickup.value)
            label = f"+{pickup.value}xp"
            sound_key = "xp_pickup"
        elif pickup.pickup_type == "heal_potion":
            previous_health=player.health
            player.heal(pickup.value)
            feedback_value=player.health-previous_health
            label = f"+{feedback_value} HP" if feedback_value>0 else 'HP FULL'
            sound_key = "heal_pickup"
        elif pickup.pickup_type == "time_stop":
            player.enemy_time_stop_timer = max(getattr(player, "enemy_time_stop_timer", 0.0), float(pickup.value))
            label = "TIME STOP"
            sound_key = "time_stop_pickup"
        else:
            return

        if effects:
            modern=hasattr(effects,'collect_pickup')
            if modern:
                effects.collect_pickup(pickup.pickup_type,feedback_value,player.rect.center)
            if pickup.pickup_type == "heal_potion" and not modern:
                effects.heal_burst(player.rect.center)
                effects.message(label, player.rect.midtop, color=(95, 255, 145))
            elif pickup.pickup_type == "time_stop":
                effects.time_stop_trigger(player.rect.center, pickup.value)
                if not modern:
                    effects.message(label, player.rect.midtop, color=(120, 225, 255))
            elif not modern:
                effects.ring(pickup.rect.center, radius=24, life=0.16, width=2)
                effects.message(label, pickup.rect.midtop)
        if audio:
            audio.play(sound_key)

    def _split_amount(self, amount, unit_value):
        amount = int(amount)
        if amount <= 0:
            return []
        values = [unit_value] * (amount // unit_value)
        remainder = amount % unit_value
        if remainder:
            values.append(remainder)
        if not values:
            values.append(amount)
        return values

    def _split_xp_amount(self, amount):
        return [value for value, _tier_id in self._split_xp_pickups(amount)]

    def _split_xp_pickups(self, amount, tier_hint=None, max_drops=MAX_XP_DROPS_PER_ENEMY):
        amount = int(amount)
        if amount <= 0:
            return []

        values = self._greedy_xp_values(amount)
        if max_drops is not None:
            values = self._cap_xp_values(values, int(max_drops))
        return [(value, self._tier_for_xp_value(value, tier_hint=tier_hint)) for value in values]

    def _greedy_xp_values(self, amount):
        remaining = int(amount)
        values = []
        for _tier_id, definition in XP_TIER_ORDER:
            anchor = definition["anchor"]
            while remaining >= anchor:
                values.append(anchor)
                remaining -= anchor
        if remaining:
            values.append(remaining)
        return values

    def _cap_xp_values(self, values, max_drops):
        if max_drops <= 0 or len(values) <= max_drops:
            return values

        capped = list(values[:max_drops])
        overflow = sum(values[max_drops:])
        capped[-1] += overflow
        return capped

    def _tier_for_xp_value(self, value, tier_hint=None):
        if tier_hint in XP_TIER_DEFINITIONS:
            return tier_hint
        value = int(value)
        selected = "xp_tier_1"
        for tier_id, definition in reversed(XP_TIER_ORDER):
            if value >= definition["anchor"]:
                selected = tier_id
        return selected
