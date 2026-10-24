import pygame
from systems.projectile_pool import clear_world_projectiles

from settings import ROOMS_TO_BOSS

from game_state import GameState
from entities.enemy import EnemyType
from systems.room_system import RoomType, room_type_for_number
from systems.room_layout import generate_room_obstacles
from systems.room_bounds import HUB_ROOM_BOUNDS, current_room_bounds, reset_room_bounds, set_room_bounds


def clear_active_enemies(game):
    horde = getattr(game, "horde", None)
    if horde is not None:
        horde.pending.clear()
        horde.enabled = False
        horde.spatial_grid.clear()
    if hasattr(game, "enemy_pool"):
        game.enemy_pool.release_many(game.enemies)
    game.enemies.clear()


def _increment_npc_visits(game):
    for npc in getattr(game, "npcs", []):
        npc.visit_count = getattr(npc, "visit_count", 0) + 1


def _carry_visit_counts(old_npcs, new_npcs):
    counts = {npc.role: getattr(npc, "visit_count", 0) for npc in old_npcs}
    for npc in new_npcs:
        if npc.role in counts:
            npc.visit_count = counts[npc.role]


def _next_room_type_name(game):
    stage = getattr(game, "stage", None)
    if stage is not None and stage.rooms:
        return stage.rooms[0].room_type.name
    return room_type_for_number(game.room_number).name


def _refresh_npc_dialogues(game):
    room_type_name = _next_room_type_name(game)
    for npc in game.npcs:
        if npc.role == "seer" and getattr(game, "stage", None) is not None:
            npc.dialogue_id = "seer_stage"
            continue
        if hasattr(npc, "greet"):
            npc.dialogue_id = npc.greet(
                player=game.player,
                room_number=game.room_number,
                rooms_to_boss=ROOMS_TO_BOSS,
                room_type_name=room_type_name,
            )


def enter_hub(game):
    if hasattr(game, "prototype_room"):
        game.prototype_room.active = False
    set_room_bounds(HUB_ROOM_BOUNDS)
    if hasattr(game, "dev_tools"):
        game.dev_tools.clear_scene_transition_state()
    _increment_npc_visits(game)
    old_npcs = getattr(game, "npcs", [])

    game.state = GameState.HUB
    game.player.move_to_hub_spawn()
    if hasattr(game.player, "reset_ninja_scene_state"):
        game.player.reset_ninja_scene_state()
    if hasattr(game.player, "reset_engineer_scene_state"):
        game.player.reset_engineer_scene_state()
    if hasattr(game.player, "reset_vampire_scene_state"):
        game.player.reset_vampire_scene_state()
    game.player.heal(game.player.regen_on_room_clear)
    game.camera.reset(game.player.rect)
    game.dialogue.close()
    game.gatekeeper_ready = False
    game.combat.reset()
    if hasattr(game, "room_flow"):
        game.room_flow.clear_scene()
    clear_active_enemies(game)
    clear_world_projectiles(game)
    game.enemy_bullets.clear()
    if hasattr(game, "loot"):
        game.loot.reset()
    game.events.emit("state_hub")
    bounds = current_room_bounds()

    game.portal_rect = game.prefabs.spawn_prefab("portal_hub", x=bounds.centerx - 45, y=105)

    game.npcs = [
        game.prefabs.spawn_prefab("npc_blacksmith", x=250, y=390),
        game.prefabs.spawn_prefab("npc_healer", x=1625, y=390),
        game.prefabs.spawn_prefab("npc_gatekeeper", x=bounds.centerx - 23, y=245),
        game.prefabs.spawn_prefab("npc_seer", x=255, y=840),
        game.prefabs.spawn_prefab("npc_tea_vendor", x=1625, y=840),
    ]

    _carry_visit_counts(old_npcs, game.npcs)
    _refresh_npc_dialogues(game)

    game.room_obstacles = []
    game.collision.clear()
    game.collision.add_entities(game.npcs)
    game.collision.add_rect(game.portal_rect)
    from systems.hub_presentation import HUB
    for rect in HUB['colliders']:
        game.collision.add_rect(pygame.Rect(rect))


def enter_room(game):
    if hasattr(game, "prototype_room"):
        game.prototype_room.active = False
    reset_room_bounds()
    if hasattr(game, "dev_tools"):
        game.dev_tools.clear_scene_transition_state()
    game.collision.clear()
    game.room_obstacles = []
    game.state = GameState.ROOM
    game.player.cancel_tea()
    game.player.move_to_room_spawn()
    if hasattr(game.player, "reset_ninja_scene_state"):
        game.player.reset_ninja_scene_state()
    if hasattr(game.player, "reset_engineer_scene_state"):
        game.player.reset_engineer_scene_state()
    if hasattr(game.player, "reset_vampire_scene_state"):
        game.player.reset_vampire_scene_state()
    game.camera.reset(game.player.rect)
    game.dialogue.close()
    clear_active_enemies(game)
    clear_world_projectiles(game)
    game.enemy_bullets.clear()
    if hasattr(game, "loot"):
        game.loot.reset()
    game.room_kills = 0
    game.events.emit("state_room")

    room_type = game.rooms.choose_next_room(game.room_number)
    if hasattr(game, "room_flow"):
        game.room_flow.start_for_room(room_type)
    game.spawn.reset(game.room_number, room_type)
    game.waves.reset(game.room_number, room_type, game.player)
    if room_type not in (RoomType.TREASURE,):
        game.rooms.target_kills = sum(wave.get("count", 0) for wave in game.waves.waves)
    game.room_exit_open = False
    game.room_obstacles = generate_room_obstacles(game.room_number, room_type)
    for obstacle in game.room_obstacles:
        game.collision.add_rect(obstacle)

    if room_type == RoomType.TREASURE:
        game.rooms.target_kills = 2
        bounds = current_room_bounds()
        loot_positions = (
            (bounds.centerx - 120, bounds.centery - 170),
            (bounds.centerx + 120, bounds.centery - 170),
        )
        for x, y in loot_positions:
            loot = game.prefabs.spawn_prefab(
                "enemy_loot",
                x=x,
                y=y,
                difficulty=1.0 + game.room_number * 0.18,
            )
            game.enemies.append(loot)
            game.effects.ring(loot.rect.center, radius=120, life=0.7, width=4)
        game.message = "Treasure room: chase the Loot Beasts for 15 seconds."
        return

    game.message = f"{game.rooms.display_name()} Room started."

    if room_type == RoomType.CURSE:
        game.message += " Rewards x2."

    game.audio.play("wave_start")


def enter_boss(game):
    if hasattr(game, "prototype_room"):
        game.prototype_room.active = False
    reset_room_bounds()
    if hasattr(game, "dev_tools"):
        game.dev_tools.clear_scene_transition_state()
    game.collision.clear()
    game.room_obstacles = []
    game.state = GameState.BOSS
    game.player.cancel_tea()
    if hasattr(game, "room_flow"):
        game.room_flow.clear_scene()
    game.player.move_to_room_spawn()
    if hasattr(game.player, "reset_ninja_scene_state"):
        game.player.reset_ninja_scene_state()
    if hasattr(game.player, "reset_engineer_scene_state"):
        game.player.reset_engineer_scene_state()
    if hasattr(game.player, "reset_vampire_scene_state"):
        game.player.reset_vampire_scene_state()
    game.camera.reset(game.player.rect)
    clear_active_enemies(game)
    clear_world_projectiles(game)
    game.enemy_bullets.clear()
    if hasattr(game, "loot"):
        game.loot.reset()
    game.events.emit("state_boss")
    game.events.emit("boss_spawned")
    bounds = current_room_bounds()

    boss_difficulty = (
        1.25
        + game.room_number * 0.68
        + max(0, game.player.level - 1) * 0.30
        + game.player.build_power_score() * 0.20
    )
    boss = game.prefabs.spawn_prefab(
        "enemy_boss",
        x=bounds.centerx,
        y=bounds.centery - 220,
        difficulty=boss_difficulty,
    )

    game.enemies.append(boss)
    game.message = f"Boss awakened. Threat x{boss_difficulty:.1f}."
    game.audio.play("boss_spawn")
    game.effects.ring(boss.rect.center, radius=180, life=1.0, width=5)
