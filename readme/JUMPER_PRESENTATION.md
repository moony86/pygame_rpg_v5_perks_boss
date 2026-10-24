# Jumper presentation

Procedural presentation of existing editable PNG art for JUMPER, JUMPER_FAST,
JUMPER_HEAVY. Preparation squash follows real windup progress; the body lifts at
most 12px during the real leap and lands with a 220ms compression/ground echo.
The ground echo reuses the editable `fx_ring` asset, follows actual ground position,
and starts only after existing landing collision resolution. It is not a new AoE.

The dotted magical direction cue replaces the old orange straight windup line.
No trajectory, invulnerability, attack duration, damage, collision or reward changes.
Visual height grants no immunity; the existing ground collision remains authoritative.
Pause/time stop do not advance actor presentation through draw calls.

Checks: `tools/check_jumper_presentation.py`; broader headless and ranged checks.
