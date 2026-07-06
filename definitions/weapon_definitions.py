from dataclasses import dataclass

from definitions.common import Definition


@dataclass(frozen=True)
class WeaponDefinition(Definition):
    attack_type: str
    cooldown: float
    damage: int | None = None
    range: int | None = None
    arc_degrees: int | None = None
    hitbox_width: int | None = None
    hitbox_length: int | None = None
    knockback: int | None = None


WEAPON_DEFINITIONS = {
    "pistol": WeaponDefinition(
        id="pistol",
        display_name="Pistol",
        attack_type="projectile",
        cooldown=0.30,
    ),
    "knife": WeaponDefinition(
        id="knife",
        display_name="Knife",
        attack_type="melee_arc",
        cooldown=0.38,
        damage=35,
        range=85,
        arc_degrees=105,
        knockback=26,
    ),
    "sword": WeaponDefinition(
        id="sword",
        display_name="Sword",
        attack_type="melee_rect",
        cooldown=0.55,
        damage=55,
        range=110,
        hitbox_width=54,
        hitbox_length=120,
        knockback=34,
    ),
}


def get_weapon_definition(weapon_id):
    return WEAPON_DEFINITIONS[weapon_id]
