# Rendering and reuse performance pass

Scope: performance only. Menu and drone artwork are deliberately unchanged in this pass.
No damage, fire interval, collision, projectile lifetime, reward or ability balance changes.
No gameplay shot is discarded to satisfy a visual budget.

## Changes

- Decode/trim image sources once and reuse across size/tint variants. Source-frame
  cache has conservative 64-entry / 128 MiB limits, cleared on relevant asset changes.
- Shared prepared pose, alpha and composite-ribbon surfaces replace repeated copies,
  metadata sorting and up to eight blits per straight/curved projectile draw.
- The same actual eight-point history, colors and .12s fade are retained. Composite
  positioning is snapped to the pixel grid (up to one pixel vs per-piece rounding),
  not pixel-identical alpha compositing. Curved homing paths are not straightened.
- VFX caches: 2048 poses / 16 MiB, 8192 faded variants / 32 MiB,
  1024 ribbons / 24 MiB. These are cache limits, not total process memory limits.
- Common VFX, projectile, actor and environment art prepares before the run. First
  preparation measured about 1.8–2s here; unchanged subsequent runs reuse it.
  Edited metadata or source file size/mtime invalidates prepared assets correctly.
- Preparation time is excluded from native simulation clock elapsed time.
- Pistol, drone and ninja projectiles use the existing shared expandable pool.
  Dead shots now return correctly, duplicate returns are ignored, and room/round
  resets recover outstanding slots. It expands at concurrent peak, never drops a shot.
- Existing 96-slot hit-VFX budget now reuses 96 prepared objects rather than allocating
  a new effect for each hit. Particle velocities and target/opacity surfaces are reused.
- Constant-heading projectile bodies reuse their exact rotated image. Direction,
  animation frame, visual key or asset revision changes invalidate the cached pose.
- Far-offscreen projectiles skip drawing only. Physics, collisions and lifetime continue.
- Window scaling reuses its destination surface with the same smoothscale algorithm.
- Profiler counts now include sprite, shot and collection effects.

## Repeatable measurements

Native Python 3.12 / pygame-ce, 1920×1080 offscreen canvas, SDL dummy.
These measure rendering workloads, NOT delivered gameplay FPS on the player's machine.

| Workload | Before median | After median | First render before → after |
|---|---:|---:|---:|
| 200 same-direction projectiles | 23.052 ms | 4.718 ms | 106.778 → 6.552 ms |
| 120 mixed-direction projectiles | 13.322 ms | 3.330 ms | 119.814 → 9.737 ms |

Warm preparation is measured separately in `after.json`; it has not disappeared.
Source results: `debug_screenshots/performance/before.json` and `after.json`.

Full Game.draw A/B, static stress scene: 200 projectiles, 24 enemies, 32 hit effects,
world 1920×1080 scaled to 1280×720. The original eight-piece trail reference took
23.305ms median / 28.210ms p95; cached ribbons took 14.997ms / 16.444ms.
Both modes share the other optimizations, so this isolates ribbon improvement,
not the entire old application. Simulation/update and real display cost are excluded.
Result: `debug_screenshots/performance/full-frame.json`.

## Verification

`tools/check_render_performance.py`: repeated dead-shot reuse (1000 cycles), duplicate
returns, overflow without shot loss, scene clearing, 96 hit-slot reuse, unchanged reload,
one decode across dimensions, cache invalidation, offscreen simulation, exact body-pose
reuse and a before/after straight/curved visual reference.
Original headless, demo, pistol, shot and collection regressions also pass.
Private browser smoke test exercised movement, shooting and dash with live VFX;
it does not establish native-window FPS or full-run difficulty balance.

Next gate: repeat the previously stuttering run in source `main.py` on the player's
Windows machine. Do not infer release readiness or guaranteed 60 FPS from these tests.
