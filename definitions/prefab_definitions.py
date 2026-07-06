from dataclasses import dataclass, field

from definitions.common import Definition
from definitions.enemy_definitions import ENEMY_DEFINITIONS
from entities.enemy import EnemyType


@dataclass(frozen=True)
class PrefabDefinition(Definition):
    prefab_type: str
    metadata: dict = field(default_factory=dict)


PREFAB_DEFINITIONS = {
    "enemy_chaser": PrefabDefinition(
        id="enemy_chaser",
        display_name="Enemy: Chaser",
        prefab_type="Enemy",
        metadata={"enemy_type": EnemyType.CHASER},
    ),
    "enemy_fast_chaser": PrefabDefinition(
        id="enemy_fast_chaser",
        display_name="Enemy: Fast Chaser",
        prefab_type="Enemy",
        metadata={"enemy_type": EnemyType.CHASER_FAST},
    ),
    "enemy_tank_chaser": PrefabDefinition(
        id="enemy_tank_chaser",
        display_name="Enemy: Tank Chaser",
        prefab_type="Enemy",
        metadata={"enemy_type": EnemyType.CHASER_TANK},
    ),
    "enemy_ranged": PrefabDefinition(
        id="enemy_ranged",
        display_name="Enemy: Ranged",
        prefab_type="Enemy",
        metadata={"enemy_type": EnemyType.RANGED},
    ),
    "enemy_jumper": PrefabDefinition(
        id="enemy_jumper",
        display_name="Enemy: Jumper",
        prefab_type="Enemy",
        metadata={"enemy_type": EnemyType.JUMPER},
    ),
    "enemy_elite": PrefabDefinition(
        id="enemy_elite",
        display_name="Enemy: Elite",
        prefab_type="Enemy",
        metadata={"enemy_type": EnemyType.ELITE},
    ),
    "enemy_boss": PrefabDefinition(
        id="enemy_boss",
        display_name="Enemy: Boss",
        prefab_type="Enemy",
        metadata={"enemy_type": EnemyType.BOSS},
    ),
    "enemy_loot": PrefabDefinition(
        id="enemy_loot",
        display_name="Enemy: Loot Beast",
        prefab_type="Enemy",
        metadata={"enemy_type": EnemyType.LOOT},
    ),
    "npc_blacksmith": PrefabDefinition(
        id="npc_blacksmith",
        display_name="NPC: Blacksmith",
        prefab_type="NPC",
        metadata={"name": "Blacksmith", "role": "blacksmith", "dialogue_id": "blacksmith_intro"},
    ),
    "npc_healer": PrefabDefinition(
        id="npc_healer",
        display_name="NPC: Healer",
        prefab_type="NPC",
        metadata={"name": "Healer", "role": "healer", "dialogue_id": "healer_intro"},
    ),
    "npc_gatekeeper": PrefabDefinition(
        id="npc_gatekeeper",
        display_name="NPC: Gatekeeper",
        prefab_type="NPC",
        metadata={"name": "Gatekeeper", "role": "portal", "dialogue_id": "portal_intro"},
    ),
    "npc_seer": PrefabDefinition(
        id="npc_seer",
        display_name="NPC: Seer",
        prefab_type="NPC",
        metadata={"name": "Seer", "role": "seer", "dialogue_id": "seer_intro"},
    ),
    "npc_tea_vendor": PrefabDefinition(
        id="npc_tea_vendor",
        display_name="NPC: Tea Vendor",
        prefab_type="NPC",
        metadata={"name": "Tea Vendor", "role": "tea_vendor", "dialogue_id": "tea_vendor"},
    ),
    "portal_hub": PrefabDefinition(
        id="portal_hub",
        display_name="Portal: Hub",
        prefab_type="Portal",
        metadata={"width": 90, "height": 55, "target_scene": "room"},
    ),
    "obstacle_rect": PrefabDefinition(
        id="obstacle_rect",
        display_name="Obstacle: Rectangle",
        prefab_type="Obstacle",
        metadata={"width": 120, "height": 90},
    ),
    "projectile_player": PrefabDefinition(
        id="projectile_player",
        display_name="Projectile: Player",
        prefab_type="Projectile",
        metadata={},
    ),
    "room_exit": PrefabDefinition(
        id="room_exit",
        display_name="Room Exit",
        prefab_type="Room Exit",
        metadata={"width": 170, "height": 170},
    ),
    "pickup_generic": PrefabDefinition(
        id="pickup_generic",
        display_name="Pickup: Generic",
        prefab_type="Pickup",
        metadata={"width": 28, "height": 28},
    ),
    "chest_generic": PrefabDefinition(
        id="chest_generic",
        display_name="Chest: Generic",
        prefab_type="Chest",
        metadata={"width": 64, "height": 44},
    ),
}


for enemy_type, enemy_definition in ENEMY_DEFINITIONS.items():
    prefab_id = f"enemy_{enemy_type.name.lower()}"
    PREFAB_DEFINITIONS.setdefault(
        prefab_id,
        PrefabDefinition(
            id=prefab_id,
            display_name=f"Enemy: {enemy_definition.display_name}",
            prefab_type="Enemy",
            metadata={"enemy_type": enemy_type},
        ),
    )
