from entities.pickup import Pickup


COIN_UNIT_VALUE = 10
MAX_XP_DROPS_PER_ENEMY = 4
DEFAULT_MAGNET_RADIUS = 100
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
            if not pickup.alive or pickup.pickup_type not in ("gold", "xp"):
                continue
            value = pickup.value
            self._collect(pickup, player, effects, audio)
            collected[pickup.pickup_type] += value
            pickup.alive = False
        self.pickups = [pickup for pickup in self.pickups if pickup.alive]
        return collected

    def spawn_enemy_rewards(self, position, gold, xp):
        self.spawn_gold(position, gold)
        self.spawn_xp(position, xp)

    def spawn_gold(self, position, amount):
        for value in self._split_amount(amount, COIN_UNIT_VALUE):
            self.pickups.append(Pickup(position[0], position[1], "gold", value))

    def spawn_xp(self, position, amount, tier_hint=None):
        for value, tier_id in self._split_xp_pickups(amount, tier_hint=tier_hint):
            self.pickups.append(Pickup(position[0], position[1], "xp", value, tier_id=tier_id))

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
        if pickup.pickup_type == "gold":
            player.add_gold(pickup.value)
            label = f"+{pickup.value}g"
            sound_key = "coin_pickup"
        else:
            player.add_xp(pickup.value)
            label = f"+{pickup.value}xp"
            sound_key = "xp_pickup"

        if effects:
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
