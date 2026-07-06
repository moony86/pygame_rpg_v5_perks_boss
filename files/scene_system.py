"""Legacy scene-flow copy.

Active runtime code imports systems.scene_system. Keep this file as a temporary
reference only until the legacy folder is removed after validation.
"""

import pygame

from settings import (
    MAP_SIZE,
    ROOMS_TO_BOSS,
)

from game_state import GameState
from entities.npc import NPC
from entities.enemy import Enemy, EnemyType
from systems.room_system import RoomType


def clear_active_enemies(game):
    if hasattr(game, "enemy_pool"):
        game.enemy_pool.release_many(game.enemies)
    game.enemies.clear()


def _increment_npc_visits(game):
    """
    Increment visit_count for every NPC that already exists in game.npcs.
    Called at the TOP of enter_hub, before the list is rebuilt,
    so the first visit stays at 0 and subsequent visits count up correctly.
    """
    if hasattr(game, "npcs"):
        for npc in game.npcs:
            npc.visit_count += 1


def _carry_visit_counts(old_npcs, new_npcs):
    """
    Transfer visit_counts from the previous NPC list to the new one
    by matching on role. This keeps memory intact across HUB rebuilds.
    """
    counts = {npc.role: npc.visit_count for npc in old_npcs}
    for npc in new_npcs:
        if npc.role in counts:
            npc.visit_count = counts[npc.role]


def _next_room_type_name(game):
    """Return a string hint about the upcoming room type for the Seer."""
    try:
        upcoming = game.rooms.choose_next_room(game.room_number)
        return upcoming.name  # e.g. "SURVIVAL", "TREASURE", "CURSE", "ELITE"
    except Exception:
        return ""


def enter_hub(game):
    # ── increment visit memory before rebuilding NPC list ────────────────
    _increment_npc_visits(game)
    old_npcs = getattr(game, "npcs", [])

    game.state = GameState.HUB
    game.player.move_to_hub_spawn()
    game.player.heal(game.player.regen_on_room_clear)
    game.camera.reset(game.player.rect)
    game.dialogue.close()
    game.gatekeeper_ready = False
    game.combat.reset()
    clear_active_enemies(game)
    game.projectiles.clear()
    game.enemy_bullets.clear()
    game.events.emit("state_hub")

    # ── build NPC list — Seer added bottom-left of hub ───────────────────
    game.npcs = [
        NPC(MAP_SIZE // 2 - 150, MAP_SIZE // 2,       "Blacksmith", "blacksmith", "blacksmith_intro"),
        NPC(MAP_SIZE // 2 + 150, MAP_SIZE // 2,       "Healer",     "healer",     "healer_intro"),
        NPC(MAP_SIZE // 2,       MAP_SIZE // 2 - 120, "Gatekeeper", "portal",     "portal_intro"),
        NPC(MAP_SIZE // 2 - 150, MAP_SIZE // 2 + 150, "Seer",       "seer",       "seer_intro"),
    ]

    # ── restore visit memory from previous hub visit ─────────────────────
    _carry_visit_counts(old_npcs, game.npcs)

    # ── update each NPC's dialogue_id to reflect current situation ───────
    room_type_name = _next_room_type_name(game)
    for npc in game.npcs:
        npc.dialogue_id = npc.greet(
            player         = game.player,
            room_number    = game.room_number,
            rooms_to_boss  = ROOMS_TO_BOSS,
            room_type_name = room_type_name,
        )

    game.collision.clear()
    game.collision.add_entities(game.npcs)
    game.collision.add_rect(game.portal_rect)


def enter_room(game):
    game.collision.clear()
    game.state = GameState.ROOM
    game.player.move_to_room_spawn()
    game.camera.reset(game.player.rect)
    game.dialogue.close()
    clear_active_enemies(game)
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
    clear_active_enemies(game)
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
