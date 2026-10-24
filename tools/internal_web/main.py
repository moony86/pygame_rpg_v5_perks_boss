"""Private browser entry point. Copied into an isolated staging directory only."""
import asyncio
import json
import os
import sys

os.environ["BLUECUBE_DEV_TOOLS"] = "0"


async def main():
    import pygame
    from game import Game

    game = Game()
    counts = {"shots": 0, "dashes": 0}
    from systems.audio_system import CUE_CHANNELS
    audio_cues=[]
    original_play=game.audio.play
    def logged_play(name):
        if name in CUE_CHANNELS:
            audio_cues.append(name)
            del audio_cues[:-12]
        original_play(name)
    game.audio.play=logged_play

    def shot(_):
        counts["shots"] += 1

    def dash(_):
        counts["dashes"] += 1

    game.events.subscribe("player_shoot", shot)
    game.events.subscribe("player_dash", dash)
    browser = sys.platform == "emscripten"
    if browser:
        import platform
        from urllib.parse import parse_qs
        query = parse_qs(str(platform.window.location.search).lstrip("?"))
        if query.get("scene") in (["arena"], ["ninja"], ["objects"], ["boss"], ["cards"], ["brute"], ["actors"], ["vfx"], ["drones"], ["boss_eyes"], ["boss_parry"], ["boss_summon"]):
            game.reset_run()
            game.stage.start_stage()
            if query.get('scene') == ['drones']:
                # Explicit visual QA build: existing machine levels and real enemy AI.
                from entities.enemy import Enemy, EnemyType
                from systems.perk_system import refresh_engineer_machines
                game.player.engineer_gun_level = 1
                game.player.engineer_blade_level = 1
                game.player.engineer_bomber_level = 1
                refresh_engineer_machines(game.player)
                game.player.reset_engineer_scene_state()
                game.prototype_room.spawn_plan = ()
                game.prototype_room.pending.clear()
                game.enemies = [Enemy(1250, 540, EnemyType.BRUTE), Enemy(600, 300, EnemyType.RANGED)]
            if query.get('scene') == ['vfx']:
                # Isolated existing explosive perk for visual QA, not a new starter build.
                from entities.enemy import Enemy, EnemyType
                game.player.explosive_rounds=True
                game.prototype_room.spawn_plan=()
                game.prototype_room.pending.clear()
                game.enemies=[Enemy(1150,540,EnemyType.BRUTE),Enemy(800,300,EnemyType.RANGED)]
            if query.get('scene') == ['actors']:
                # Mixed real-AI visual fixture only; not authored room balance.
                from entities.enemy import Enemy, EnemyType
                game.prototype_room.spawn_plan = ()
                game.prototype_room.pending.clear()
                game.enemies=[Enemy(x,y,kind) for x,y,kind in (
                    (700,300,EnemyType.HUNTER),(1200,300,EnemyType.ELITE),
                    (1100,760,EnemyType.LOOT),(600,700,EnemyType.CHASER_FAST),
                    (1250,700,EnemyType.CHASER_TANK))]
            if query.get('scene') == ['brute']:
                # Isolated real-AI visual fixture, not normal room balance.
                from entities.enemy import Enemy, EnemyType
                game.prototype_room.spawn_plan = ()
                game.prototype_room.pending.clear()
                game.player.rect.center = (980,540)
                game.enemies = [Enemy(1250,540,EnemyType.BRUTE)]
                game.camera.reset(game.player.rect)
            if query.get('scene') in (['boss'],['boss_eyes'],['boss_parry'],['boss_summon']):
                node = next(n for n in game.stage.nodes if n.room.boss)
                game.stage.current_pos = node.grid_pos
                game.stage._enter_current_room()
                if query.get('scene')==['boss_summon']:
                    boss=next(e for e in game.enemies if e.encounter is not None)
                    boss.health=boss.max_health*2/3
                    boss.encounter.started=True
                    boss.encounter.next_phase=2
                    boss.encounter.state='transition'
                    boss.encounter.timer=1.
                if query.get('scene') in (['boss_eyes'],['boss_parry']):
                    # Explicit phase fixture for input/visual QA, not a normal victory.
                    boss=next(e for e in game.enemies if e.encounter is not None)
                    phase=2 if query.get('scene')==['boss_eyes'] else 3
                    boss.phase=boss.encounter.phase=phase
                    boss.encounter.started=True
                    boss.encounter.state='guard'
                    boss.encounter.timer=.5
                    boss.health=boss.max_health*(2/3 if phase==2 else 1/3)
                    if phase==2:
                        boss.player_rect=game.player.rect
                        boss.encounter.arena_solids=tuple(game.collision.get_colliders())
                        boss.encounter.spawn_eyes(game.enemies)
                    else:
                        from systems.perk_system import PERK_EFFECTS
                        PERK_EFFECTS['phantom_step'][0](game.player)
            if query.get('scene') == ['cards']:
                from systems.perk_system import PERKS
                from game_state import GameState
                game.perks.current_options = [game.perks._option_for_player(next(p for p in PERKS if p['key']==key),game.player)
                                              for key in ('rapid_fire','blade_drone','vital_core')]
                game.previous_state = GameState.ROOM
                game.state = GameState.PERK_SELECT
            if query.get('scene') == ['objects']:
                from entities.pickup import Pickup
                game.player.health = 80
                game.prototype_room.elapsed = -30  # Isolated interaction fixture.
                game.loot.pickups = [Pickup(660, 540, 'heal_potion', 25), Pickup(1260, 540, 'time_stop', 2)]
                for pickup in game.loot.pickups:
                    pickup.velocity.update(0, 0)
            if query.get("scene") == ["ninja"]:
                # Explicit low-health QA fixture, not the normal game's balance.
                from entities.enemy import Enemy
                from systems.perk_system import PERK_EFFECTS
                PERK_EFFECTS["phantom_step"][0](game.player)
                game.player.rect.center = (700, 240)
                game.prototype_room.spawn_plan = ()
                game.prototype_room.pending.clear()
                game.enemies = [Enemy(x, 240) for x in (800, 930, 1060, 1190)]
                for enemy, x in zip(game.enemies, (800, 930, 1060, 1190)):
                    enemy.rect.center = (x, 240)
                    enemy.health = 1
                    enemy.speed = 0
                game.camera.reset(game.player.rect)

    # No clock.tick(FPS) here: the browser must regain control every frame.
    last = pygame.time.get_ticks()
    frame = 0
    try:
        while True:
            now = pygame.time.get_ticks()
            dt = min(0.05, max(0.001, (now - last) / 1000.0))
            last = now
            game.run_frame(dt)
            frame += 1
            if browser:
                snapshot = {
                    "internal_test_only": True,
                    "frame": frame,
                    "state": game.state.name,
                    "position": list(game.player.rect.center),
                    "health": game.player.health,
                    "time_stop": game.player.enemy_time_stop_timer,
                    "weapon": game.player.active_weapon_key,
                    "audio_cues":list(audio_cues),
                    "projectiles": len(game.projectiles),
                    "enemies": len(game.enemies),
                    "dash_timer": game.player.dash_timer,
                    "chain_hops": game.player.ninja_chain_hops,
                    "chain_kills": game.player.ninja_chain_kills,
                    "shot_timer": game.player.gun_shoot_timer,
                    "drone_helper": game.player.engineer_helper_enabled,
                    "drone_blades": len(game.player.engineer_blade_positions),
                    "drone_bomber": game.player.engineer_bomber_state,
                    "boss": next(({'phase':e.phase,'state':e.encounter.state,'timer':e.encounter.timer,
                                   'health':e.health,'eyes':len(e.encounter.living_eyes()),
                                   'lift':e.encounter.lift,'guards':len(e.encounter.living_guards()),
                                   'reflections':e.encounter.reflections,'position':list(e.rect.center)}
                                  for e in game.enemies if getattr(e,'encounter',None) is not None),None),
                    "aim": list(game.player.aim_direction),
                    "muzzle": list(game.player.weapon_muzzle_position()),
                    **counts,
                }
                platform.window.eval("window.__cubeProbe = " + json.dumps(snapshot))
            await asyncio.sleep(0)
    except SystemExit:
        pass


asyncio.run(main())
