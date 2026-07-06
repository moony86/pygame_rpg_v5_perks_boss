from dataclasses import dataclass

from definitions.common import Definition
from entities.enemy import EnemyType


@dataclass(frozen=True)
class EnemyDefinition(Definition):
    enemy_type: EnemyType
    category: str
    behavior_type: str
    draw_profile: str
    threat_cost: int | None = None


ENEMY_DEFINITIONS = {
    EnemyType.CHASER: EnemyDefinition(
        id="chaser",
        display_name="Chaser",
        enemy_type=EnemyType.CHASER,
        category="basic",
        behavior_type="chase",
        draw_profile="chaser",
        threat_cost=1,
    ),
    EnemyType.CHASER_FAST: EnemyDefinition(
        id="chaser_fast",
        display_name="Fast Chaser",
        enemy_type=EnemyType.CHASER_FAST,
        category="basic",
        behavior_type="chase",
        draw_profile="chaser",
        threat_cost=2,
    ),
    EnemyType.CHASER_TANK: EnemyDefinition(
        id="chaser_tank",
        display_name="Tank Chaser",
        enemy_type=EnemyType.CHASER_TANK,
        category="basic",
        behavior_type="chase",
        draw_profile="chaser",
        threat_cost=4,
    ),
    EnemyType.RANGED: EnemyDefinition(
        id="ranged",
        display_name="Ranged",
        enemy_type=EnemyType.RANGED,
        category="ranged",
        behavior_type="ranged",
        draw_profile="ranged",
        threat_cost=3,
    ),
    EnemyType.RANGED_THREE: EnemyDefinition(
        id="ranged_three",
        display_name="Triple Ranged",
        enemy_type=EnemyType.RANGED_THREE,
        category="ranged",
        behavior_type="ranged",
        draw_profile="ranged",
        threat_cost=5,
    ),
    EnemyType.RANGED_FIVE: EnemyDefinition(
        id="ranged_five",
        display_name="Five-Shot Ranged",
        enemy_type=EnemyType.RANGED_FIVE,
        category="ranged",
        behavior_type="ranged",
        draw_profile="ranged",
        threat_cost=8,
    ),
    EnemyType.RANGED_RAIN: EnemyDefinition(
        id="ranged_rain",
        display_name="Rain Ranged",
        enemy_type=EnemyType.RANGED_RAIN,
        category="ranged",
        behavior_type="ranged_rain",
        draw_profile="ranged",
        threat_cost=9,
    ),
    EnemyType.JUMPER: EnemyDefinition(
        id="jumper",
        display_name="Jumper",
        enemy_type=EnemyType.JUMPER,
        category="jumper",
        behavior_type="jumper",
        draw_profile="jumper",
        threat_cost=4,
    ),
    EnemyType.JUMPER_FAST: EnemyDefinition(
        id="jumper_fast",
        display_name="Fast Jumper",
        enemy_type=EnemyType.JUMPER_FAST,
        category="jumper",
        behavior_type="jumper",
        draw_profile="jumper",
        threat_cost=6,
    ),
    EnemyType.JUMPER_HEAVY: EnemyDefinition(
        id="jumper_heavy",
        display_name="Heavy Jumper",
        enemy_type=EnemyType.JUMPER_HEAVY,
        category="jumper",
        behavior_type="jumper",
        draw_profile="jumper",
        threat_cost=7,
    ),
    EnemyType.HUNTER: EnemyDefinition(
        id="hunter",
        display_name="Hunter",
        enemy_type=EnemyType.HUNTER,
        category="ranged",
        behavior_type="hunter",
        draw_profile="hunter",
        threat_cost=5,
    ),
    EnemyType.BRUTE: EnemyDefinition(
        id="brute",
        display_name="Brute",
        enemy_type=EnemyType.BRUTE,
        category="heavy",
        behavior_type="brute",
        draw_profile="brute",
        threat_cost=6,
    ),
    EnemyType.ELITE: EnemyDefinition(
        id="elite",
        display_name="Elite",
        enemy_type=EnemyType.ELITE,
        category="elite",
        behavior_type="elite",
        draw_profile="elite",
        threat_cost=10,
    ),
    EnemyType.BOSS: EnemyDefinition(
        id="boss",
        display_name="Boss",
        enemy_type=EnemyType.BOSS,
        category="boss",
        behavior_type="boss",
        draw_profile="boss",
    ),
    EnemyType.LOOT: EnemyDefinition(
        id="loot",
        display_name="Loot Beast",
        enemy_type=EnemyType.LOOT,
        category="special",
        behavior_type="loot",
        draw_profile="loot",
    ),
}


def get_enemy_definition(enemy_type):
    return ENEMY_DEFINITIONS[enemy_type]


def enemy_threat_costs():
    return {
        enemy_type: definition.threat_cost
        for enemy_type, definition in ENEMY_DEFINITIONS.items()
        if definition.threat_cost is not None
    }
