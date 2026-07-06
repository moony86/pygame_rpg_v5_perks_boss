import os
import statistics
import sys
from pathlib import Path
from time import perf_counter

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame

from game import Game
from game_state import GameState
from systems.perk_system import PERK_EFFECTS


BUILD_KEYS = {
    "Engineer": ("impact_drive", "kinetic_rounds", "overclock", "blade_drone", "bomber_drone"),
    "Vampire": ("sanguine_rounds", "vital_core", "blood_bat", "blood_trail"),
    "Ninja": ("phantom_step", "shadow_shuriken", "scout_boots"),
    "Gunslinger": ("rapid_fire", "power_rounds", "hollow_point", "split_shot", "needle_rounds", "critical_spark", "explosive_rounds"),
}


def grant_full(player, key):
    apply_effect, legendary_effect = PERK_EFFECTS[key]
    for pick in range(4):
        if pick == 3:
            legendary_effect(player)
        else:
            apply_effect(player)
        player.perk_counts[key] = player.perk_counts.get(key, 0) + 1


def apply_build(game, build_name):
    if build_name == "Base":
        return
    for key in BUILD_KEYS[build_name]:
        if key in PERK_EFFECTS:
            grant_full(game.player, key)


def run_case(label, enemy_count, build_name="Base", frames=180):
    game = Game()
    game.state = GameState.ROOM
    game.rooms.choose_next_room(1)
    game.room_flow.countdown_timer = 0.0
    game.room_flow.active = False
    apply_build(game, build_name)
    game.horde.spawn_test(game, enemy_count)
    frame_ms = []
    for frame in range(frames):
        start = perf_counter()
        if frame % 6 == 0:
            game.shooting.try_shoot(game.player, game.projectiles, audio=None)
        game.update(1 / 60)
        game.draw()
        frame_ms.append((perf_counter() - start) * 1000.0)
    metrics = game.horde.last_metrics.copy()
    avg_ms = sum(frame_ms) / len(frame_ms)
    p95 = sorted(frame_ms)[min(len(frame_ms) - 1, int(len(frame_ms) * 0.95))]
    result = {
        "label": label,
        "fps_avg": 1000.0 / avg_ms if avg_ms > 0 else 0.0,
        "p95_frame_ms": p95,
        "worst_spike_ms": max(frame_ms),
        "enemy_update_ms": metrics.get("enemy_update_ms", 0.0),
        "projectile_collision_ms": metrics.get("combat_collision_ms", 0.0),
        "draw_ms": metrics.get("draw_ms", 0.0),
        "active_projectiles": len(game.projectiles) + len(game.enemy_bullets),
        "active_pickups": len(getattr(game.loot, "pickups", [])),
        "active_effects": len(getattr(game.effects, "floating_texts", [])) + len(getattr(game.effects, "rings", [])) + len(getattr(game.effects, "sprite_effects", [])),
        "real_enemies": metrics.get("real", 0),
        "virtual_enemies": metrics.get("virtual", 0),
    }
    return result


def main():
    pygame.init()
    cases = [
        ("A 100 enemies base pistol", 100, "Base"),
        ("B 200 enemies base pistol", 200, "Base"),
        ("C 300 enemies Engineer full build", 300, "Engineer"),
        ("D 300 enemies Vampire full build", 300, "Vampire"),
        ("E 300 enemies Ninja full build", 300, "Ninja"),
        ("F 300 enemies Gunslinger projectile-heavy", 300, "Gunslinger"),
    ]
    for label, count, build in cases:
        result = run_case(label, count, build)
        print(
            f"{result['label']} | FPS avg {result['fps_avg']:.1f} | p95 {result['p95_frame_ms']:.2f}ms | "
            f"worst {result['worst_spike_ms']:.2f}ms | enemy {result['enemy_update_ms']:.2f}ms | "
            f"combat {result['projectile_collision_ms']:.2f}ms | draw {result['draw_ms']:.2f}ms | "
            f"proj {result['active_projectiles']} | pickups {result['active_pickups']} | fx {result['active_effects']} | "
            f"real {result['real_enemies']} | virtual {result['virtual_enemies']}"
        )


if __name__ == "__main__":
    main()
