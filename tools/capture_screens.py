import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame
import settings
settings.DEBUG_CAPTURE_SCREENS = True

from game import Game
from game_state import GameState
from systems.scene_system import enter_hub, enter_room, enter_boss
from systems.room_system import RoomType
from entities.enemy import EnemyType

OUT_DIR = ROOT / "debug_screenshots"


def tick(game, seconds, step=0.1):
    elapsed = 0.0
    while elapsed < seconds:
        dt = min(step, seconds - elapsed)
        game.update(dt)
        elapsed += dt


def force_room(game, room_type, target=6, survival_time=12):
    def choose(room_number):
        game.rooms.room_type = room_type
        game.rooms.room_time = 0.0
        game.rooms.banner_timer = 0.0
        game.rooms.reward_multiplier = 2 if room_type == RoomType.CURSE else 1
        if room_type == RoomType.ELITE:
            game.rooms.target_kills = 1
        elif room_type == RoomType.TREASURE:
            game.rooms.target_kills = 0
        elif room_type == RoomType.SURVIVAL:
            game.rooms.target_kills = 999
        else:
            game.rooms.target_kills = target
        game.rooms.survival_time = survival_time
        return room_type

    game.rooms.choose_next_room = choose
    enter_room(game)


def set_small_waves(game, per_wave=2, wave_count=2):
    game.waves.waves = [
        {"count": per_wave, "types": [EnemyType.CHASER]},
        {"count": per_wave, "types": [EnemyType.CHASER, EnemyType.RANGED]},
    ][:wave_count]
    game.waves.current_wave_index = 0
    game.waves._start_current_wave()


def kill_all(game):
    for enemy in list(game.enemies):
        if enemy.alive:
            enemy.alive = False
            game.room_kills += 1
    game.enemies = [e for e in game.enemies if e.alive]


def save(game, out_dir, name):
    game.draw()
    path = out_dir / f"{name}.png"
    pygame.image.save(game.screen, str(path))
    return path


def new_game():
    game = Game()
    game.clock.tick(60)
    return game


def capture_all(label="before"):
    target = OUT_DIR / label
    target.mkdir(parents=True, exist_ok=True)

    captured = []

    game = new_game()
    captured.append(save(game, target, "01_main_menu"))

    game = new_game()
    enter_hub(game)
    captured.append(save(game, target, "02_hub"))

    game = new_game()
    force_room(game, RoomType.COMBAT, target=4)
    set_small_waves(game, per_wave=2)
    tick(game, 0.6)
    captured.append(save(game, target, "03_combat_wave1"))

    game = new_game()
    force_room(game, RoomType.COMBAT, target=4)
    set_small_waves(game, per_wave=2)
    while game.waves.wave_state != "clearing":
        tick(game, 0.2)
    kill_all(game)
    tick(game, 0.2)
    tick(game, 2.6)
    captured.append(save(game, target, "04_combat_wave_incoming"))

    game = new_game()
    force_room(game, RoomType.COMBAT, target=4)
    set_small_waves(game, per_wave=2)
    while game.waves.wave_state != "clearing":
        tick(game, 0.2)
    kill_all(game)
    tick(game, 0.2)
    tick(game, 2.6)
    tick(game, 2.1)
    while game.waves.wave_state != "clearing":
        tick(game, 0.2)
    kill_all(game)
    tick(game, 0.3)
    captured.append(save(game, target, "05_combat_room_cleared_portal"))

    game = new_game()
    force_room(game, RoomType.SURVIVAL, survival_time=12)
    tick(game, 1.2)
    captured.append(save(game, target, "06_survival_room"))

    game = new_game()
    force_room(game, RoomType.CURSE, target=4)
    set_small_waves(game, per_wave=2)
    tick(game, 0.8)
    captured.append(save(game, target, "07_curse_room"))

    game = new_game()
    force_room(game, RoomType.ELITE)
    tick(game, 0.6)
    captured.append(save(game, target, "08_elite_room"))

    game = new_game()
    enter_boss(game)
    captured.append(save(game, target, "09_boss_phase1_shield"))

    game = new_game()
    enter_boss(game)
    boss = game.enemies[0]
    boss.phase = 2
    boss.shield = 0
    boss.health = int(boss.max_health * 0.65)
    captured.append(save(game, target, "10_boss_phase2"))

    game = new_game()
    enter_boss(game)
    boss = game.enemies[0]
    boss.phase = 3
    boss.rage = True
    boss.shield = 0
    boss.health = int(boss.max_health * 0.25)
    captured.append(save(game, target, "11_boss_phase3_rage"))

    game = new_game()
    enter_hub(game)
    game.perks.roll_options()
    game.state = GameState.PERK_SELECT
    captured.append(save(game, target, "12_perk_selection"))

    game = new_game()
    enter_hub(game)
    game.previous_state = GameState.HUB
    game.state = GameState.PAUSED
    captured.append(save(game, target, "13_pause_menu"))

    game = new_game()
    enter_room(game)
    game.state = GameState.GAME_OVER
    captured.append(save(game, target, "14_game_over"))

    game = new_game()
    enter_boss(game)
    game.state = GameState.WIN
    captured.append(save(game, target, "15_win_screen"))

    return captured


if __name__ == "__main__":
    paths = capture_all(sys.argv[1] if len(sys.argv) > 1 else "before")
    for path in paths:
        print(path)
    pygame.quit()