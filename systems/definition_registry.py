from definitions.enemy_definitions import ENEMY_DEFINITIONS, enemy_threat_costs
from definitions.perk_definitions import PERK_DEFINITIONS, PERK_SYNERGY_PAIRS
from definitions.room_definitions import ROOM_DEFINITIONS, get_room_info
from definitions.upgrade_definitions import (
    UPGRADE_BASE_COSTS,
    UPGRADE_MAX_LEVELS,
    UPGRADE_OPTIONS,
)
from definitions.weapon_definitions import WEAPON_DEFINITIONS
from definitions.prefab_definitions import PREFAB_DEFINITIONS


class DefinitionRegistry:
    VALID_WEAPON_ATTACK_TYPES = {"projectile", "melee_arc", "melee_rect"}

    def __init__(self):
        self.weapons = WEAPON_DEFINITIONS
        self.enemies = ENEMY_DEFINITIONS
        self.rooms = ROOM_DEFINITIONS
        self.perks = {definition["key"]: definition for definition in PERK_DEFINITIONS}
        self.upgrades = UPGRADE_OPTIONS
        self.upgrade_max_levels = UPGRADE_MAX_LEVELS
        self.upgrade_base_costs = UPGRADE_BASE_COSTS
        self.perk_synergy_pairs = PERK_SYNERGY_PAIRS
        self.prefabs = PREFAB_DEFINITIONS

    def require_weapon(self, weapon_id):
        return self._require(self.weapons, weapon_id, "weapon")

    def require_enemy(self, enemy_type):
        return self._require(self.enemies, enemy_type, "enemy")

    def require_room(self, room_id):
        return self._require(self.rooms, room_id, "room")

    def require_perk(self, perk_key):
        return self._require(self.perks, perk_key, "perk")

    def require_prefab(self, prefab_id):
        return self._require(self.prefabs, prefab_id, "prefab")

    def upgrade_options_for(self, npc_role):
        return list(self.upgrades.get(npc_role, ()))

    def room_info(self, room_id):
        return get_room_info(room_id)

    def enemy_threat_costs(self):
        return enemy_threat_costs()

    def validate(self):
        self._validate_weapon_definitions()
        self._validate_enemy_definitions()
        self._validate_room_definitions()
        self._validate_perk_definitions()
        self._validate_upgrade_definitions()
        self._validate_prefab_definitions()
        return True

    def _require(self, definitions, key, label):
        try:
            return definitions[key]
        except KeyError as error:
            raise KeyError(f"Unknown {label} definition: {key!r}") from error

    def _validate_keys(self, label, definitions):
        for key in definitions:
            if key is None or key == "":
                raise ValueError(f"{label} definition has an empty key")

    def _validate_unique_ids(self, label, definitions):
        seen = {}
        for key, definition in definitions.items():
            definition_id = getattr(definition, "id", None)
            if not definition_id:
                raise ValueError(f"{label} definition {key!r} has an empty id")
            if definition_id in seen:
                raise ValueError(f"Duplicate {label} definition id {definition_id!r}: {seen[definition_id]!r} and {key!r}")
            seen[definition_id] = key

    def _validate_weapon_definitions(self):
        self._validate_keys("weapon", self.weapons)
        self._validate_unique_ids("weapon", self.weapons)
        for weapon_id, definition in self.weapons.items():
            if definition.attack_type not in self.VALID_WEAPON_ATTACK_TYPES:
                raise ValueError(
                    f"Weapon definition {weapon_id!r} has invalid attack_type "
                    f"{definition.attack_type!r}; expected one of {sorted(self.VALID_WEAPON_ATTACK_TYPES)}"
                )
            if definition.cooldown < 0:
                raise ValueError(f"Weapon definition {weapon_id!r} has negative cooldown {definition.cooldown!r}")

    def _validate_enemy_definitions(self):
        self._validate_keys("enemy", self.enemies)
        self._validate_unique_ids("enemy", self.enemies)
        for enemy_type, definition in self.enemies.items():
            if definition.enemy_type != enemy_type:
                raise ValueError(
                    f"Enemy definition {definition.id!r} is registered under {enemy_type!r} "
                    f"but stores enemy_type {definition.enemy_type!r}"
                )
            if definition.threat_cost is not None and definition.threat_cost <= 0:
                raise ValueError(f"Enemy definition {definition.id!r} has non-positive threat_cost {definition.threat_cost!r}")

    def _validate_room_definitions(self):
        from systems.room_system import RoomType

        self._validate_keys("room", self.rooms)
        self._validate_unique_ids("room", self.rooms)
        expected_room_ids = {room_type.name.lower() for room_type in RoomType}
        actual_room_ids = set(self.rooms)
        missing = sorted(expected_room_ids - actual_room_ids)
        extra = sorted(actual_room_ids - expected_room_ids)
        if missing or extra:
            raise ValueError(f"Room definition ids do not match RoomType values; missing={missing}, extra={extra}")

    def _validate_perk_definitions(self):
        keys = []
        for definition in PERK_DEFINITIONS:
            key = definition.get("key")
            if not key:
                raise ValueError(f"Perk definition has an empty key: {definition!r}")
            keys.append(key)
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        if duplicates:
            raise ValueError(f"Duplicate perk definition keys: {duplicates}")

    def _validate_upgrade_definitions(self):
        option_keys = set()
        for npc_role, options in self.upgrades.items():
            if not npc_role:
                raise ValueError("Upgrade options contain an empty npc role")
            for option in options:
                if len(option) != 3:
                    raise ValueError(f"Upgrade option for {npc_role!r} must be (name, base_cost, key): {option!r}")
                name, base_cost, key = option
                if not name:
                    raise ValueError(f"Upgrade option for {npc_role!r} has an empty name: {option!r}")
                if not key:
                    raise ValueError(f"Upgrade option {name!r} for {npc_role!r} has an empty key")
                if base_cost < 0:
                    raise ValueError(f"Upgrade option {name!r} for {npc_role!r} has negative base_cost {base_cost!r}")
                option_keys.add(key)

        for key, max_level in self.upgrade_max_levels.items():
            if key not in option_keys:
                raise ValueError(f"Upgrade max level key {key!r} does not exist in upgrade options")
            if not isinstance(max_level, int) or max_level <= 0:
                raise ValueError(f"Upgrade max level for {key!r} must be a positive int, got {max_level!r}")

        for key, base_cost in self.upgrade_base_costs.items():
            if key not in option_keys:
                raise ValueError(f"Upgrade base cost key {key!r} does not exist in upgrade options")
            if base_cost < 0:
                raise ValueError(f"Upgrade base cost for {key!r} must be non-negative, got {base_cost!r}")

    def _validate_prefab_definitions(self):
        self._validate_keys("prefab", self.prefabs)
        self._validate_unique_ids("prefab", self.prefabs)
        valid_types = {"Enemy", "NPC", "Portal", "Obstacle", "Projectile", "Room Exit", "Pickup", "Chest"}
        for prefab_id, definition in self.prefabs.items():
            if definition.prefab_type not in valid_types:
                raise ValueError(
                    f"Prefab definition {prefab_id!r} has invalid prefab_type "
                    f"{definition.prefab_type!r}; expected one of {sorted(valid_types)}"
                )


definition_registry = DefinitionRegistry()
