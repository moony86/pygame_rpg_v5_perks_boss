import pygame

from settings import (
    MAP_SIZE,
    ROOMS_TO_BOSS,
)

from game_state import GameState
from entities.npc import NPC
from entities.enemy import Enemy, EnemyType
from systems.room_system import RoomType


def enter_hub(game):
    game.state = GameState.HUB
    game.player.move_to_hub_spawn()
    game.player.heal(game.player.regen_on_room_clear)
    game.camera.reset(game.player.rect)
    game.dialogue.close()
    game.combat.reset()
    game.enemies.clear()
    game.projectiles.clear()
    game.enemy_bullets.clear()
    game.events.emit("state_hub")

    game.npcs = [
        NPC(MAP_SIZE // 2 - 150, MAP_SIZE // 2, "Blacksmith", "blacksmith", "blacksmith_intro"),
        NPC(MAP_SIZE // 2 + 150, MAP_SIZE // 2, "Healer", "healer", "healer_intro"),
        NPC(MAP_SIZE // 2, MAP_SIZE // 2 - 120, "Gatekeeper", "portal", "portal_intro"),
    ]

    game.collision.clear()
    game.collision.add_entities(game.npcs)
    game.collision.add_rect(game.portal_rect)


def enter_room(game):
    game.collision.clear()
    game.state = GameState.ROOM
    game.player.move_to_room_spawn()
    game.camera.reset(game.player.rect)
    game.dialogue.close()
    game.enemies.clear()
    game.projectiles.clear()
    game.enemy_bullets.clear()
    game.room_kills = 0
    game.events.emit("state_room")

    room_type = game.rooms.choose_next_room(game.room_number)
    game.spawn.reset(game.room_number, room_type)

    if room_type == RoomType.TREASURE:
        reward = 25 + game.room_number * 8
        game.player.add_gold(reward)
        game.message = f"Treasure room: +{reward} gold. Return to hub."
        game.audio.play("room")
        game.effects.ring(game.player.rect.center, radius=120, life=0.7)
        game.room_number += 1
        enter_hub(game)
        return

    game.message = f"{game.rooms.display_name()} Room started."

    if room_type == RoomType.CURSE:
        game.message += " Rewards x2."

    game.audio.play("room")


def enter_boss(game):
    game.collision.clear()
    game.state = GameState.BOSS
    game.player.move_to_room_spawn()
    game.camera.reset(game.player.rect)
    game.enemies.clear()
    game.projectiles.clear()
    game.enemy_bullets.clear()
    game.events.emit("state_boss")
    game.events.emit("boss_spawned")

    boss = Enemy(
        MAP_SIZE // 2,
        MAP_SIZE // 2 - 360,
        EnemyType.BOSS,
        difficulty=1.0,
    )

    game.enemies.append(boss)
    game.message = "Boss awakened. Phase attacks have warnings."
    game.audio.play("boss")
    game.effects.ring(boss.rect.center, radius=180, life=1.0, width=5)
