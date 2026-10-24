import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from definitions.prototype_room_definitions import (
    COMBAT_LAYOUT_VARIANTS,
    PROTOTYPE_ACTIVE_ENEMY_CAP,
    PROTOTYPE_DOORS,
    PROTOTYPE_OBSTACLES,
    PROTOTYPE_SPAWN_PLAN,
)
from game import Game
from settings import PERK_PICK_LIMIT
from entities.enemy import EnemyType
from entities.enemy import Enemy
from entities.projectile import Projectile
from systems.perk_system import PERK_EFFECTS
from systems.room_bounds import HUB_ROOM_BOUNDS, current_room_bounds
from systems.shooting_system import ShootingSystem
from systems.xp_budget import (
    STAGE_COMPLETION_XP,
    STAGE_EXPECTED_ENEMY_XP,
    level_for_cumulative_xp,
)
from systems.xp_progression import cumulative_xp_for_level
from states.combat_state import handle_combat_events


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


class TraceEnemy:
    def __init__(self, rect, health=30, stacks=1):
        self.rect = rect
        self.health = health
        self.max_health = health
        self.alive = True
        self.type = EnemyType.CHASER
        self.vampire_wound_stacks = stacks
        self.vampire_wound_timer = 5.0

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.alive = False
            return True
        return False


def grant_full_vampire(player):
    for key in ("sanguine_rounds", "battle_recovery", "vital_core", "blood_bat", "blood_trail"):
        apply_effect, legendary_effect = PERK_EFFECTS[key]
        for pick in range(PERK_PICK_LIMIT):
            if pick == PERK_PICK_LIMIT - 1:
                legendary_effect(player)
            else:
                apply_effect(player)
            player.perk_counts[key] = player.perk_counts.get(key, 0) + 1


def trace_vampire_combo(game):
    player = game.player
    grant_full_vampire(player)
    player.reset_vampire_scene_state()
    player.vampire_blood_per_kill = 0
    player.vampire_bat_pos.update((880, 540))
    first = TraceEnemy(pygame.Rect(900, 520, 34, 34), health=20, stacks=3)
    second = TraceEnemy(pygame.Rect(980, 520, 34, 34), health=20, stacks=2)

    game.combat.update(0.05, player, [], [first, second], [])
    assert_true(player.vampire_bat_state == "diving", "Vampire bat should engage wounded prototype target immediately")
    game.combat.update(0.10, player, [], [first, second], [])
    assert_true(player.vampire_bat_state == "feeding" and not first.alive, "Vampire bat should kill first wounded target")
    carried = player.vampire_bat_carried_blood
    game.combat.update(0.10, player, [], [first, second], [])
    assert_true(player.vampire_bat_state == "diving", "Vampire bat should chain before returning when wounded targets remain")
    assert_true(player.vampire_bat_carried_blood == carried and carried > 0, "Vampire bat should keep carried Blood mid-chain")

    player.vampire_bat_chain_kills = player.vampire_bat_chain_cap
    game.combat.update(0.15, player, [], [second], [])
    game.combat.update(0.10, player, [], [second], [])
    assert_true(player.vampire_bat_state == "returning", "Vampire bat should return after bounded chain cap")
    blood_before_bank = player.vampire_blood
    player.vampire_bat_pos.update(player.rect.center)
    game.combat.update(0.10, player, [], [second], [])
    assert_true(player.vampire_blood > blood_before_bank, "Vampire bat should bank carried Blood once on return")

    trail_target = TraceEnemy(pygame.Rect(player.rect.x + 42, player.rect.y, 34, 34), health=80, stacks=2)
    player.dash_timer = 0.0
    player.move_direction.update(1, 0)
    trail_blood_before = player.vampire_blood
    game.combat.update(0.10, player, [], [trail_target], [])
    assert_true(player.vampire_blood > trail_blood_before, "Vampire Blood Trail should harvest while moving without Dash")


def clear_active_stage_room(game):
    for _ in range(800):
        for enemy in game.enemies:
            enemy.alive = False
        game.enemy_pool.release_many(game.enemies)
        game.enemies.clear()
        game.prototype_room.update(0.20)
        if game.prototype_room.ready_to_clear():
            game.prototype_room.open_exit()
            return
    raise AssertionError(f"stage room did not clear: {game.prototype_room.debug_snapshot()}")


def trace_enemy_obstacle_collision(game):
    obstacle = game.room_obstacles[0]
    enemy = Enemy(obstacle.left - 74, obstacle.centery - 28, EnemyType.CHASER, difficulty=1.0)
    before_right = enemy.rect.right
    enemy.update(0.25, pygame.Rect(obstacle.centerx + 220, obstacle.centery - 18, 36, 36), [obstacle])
    assert_true(enemy.rect.right <= obstacle.left, "enemy should be blocked by prototype obstacle")
    assert_true(enemy.rect.right >= before_right, "enemy should still move until blocked")

    ranged = Enemy(obstacle.left - 110, obstacle.centery - 28, EnemyType.RANGED, difficulty=1.0)
    ranged.attack_cooldown = 0.0
    action = ranged.update(0.70, pygame.Rect(obstacle.right + 70, obstacle.centery - 17, 34, 34), [obstacle])
    assert_true(action is None and ranged.windup_action is None, "ranged enemy should not shoot through obstacle line of sight")

    jumper = Enemy(obstacle.left - 74, obstacle.centery - 28, EnemyType.JUMPER, difficulty=1.0)
    jumper.leap_timer = 0.25
    jumper.leap_velocity = pygame.Vector2(900, 0)
    jumper.update(0.30, pygame.Rect(obstacle.right + 100, obstacle.centery - 17, 34, 34), [obstacle])
    assert_true(not jumper.rect.colliderect(obstacle), "jumper leap landing should resolve outside prototype obstacle")

    chaser = Enemy(obstacle.left - 130, obstacle.centery - 17, EnemyType.CHASER, difficulty=1.0)
    chaser.chase_pressure_timer = 99.0
    chaser.chaser_burst_cooldown = 0.0
    chaser.update(0.20, pygame.Rect(obstacle.right + 90, obstacle.centery - 17, 34, 34), [obstacle])
    assert_true(chaser.chaser_burst_timer == 0.0, "chaser should not start burst through obstacle")

    brute = Enemy(obstacle.left - 170, obstacle.centery - 26, EnemyType.BRUTE, difficulty=1.0)
    brute.attack_cooldown = 0.0
    brute.update(0.55, pygame.Rect(obstacle.right + 120, obstacle.centery - 18, 34, 34), [obstacle])
    assert_true(brute.windup_action != "brute_charge", "brute should not wind up charge without line of sight")

    seeker = Enemy(obstacle.left - 90, obstacle.top - 80, EnemyType.RANGED, difficulty=1.0)
    direction = pygame.Vector2(1, 1).normalize()
    first = seeker._obstacle_seek_direction(direction)
    second = seeker._obstacle_seek_direction(pygame.Vector2(1, -1).normalize())
    assert_true(first == second and seeker.path_commit_timer > 0.0, "obstacle pathing should commit briefly instead of flip-flopping")

    bullet = Projectile(obstacle.left - 24, obstacle.centery, pygame.Vector2(1, 0), damage=10, speed=900)
    game.projectiles = [bullet]
    game.update(0.05)
    assert_true(not bullet.alive, "player projectiles should be destroyed by room obstacles")


def trace_rapid_fire_timer_normalization(game):
    shooting = ShootingSystem()
    player = game.player
    player.fire_rate_multiplier = 1.0
    player.aim_direction.update(1, 0)
    projectiles = []
    assert_true(shooting.try_shoot(player, projectiles), "baseline shot should fire")
    before = shooting.shoot_timer
    player.fire_rate_multiplier = 2.0
    shooting.try_shoot(player, projectiles)
    assert_true(shooting.shoot_timer <= before and shooting.shoot_timer <= 0.2251, "rapid_fire should clamp existing shot timer to new interval")


def trace_movement_pickup(game):
    assert_true(len(game.movement_pickups) > 0, "stage room should place movement pickups near obstacles")
    pickup = game.movement_pickups[0]
    assert_true(not game.player.rect.colliderect(pickup["rect"]), "movement pickup should not spawn under the player")
    game.player.dash_cooldown_timer = 3.0
    game.player.ghost_timer = 0.0
    game.player.rect.center = pickup["rect"].center
    game.update_movement_pickups(0.1)
    assert_true(game.player.dash_cooldown_timer == 0.0, "movement pickup should refresh Dash cooldown")
    assert_true(game.player.ghost_timer > 0, "movement pickup should grant temporary speed boost")
    assert_true(not pickup["alive"], "movement pickup should deactivate after collection")
    game.update_movement_pickups(11.9)
    assert_true(not pickup["alive"], "movement pickup should stay inactive before respawn timer")
    assert_true(pickup["respawn_timer"] <= 3.0, "movement pickup should enter visible forming state near respawn")
    game.update_movement_pickups(0.2)
    assert_true(pickup["alive"], "movement pickup should respawn after its timer")
    boost = game.player.ghost_timer
    game.player.update(0.5, [])
    assert_true(game.player.ghost_timer < boost, "movement pickup speed boost should expire over time")


def trace_space_dash_input(game):
    game.player.skill_cooldown_timer = 0.0
    game.player.dash_timer = 0.0
    game.player.dash_cooldown_timer = 0.0
    handle_combat_events(game, pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_q}))
    assert_true(game.player.dash_timer == 0.0, "Q should no longer trigger Dash in combat")
    handle_combat_events(game, pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))
    handle_combat_events(game, pygame.event.Event(pygame.KEYUP, {"key": pygame.K_SPACE}))
    assert_true(game.player.dash_timer > 0.0, "Space should trigger Dash in combat")


def trace_stage_sequence(game):
    assert_true(getattr(game, "horde", None) is None, "normal Stage trace should not instantiate HordeSystem before entry")
    game.stage.start_stage()
    assert_true(getattr(game, "horde", None) is None, "normal Stage entry should not instantiate HordeSystem")
    assert_true(game.stage.active, "stage should become active")
    assert_true(len(game.stage.rooms) == 8, "Stage 1 should contain 8 small rooms")
    assert_true(game.stage.rooms[0].spawn_plan and len(game.stage.rooms[0].spawn_plan) == 39, "stage room 1 should use scaled spawn plan")
    assert_true(len(game.stage.rooms[5].spawn_plan) == 64, "late combat rooms should increase spawn throughput")
    assert_true(game.prototype_room.elapsed < 0, "stage room should start with pre-combat grace")
    assert_true(current_room_bounds().width == 1920 and current_room_bounds().height == 1080, "stage rooms should use small bounds")
    assert_true(any(node.room.boss for node in game.stage.nodes), "stage map should include a boss node")
    layout_ids = {room.layout.id for room in game.stage.rooms if not room.boss}
    assert_true(len(layout_ids) >= 2, f"stage rooms should use multiple layout variants, got {layout_ids}")
    assert_true(game.prototype_room.layout.id in layout_ids, "active prototype room should receive layout data from stage room")
    boss_node = next(node for node in game.stage.nodes if node.room.boss)
    distances = _stage_node_distances(game.stage)
    assert_true(distances[boss_node.grid_pos] == max(distances.values()), "boss room should be placed at a farthest map node")
    trace_enemy_obstacle_collision(game)
    trace_movement_pickup(game)
    trace_space_dash_input(game)
    trace_rapid_fire_timer_normalization(game)

    game.player.gold = 77
    game.player.level = 1
    game.player.xp = 0
    game.player.xp_to_next = 100
    game.player.pending_level_ups = 0
    game.player.perk_counts["rapid_fire"] = 2
    game.upgrades.levels["power_rounds"] = 2

    visited = []
    cleared_positions = set()
    expected_stage_xp = 0
    while game.stage.active:
        node = game.stage.current_node
        room = node.room
        if node.grid_pos not in cleared_positions:
            visited.append(room.room_type.name)
            blocked_door = game.stage.open_doors()[0] if game.stage.open_doors() else None
            if blocked_door:
                game.player.rect.center = blocked_door[2].center
                assert_true(not game.stage.try_use_door(game.player.rect), "stage doors should stay locked until the room is cleared")
            clear_active_stage_room(game)
            expected_completion_xp = STAGE_COMPLETION_XP[room.index]
            visible_completion_xp = sum(pickup.value for pickup in game.loot.pickups if pickup.pickup_type == "xp")
            assert_true(visible_completion_xp == expected_completion_xp, f"stage room {room.index} completion XP pickup mismatch: {visible_completion_xp}")
            game.player.add_xp(STAGE_EXPECTED_ENEMY_XP[room.index])
            game.loot.collect_remaining(game.player, game.effects, game.audio)
            expected_stage_xp += STAGE_EXPECTED_ENEMY_XP[room.index] + expected_completion_xp
            current_stage_xp = cumulative_xp_for_level(game.player.level) + game.player.xp
            assert_true(game.player.level == level_for_cumulative_xp(expected_stage_xp), f"stage room {room.index} should leave player at budgeted level {level_for_cumulative_xp(expected_stage_xp)}, got {game.player.level}")
            assert_true(current_stage_xp == expected_stage_xp, f"stage room {room.index} should collect budgeted Stage XP, got {current_stage_xp}")
            cleared_positions.add(node.grid_pos)
            assert_true(node.cleared, "cleared stage room should persist cleared state")
            if room.boss:
                assert_true(game.room_exit_open, "cleared boss room should open completion portal")
                game.stage.advance_after_exit()
                break
            assert_true(not game.room_exit_open, "non-boss stage rooms should use edge doors instead of the old fixed center exit")

        next_target = _next_uncleared_stage_step(game.stage, cleared_positions)
        assert_true(next_target is not None, "stage graph traversal should find a connected next room")
        _stage_travel_to(game, next_target)
        if game.stage.current_node.cleared:
            assert_true(game.prototype_room.cleared and not game.enemies, "returning to a cleared room should not reactivate combat")

    assert_true(len(cleared_positions) == len(game.stage.nodes), f"stage traversal should clear every map node, got {len(cleared_positions)}")
    assert_true(visited[-1] == "ELITE", f"boss room should be the final cleared room, got {visited}")
    assert_true(game.stage.completed, "stage should mark completion")
    assert_true(getattr(game, "horde", None) is None, "normal Stage completion should not instantiate HordeSystem")
    assert_true(game.player.gold >= 77, "stage completion should preserve gold")
    assert_true(game.player.level == 1 and game.player.xp == 0 and game.player.pending_level_ups == 0, "stage completion should reset level and pending perks")
    assert_true(game.player.perk_counts == {}, "stage completion should reset perks")
    assert_true(all(value == 0 for value in game.upgrades.levels.values()), "stage completion should reset upgrades")
    assert_true((current_room_bounds().width, current_room_bounds().height) == (HUB_ROOM_BOUNDS.width, HUB_ROOM_BOUNDS.height), "hub should use compact bounds after stage")


def _stage_travel_to(game, target_pos):
    for _door_id, neighbor_pos, rect in game.stage.open_doors():
        if neighbor_pos == target_pos:
            game.player.rect.center = rect.center
            assert_true(game.stage.try_use_door(game.player.rect), "stage door should transition to its linked room")
            return
    raise AssertionError(f"no door from {game.stage.current_pos} to {target_pos}")


def _stage_node_distances(stage):
    distances = {(0, 0): 0}
    queue = [(0, 0)]
    while queue:
        current = queue.pop(0)
        node = stage.node_by_pos[current]
        for target in node.neighbors.values():
            if target in distances:
                continue
            distances[target] = distances[current] + 1
            queue.append(target)
    return distances


def _next_uncleared_stage_step(stage, cleared_positions):
    candidates = [
        node.grid_pos for node in stage.nodes
        if node.grid_pos not in cleared_positions and not node.room.boss
    ]
    if not candidates:
        candidates = [node.grid_pos for node in stage.nodes if node.grid_pos not in cleared_positions]
    if not candidates:
        return None
    start = stage.current_pos
    queue = [(start, [start])]
    seen = {start}
    while queue:
        current, path = queue.pop(0)
        if current in candidates and len(path) > 1:
            return path[1]
        for target in stage.node_by_pos[current].neighbors.values():
            if target in seen:
                continue
            seen.add(target)
            queue.append((target, path + [target]))
    return None


def main():
    game = Game()
    starting_room_number = game.room_number
    game.prototype_room.enter()

    bounds = current_room_bounds()
    assert_true((bounds.width, bounds.height) == (1920, 1080), f"prototype bounds wrong: {bounds}")
    assert_true(tuple(game.camera.offset) == (0, 0), f"static camera should clamp to zero: {game.camera.offset}")
    assert_true(game.prototype_room.total_spawns == len(PROTOTYPE_SPAWN_PLAN), "prototype spawn count mismatch")
    assert_true(PROTOTYPE_ACTIVE_ENEMY_CAP == 10, "prototype active cap should match tuning target")
    assert_true(len(COMBAT_LAYOUT_VARIANTS) >= 3, "combat room should expose default plus alternate layout data")
    assert_true(len(game.room_obstacles) == len(PROTOTYPE_OBSTACLES), "prototype obstacles not installed")
    assert_true(
        len(game.collision.get_colliders()) == len(PROTOTYPE_OBSTACLES),
        "prototype obstacles should be registered as static colliders",
    )
    assert_true(
        not any(game.player.rect.colliderect(obstacle) for obstacle in game.room_obstacles),
        "prototype player spawn overlaps an obstacle",
    )
    for door in PROTOTYPE_DOORS:
        door_clearance = pygame.Rect(0, 0, 180, 180)
        door_clearance.center = (door.x, door.y)
        assert_true(
            not any(door_clearance.colliderect(obstacle) for obstacle in game.room_obstacles),
            f"prototype obstacle blocks {door.id} door approach",
        )

    game.prototype_room.update(0.21)
    assert_true(len(game.prototype_room.pending) == 1, "first door telegraph should be pending before spawn")
    assert_true(len(game.enemies) == 0, "enemy should not spawn before telegraph finishes")

    game.prototype_room.update(0.80)
    assert_true(len(game.enemies) >= 1, "enemy should spawn after telegraph")
    enemy = game.enemies[0]
    assert_true(bounds.rect.contains(enemy.rect), f"spawned enemy outside prototype bounds: {enemy.rect}")

    for _ in range(420):
        for enemy in game.enemies:
            enemy.alive = False
        game.enemy_pool.release_many(game.enemies)
        game.enemies.clear()
        game.prototype_room.update(0.20)

    assert_true(game.prototype_room.ready_to_clear(), f"prototype did not become clear: {game.prototype_room.debug_snapshot()}")
    game.prototype_room.open_exit()
    assert_true(game.room_exit_open, "prototype exit should open on clear")
    assert_true(len(game.loot.pickups) > 0, "prototype reward pickups should spawn")
    assert_true(bounds.rect.contains(game.room_exit_rect), f"exit outside prototype bounds: {game.room_exit_rect}")

    trace_vampire_combo(game)

    game.prototype_room.exit_to_hub()
    bounds = current_room_bounds()
    assert_true((bounds.width, bounds.height) == (HUB_ROOM_BOUNDS.width, HUB_ROOM_BOUNDS.height), "prototype exit should return to compact hub bounds")
    assert_true(game.room_number == starting_room_number, "prototype room must not advance normal room_number")

    trace_stage_sequence(game)

    print("PROTOTYPE_ROOM_TRACE_OK")
    print("bounds=1920x1080 camera=static_offset_0")
    print(
        f"spawns={len(PROTOTYPE_SPAWN_PLAN)} active_cap={PROTOTYPE_ACTIVE_ENEMY_CAP} "
        f"obstacles={len(PROTOTYPE_OBSTACLES)}"
    )
    print("vampire_combo=bat_chain_bounded trail_without_dash=True")
    print("stage_sequence=8_rooms reset_build=True gold_preserved=True enemy_obstacle_collision=True movement_pickup=True layout_variants>=2")
    print("telegraph=0.60s precombat=1.80s spawn_inside_bounds=True clear=True reward=True exit_to_hub=True")


if __name__ == "__main__":
    main()
