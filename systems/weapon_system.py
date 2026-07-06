from abc import ABC, abstractmethod
from typing import Any

from systems.definition_registry import definition_registry


AttackRequest = dict[str, Any]

ATTACK_PROJECTILE = "projectile"
ATTACK_MELEE_ARC = "melee_arc"
ATTACK_MELEE_RECT = "melee_rect"


def projectile_request() -> AttackRequest:
    return {
        "type": ATTACK_PROJECTILE,
    }


def melee_arc_request(origin, direction, damage, attack_range, arc_degrees, knockback) -> AttackRequest:
    return {
        "type": ATTACK_MELEE_ARC,
        "origin": origin,
        "direction": direction,
        "damage": damage,
        "range": attack_range,
        "arc_degrees": arc_degrees,
        "knockback": knockback,
    }


def melee_rect_request(origin, direction, damage, attack_range, width, length, knockback) -> AttackRequest:
    return {
        "type": ATTACK_MELEE_RECT,
        "origin": origin,
        "direction": direction,
        "damage": damage,
        "range": attack_range,
        "width": width,
        "length": length,
        "knockback": knockback,
    }


class Weapon(ABC):
    def __init__(self, definition):
        self.definition = definition
        self.id = definition.id
        self.name = definition.display_name
        self.cooldown = definition.cooldown

    @abstractmethod
    def attack(self, player):
        """Return an attack intent only; weapons do not resolve combat."""


class PistolWeapon(Weapon):
    def __init__(self):
        super().__init__(definition_registry.require_weapon("pistol"))

    def attack(self, player):
        return projectile_request()


class KnifeWeapon(Weapon):
    def __init__(self):
        super().__init__(definition_registry.require_weapon("knife"))

    def attack(self, player):
        return melee_arc_request(
            origin=player.rect.center,
            direction=player.aim_direction.copy(),
            damage=self.definition.damage,
            attack_range=self.definition.range,
            arc_degrees=self.definition.arc_degrees,
            knockback=self.definition.knockback,
        )


class SwordWeapon(Weapon):
    def __init__(self):
        super().__init__(definition_registry.require_weapon("sword"))

    def attack(self, player):
        return melee_rect_request(
            origin=player.rect.center,
            direction=player.aim_direction.copy(),
            damage=self.definition.damage,
            attack_range=self.definition.range,
            width=self.definition.hitbox_width,
            length=self.definition.hitbox_length,
            knockback=self.definition.knockback,
        )
