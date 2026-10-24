# Heavy enemy presentation

Procedural poses of the existing editable BRUTE PNG: idle breathing, distance-driven
gait, windup compression, charge lean, hit recoil and 260ms stopping compression.
The ground echo reuses `fx_ring`; it is decorative and adds no AoE damage.
The windup uses the shared broken arcane path with a gold palette rather than a solid line.

No speed, damage, charge duration, cooldown, collision, cancellation or reward changes.
The existing charge still lasts .42s and is cancelled if line of sight is lost at release.
Timers advance in update, not draw; paused/time-stopped actors do not advance presentation.

Tests: `tools/check_brute_presentation.py` (4), headless checks (23 groups), ranged
presentation regressions (6). Browser smoke test uses `?scene=brute`: isolated real-AI
enemy with normal health, normal player vulnerability and normal projectiles. This
fixture is not normal room balance and does not validate a complete run.
