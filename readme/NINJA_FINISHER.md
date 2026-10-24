# Ninja sword-dash finisher

The desktop source (`main.py`) and private browser QA use the same Player and
CombatSystem implementation. No executable was rebuilt or published.

## Behaviour

- A Ninja dash with dash-strike damage draws the existing `soward.png` sprite.
  It does not equip or unlock the standalone sword weapon. The pistol remains
  the normal weapon and returns after the sword animation.
- Pistol firing is suppressed during the damaging Ninja dash, not during normal
  movement. Dash damage, enemy health and perk progression are unchanged.
- A lethal dash-strike selects the nearest living non-boss ahead, within 280
  world pixels, inside a 72-pixel half-width lane around the ORIGINAL direction,
  and within a forward cone (dot product >= 0.80).
- Up to four automatic follow-up legs per manually activated dash. No extra
  charges are spent. A victim is hit at most once throughout the chain.
- This is movement, not teleportation. Target selection rejects walls expanded
  by the player's body dimensions. Wall collision, no eligible next target,
  or a surviving enemy on an automatic leg ends that leg.
- Violet local slash/ring plus a 60 ms hit-stop on a sword kill. No repeated
  full-screen white flash. Existing reward, pickup and kill accounting remains
  in CombatSystem. Normal projectile kills do not initiate a chain.
- Scene transitions and restart clear transient chain state.

## Verification

`tools/check_ninja_dash.py`: eight deterministic checks covering a four-enemy
chain, targeting/walls/bosses, no duplicate hits, sweep collision, charge cost,
limits/reset, surviving targets, expiry, and pistol suppression/recovery.

The internal browser `?scene=ninja` is an explicitly artificial QA fixture:
four stationary enemies with 1 health. Real keyboard input produced one manual
dash, three automatic follow-ups and four kills without shots or health loss.
It is not evidence of normal enemy balance or a replacement for playtesting a
full Ninja run. The browser build is private and not a player-facing platform.
