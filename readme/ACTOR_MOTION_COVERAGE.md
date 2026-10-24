# Actor motion coverage

This pass completes a first procedural motion layer over existing editable PNGs.
It is NOT a set of newly authored walk/attack/death sprite sheets and does not add
class-specific hero art, NPC redesigns, split boss limbs, or a new player death scene.

| Actor | Presentation |
|---|---|
| Hero (shared by builds) | Idle breathing, movement sway, existing dash squash, brief hurt compression; aim-facing and muzzle geometry retained |
| Chaser | Existing move/pressure/burst/hit poses |
| Fast/tank chasers | Distance-driven fast/heavy stride and hit reaction |
| Four ranged variants | Existing charge/release/recovery and hit poses |
| Three jumper variants | Existing preparation/air/landing poses |
| Brute | Existing displacement-driven gait, preparation, charge and stop |
| Hunter | Fast stride, preparation, release and hit; pink broken direction cue |
| Elite | Hover, windup/release/lunge/hit; gold directional cues |
| Boss phases 1–3 | Phase-dependent hover, windup/release/lunge/hit; red directional cues; existing circular warnings retained |
| Loot creature | Skipping gait and hit reaction |
| Every enemy | Short independently expiring death echo using the current family/phase asset |
| Drone/bomber | Subtle tilt; existing orbit, blade spin, trails and firing flash retained |
| Blood bat | Existing wing squash and carried-blood highlight retained |
| Hub NPCs | Existing ambient drawing and tea sprite sheet retained; time now advances once in update, never in draw |

Gameplay movement, damage, hitboxes, rewards and attack schedules unchanged.
The hero's gun does not inherit body sway; projectile geometry remains registered.
Draw calls never advance timers. NPC timers stop outside active world states.

Validation: all 15 enemy types and all 3 boss phases render without gameplay
mutation; death echoes expire; hero reset clears hurt pose; NPC draw doesn't advance
time; original pistol, chaser, ranged, jumper, brute and companion regressions pass.
Private browser tests exercised mixed real-AI actors and boss phase 1. Other phases
were render-tested, not defeated in a full run. These fixtures don't establish balance.
