# Single-Stage Progression Budget Audit

Scope: design/progression audit only. This document does not modify gameplay code, XP values, enemy counts, cards, room logic, or boss timing.

Authoritative current direction:

- BlueCube current full game/run is one stage only.
- The stage is Room 1 through Room 8, then one Boss.
- The run ends after the Boss.
- Level 25 must not trigger the Boss.
- Player level must not control world progression.
- World progression remains rooms -> waves -> room completion -> next room -> Boss.
- Player progression remains XP -> levels -> cards/perks.

## 1. Exact Level 1-25 XP Table

Current code formula:

- Player starts at Level 1.
- `xp_to_next` starts at 100.
- On each level-up, the next requirement becomes `int(current_requirement * 1.28)`.
- Every level-up currently creates one pending perk/card pick.

| Level Reached | XP From Previous Level | Cumulative XP Required |
| ---: | ---: | ---: |
| 1 | 0 | 0 |
| 2 | 100 | 100 |
| 3 | 128 | 228 |
| 4 | 163 | 391 |
| 5 | 208 | 599 |
| 6 | 266 | 865 |
| 7 | 340 | 1,205 |
| 8 | 435 | 1,640 |
| 9 | 556 | 2,196 |
| 10 | 711 | 2,907 |
| 11 | 910 | 3,817 |
| 12 | 1,164 | 4,981 |
| 13 | 1,489 | 6,470 |
| 14 | 1,905 | 8,375 |
| 15 | 2,438 | 10,813 |
| 16 | 3,120 | 13,933 |
| 17 | 3,993 | 17,926 |
| 18 | 5,111 | 23,037 |
| 19 | 6,542 | 29,579 |
| 20 | 8,373 | 37,952 |
| 21 | 10,717 | 48,669 |
| 22 | 13,717 | 62,386 |
| 23 | 17,557 | 79,943 |
| 24 | 22,472 | 102,415 |
| 25 | 28,764 | 131,179 |

Exact cumulative XP required to reach Level 20: **37,952 XP**.

Exact cumulative XP required to reach Level 25: **131,179 XP**.

## 2. Current Room-By-Room XP Supply

### Assumptions

- This table audits the intended single-stage route: Room 1 -> Room 2 -> Room 3 -> Room 4 -> Room 5 -> Room 6 -> Room 7 -> Room 8 -> Boss.
- Normal enemy XP is 44.
- Elite enemy XP is 220.
- Boss XP is 600.
- Treasure room estimate assumes both loot enemies are fully killed after being hit, for about 60 XP each.
- Combat rooms that use threat budgets are seed-dependent because enemy composition is random.
- Room 2 is deterministic because it uses fixed enemy counts: 10, 20, 30, 40, 50.
- Elite rooms are deterministic because they spawn 1, then 2, then 4 elite enemies.

| Segment | Type | Value Type | Enemies Avg/Min/Max | Elite Avg/Min/Max | XP Avg/Min/Max | Cumulative Avg XP | Expected Level After |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Room 1 | Combat | Seed-dependent estimate | 63.6 / 44 / 94 | 0 / 0 / 0 | 2,799 / 1,936 / 4,136 | 2,799 | Level 9 |
| Room 2 | Combat | Deterministic | 150 / 150 / 150 | 0 / 0 / 0 | 6,600 / 6,600 / 6,600 | 9,399 | Level 14 |
| Room 3 | Treasure | Deterministic assumption | 2 / 2 / 2 | 0 / 0 / 0 | 120 / 120 / 120 | 9,519 | Level 14 |
| Room 4 | Elite | Deterministic | 7 / 7 / 7 | 7 / 7 / 7 | 1,540 / 1,540 / 1,540 | 11,059 | Level 15 |
| Room 5 | Combat | Seed-dependent estimate | 59.5 / 42 / 83 | 0 / 0 / 0 | 2,617 / 1,848 / 3,652 | 13,676 | Level 15 |
| Room 6 | Combat | Seed-dependent estimate | 54.5 / 38 / 71 | 0 / 0 / 0 | 2,399 / 1,672 / 3,124 | 16,075 | Level 16 |
| Room 7 | Combat | Seed-dependent estimate | 129.1 / 106 / 163 | 0 / 0 / 0 | 5,678 / 4,664 / 7,172 | 21,753 | Level 17 |
| Room 8 | Elite | Deterministic | 7 / 7 / 7 | 7 / 7 / 7 | 1,540 / 1,540 / 1,540 | 23,293 | Level 18 |
| Boss | Boss | Deterministic | 1 / 1 / 1 | 0 / 0 / 0 | 600 / 600 / 600 | 23,893 | Level 18 |

Current intended single-stage content supplies about **23,893 XP** on a normal full clear.

That reaches about **Level 18**, not Level 25.

Current XP shortfall to Level 25:

- Required Level 25 XP: 131,179.
- Current expected full-clear XP: about 23,893.
- Shortfall: about 107,286 XP.
- Current content supplies about 18.2% of the XP needed for Level 25.

## 3. Front-Loading Verification

The previous audit finding is verified by current code:

- Room 1 alone reaches approximately Level 9, creating about 8 card picks.
- Room 2 brings the player to approximately Level 14, creating about 13 cumulative card picks.

Root causes:

- The early XP curve is very cheap: only 2,196 cumulative XP is required to reach Level 9.
- Room 1 currently supplies about 2,799 average XP.
- Room 2 deterministically spawns 150 normal enemies, worth 6,600 XP.
- Room 1 and Room 2 together supply about 9,399 XP, enough to reach Level 14.

This means early rooms over-deliver card picks relative to the intended "Build discovery" phase, even though the full stage under-delivers XP relative to the Level 25 target.

## 4. Build Completion Pick Budget

Current perk progression rules:

- A card can be picked up to 4 times.
- Picks 1-3 are normal progression.
- The 4th pick is presented as Legendary.
- Every current level-up grants one card pick.
- Reaching Level 20 from Level 1 grants 19 card picks.
- Reaching Level 25 from Level 1 grants 24 card picks.

### Current actual perk definitions

Current actual perk keys:

- `rapid_fire`
- `power_rounds`
- `hollow_point`
- `glass_cannon`
- `split_shot`
- `needle_rounds`
- `kinetic_rounds`
- `critical_spark`
- `overclock`
- `explosive_rounds`
- `impact_drive`
- `vital_core`
- `battle_recovery`
- `scout_boots`
- `phantom_step`

### Official Build support from current implementation

| Build | Current Actual Supporting Cards | Count | Picks To Complete All Listed 4-Stage Paths | Evaluation |
| --- | --- | ---: | ---: | --- |
| Gunslinger | `rapid_fire`, `power_rounds`, `hollow_point`, `glass_cannon`, `split_shot`, `needle_rounds`, `kinetic_rounds`, `critical_spark`, `overclock`, `explosive_rounds`, `impact_drive` | 11 | 44 | Strongest current support, but too many projectile cards exist for one run to complete all. |
| Ninja | `scout_boots`, `phantom_step`; hybrid candidates: `glass_cannon`, `kinetic_rounds`, `overclock` | 2 primary, 5 including hybrids | 8 primary, 20 including hybrids | Partially evaluable. Mobility exists, but close-range/dash reward identity is incomplete. |
| Engineer | No primary cards currently implemented. Weak temporary candidates: `explosive_rounds`, `impact_drive` | 0 primary | 0 primary | Cannot be meaningfully evaluated yet because automation tools do not exist. |
| Vampire | `vital_core`, `battle_recovery` | 2 | 8 | Partially evaluable as sustain/health, but not yet as death-fed Vampire identity. |

### Can Level 20 represent Build completion?

Yes, for the current single-stage version, Level 20 can represent substantial Build completion if "complete Build" means a focused build package, not every relevant card.

At Level 20, the player has 19 card picks. That can support:

- 3 fully completed 4-stage cards = 12 picks.
- 4 fully completed 4-stage cards = 16 picks.
- 4 completed cards plus 3 exploratory/hybrid picks = 19 picks.

This is enough for a primary Build to feel substantially complete around Level 20.

It is not enough to complete every current Gunslinger-supporting card, which would require 44 picks. That is acceptable; a Build should not mean "take every card with the same tag."

Builds that cannot currently be fully evaluated:

- Engineer, because it has no actual automation card path.
- Vampire, because current sustain cards do not yet create battlefield-fed scaling.
- Ninja, because movement cards exist but close-range/dash-reward payoff is incomplete.

## 5. Should Every Level From 2-25 Grant A Card?

### Option A: Every level grants a card pick

Consequences:

- Level 25 gives 24 total card picks.
- The player can complete six 4-stage cards if rolls and choices allow it.
- This strongly supports a single-stage game because every level feels rewarding.
- It makes the XP curve the main card-pacing lever.
- It may create too many completed 4-stage cards if the card pool remains small or if offered cards are too easy to force.

Current impact:

- 24 picks is acceptable for the current single-stage target if Level 20 is treated as primary Build completion and Levels 20-25 are power-expression time.
- The bigger problem is not "too many total picks." The bigger problem is that current XP supply grants too many picks in Rooms 1-2 and too few total XP points to reach Level 25.

### Option B: Some levels do not grant cards

Consequences:

- This creates room for non-card level rewards, but those rewards do not currently exist.
- It would make some level-ups feel empty unless another reward is added.
- It reduces the pressure on 4-stage card completion but risks weakening the core progression loop.

Current impact:

- Not recommended for the current version unless a real non-card level reward is designed later.

### Option C: Separate card pacing rule

Consequences:

- This gives designers direct control over card frequency independent of XP level.
- It creates another progression layer and risks making XP less intuitive.
- It could solve front-loading, but it is a larger architecture decision.

Current impact:

- Not recommended yet. Avoid inventing a separate reward system just to compensate for XP curve and room XP imbalance.

Recommendation:

Keep **one card pick per level-up** for the current single-stage version.

The immediate problem should be solved by progression budget ownership and XP distribution, not by making some level-ups empty.

## 6. Proposed Single-Stage Progression Curve

Target shape:

- Early rooms: Build discovery.
- Middle rooms: Build identity becomes clear.
- Late rooms: Build completion.
- Final rooms and Boss: power expression and Build test.

Recommended target level curve:

| Segment | Target Expected Level After Completion | Cumulative XP Target | Purpose |
| --- | ---: | ---: | --- |
| Room 1 | Level 5 | 599 | First few choices; no completed 4-stage card yet. |
| Room 2 | Level 8 | 1,640 | Build direction starts to appear. |
| Room 3 | Level 10 | 2,907 | Early support picks; treasure/economy does not dominate XP. |
| Room 4 | Level 13 | 6,470 | First card can be completed or nearly completed. |
| Room 5 | Level 16 | 13,933 | Build identity is clear. |
| Room 6 | Level 20 | 37,952 | Primary Build is substantially complete. |
| Room 7 | Level 22 | 62,386 | Power expression begins. |
| Room 8 | Level 24 | 102,415 | Final build refinement. |
| Boss | Level 25 | 131,179 | Final Build test. |

Recommended variance:

- Normal full clear should land around Level 24-25.
- Strong bonus-XP performance can land around Level 26 if later supported by legitimate bonus content.
- Missed treasure, skipped kills, or weaker performance can land around Level 22-23.
- Boss timing must remain room/stage based regardless of level.

This target is intentionally not linear. The current XP curve is exponential, so late-stage content must carry much larger XP budgets if Level 25 remains the expected endpoint.

## 7. Recommended XP Ownership Model

### A. Enemy XP only

Strengths:

- Immediate feedback on kills.
- Simple to understand.
- Supports the action combat loop.

Weaknesses:

- Progression becomes heavily dependent on enemy count.
- Room 2 demonstrates the risk: 150 enemies create a massive early XP spike.
- Treasure, elite, survival, and future room types become hard to balance against each other.
- Enemy count changes become progression changes, even when the intent was difficulty or pacing.

### B. Room completion XP only

Strengths:

- Very predictable.
- Easy to place target levels after each room.
- Reduces farming and enemy-count dependency.

Weaknesses:

- Kills feel less rewarding.
- Combat feedback becomes flatter.
- Enemy deaths lose part of their reward identity.
- Elite enemies and high-pressure rooms need separate handling to feel valuable.

### C. Hybrid: enemy XP + room completion XP

Strengths:

- Keeps kill feedback.
- Gives room/stage designers a stable progression budget.
- Reduces enemy-count dependency.
- Supports future room variety.
- Lets Elite and Treasure rooms have clear completion rewards without requiring huge enemy counts.
- Makes it possible to target Level 25 without spawning extreme enemy volumes.

Weaknesses:

- Requires explicit budget ownership.
- Requires clear UI feedback so players understand both kill XP and room-clear XP.
- Room completion XP must avoid feeling like a hidden scripted level grant.

Recommendation:

Use **Hybrid: enemy XP + room completion XP**.

Enemy XP should remain a meaningful moment-to-moment reward, but room completion XP should own the majority of progression accuracy. This is the safest way to make one 8-room stage reliably end around Level 25 without letting enemy count spikes control the entire card economy.

## 8. Boss Timing Independence

Required architecture:

- Boss unlocks after Room 8 is completed.
- Boss spawning checks stage/room progression only.
- Boss spawning does not check player level.
- Player XP and level do not advance world progression.
- The player can reach Boss underleveled if they missed XP, skipped optional rewards, or performed poorly.
- The player can reach Boss slightly overleveled if legitimate bonus XP exists later.
- The expected normal full-clear budget should still target approximately Level 25 by the end of the Boss.

Current note:

- The current codebase has a mismatch between `ROOMS_TO_BOSS = 8` and existing hub boss gate logic that can route the first boss at room 6 and the second boss at room 9.
- For the approved single-stage model, that later implementation pass should align boss routing to exactly Room 1 through Room 8, then Boss, then run end.

## 9. Required Code Changes Later

No implementation is performed in this audit.

Later code changes likely required:

1. Align hub/boss routing to the approved one-stage structure:
   - Room 1 through Room 8.
   - Boss after Room 8.
   - Win after Boss.

2. Decide and implement XP budget ownership:
   - Keep enemy XP.
   - Add room completion XP.
   - Assign explicit target XP budgets per room.

3. Rebalance room XP output:
   - Reduce early front-loading from Room 1 and Room 2.
   - Prevent fixed enemy-count rooms from dominating card pacing.
   - Increase late-room and boss contribution enough to approach Level 25.

4. Update UI feedback if room completion XP is added:
   - Communicate room-clear XP clearly.
   - Preserve visible kill XP feedback.

5. Update headless checks:
   - Verify XP curve math.
   - Verify boss timing is room-based.
   - Verify full intended room route is 1-8 plus Boss.
   - Verify level-up still grants card picks consistently.

6. Revisit card redesign only after progression budget targets are accepted.

## 10. Risks And Assumptions

Risks:

- Level 25 requires 131,179 cumulative XP, which is far above current content supply.
- If enemy XP alone is used, reaching Level 25 may require extreme enemy counts.
- If room completion XP is too large or poorly messaged, it may feel scripted.
- One card pick per level means Level 25 creates 24 picks, enough to complete up to six 4-stage cards.
- Gunslinger currently has enough cards to support many builds, while Engineer cannot be evaluated as a real Build yet.
- The current front-loaded XP curve can make early card choices feel compressed before the player understands the run.

Assumptions:

- Level 25 is an expected normal full-clear endpoint, not a guaranteed endpoint.
- Room 3 treasure XP assumes both loot enemies are killed.
- Random combat room estimates are based on current threat-budget wave generation and will vary by seed.
- Current build classification uses `BLUECUBE_DESIGN_BIBLE.md`, `BUILD_MAPPING_V1.md`, and actual current perk definitions; where the mapping document is stale, actual current perk keys take priority.
- No missing cards or mechanics are invented in this audit.

