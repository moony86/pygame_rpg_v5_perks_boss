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
    game.gatekeeper_ready = False
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
    game.waves.reset(game.room_number, room_type, game.player)
    if room_type not in (RoomType.TREASURE,):
        game.rooms.target_kills = sum(wave.get("count", 0) for wave in game.waves.waves)
    game.room_exit_open = False

    if room_type == RoomType.TREASURE:
        game.rooms.target_kills = 2
        loot_positions = (
            (MAP_SIZE // 2 - 120, MAP_SIZE // 2 - 170),
            (MAP_SIZE // 2 + 120, MAP_SIZE // 2 - 170),
        )
        for x, y in loot_positions:
            loot = Enemy(
                x,
                y,
                EnemyType.LOOT,
                difficulty=1.0 + game.room_number * 0.18,
            )
            game.enemies.append(loot)
            game.effects.ring(loot.rect.center, radius=120, life=0.7, width=4)
        game.message = "Treasure room: chase the Loot Beasts for 15 seconds."
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

    boss_stage = 2 if game.room_number > ROOMS_TO_BOSS else 1
    boss_difficulty = (
        1.25
        + game.room_number * 0.68
        + max(0, game.player.level - 1) * 0.30
        + game.player.build_power_score() * 0.20
        + (boss_stage - 1) * 1.35
    )
    boss = Enemy(
        MAP_SIZE // 2,
        MAP_SIZE // 2 - 220,
        EnemyType.BOSS,
        difficulty=boss_difficulty,
    )

    game.enemies.append(boss)
    game.message = f"Boss {boss_stage}/2 awakened. Threat x{boss_difficulty:.1f}."
    game.audio.play("boss")
    game.effects.ring(boss.rect.center, radius=180, life=1.0, width=5)
