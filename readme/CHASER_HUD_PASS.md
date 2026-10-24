# Focused chaser / HUD pass

- Crystal chaser: visual-only idle locomotion, pressure squash before the existing
  burst threshold, burst stretch, hit reaction and a 240 ms shrinking death echo.
- This is procedural animation of the current PNG, not a new authored sprite sheet.
- No AI, damage, speed, collision, reward or attack-timing changes.
- Compact HUD: health, level, gold, XP, skill readiness; optional vampire resources.
- Hold Tab for the previous detailed stats and route map. Release to restore compact view.
- First-run control hint expires after eight seconds of run time instead of repeating
  in each room. Door guidance remains after clearing. Persistent debug-style message
  text is only visible with Tab.
- Hub artwork and other enemy animations are intentionally unchanged.

Verification: `tools/check_chaser_hud.py`, `tools/headless_checks.py`,
`tools/check_demo_fixes.py`; private browser checks exercise the shared game loop.
Browser performance does not establish desktop performance or mobile support.
