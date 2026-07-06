# XP Curve + XP Pickup Tier Implementation Plan

Scope: implementation plan only. No gameplay code, XP values, enemy counts, room logic, cards, or assets are changed by this document.

Approved direction:

- One full run = one stage.
- Stage = 8 rooms + boss.
- Boss timing does not depend on player level.
- Target endpoint is around Level 24-25 before or around the boss.
- Build should feel mostly complete around Level 20.
- Keep one card pick per level for now.
- Avoid increasing enemy count just to feed XP.

## 1. Current Problem

The current XP curve starts at 100 XP and multiplies each next level requirement by `1.28`.

That makes Level 25 require **131,179 cumulative XP**, which is too high for the approved single-stage run.

The current intended 8-room + boss content was previously estimated at about **23,893 XP**, which reaches only about Level 18 under the current curve.

The problem is two-sided:

- Current curve is too steep for a one-stage game.
- Current XP delivery is too front-loaded in Room 1 and Room 2.

XP pickup tiers solve pickup clutter and reward readability. They do not solve the total XP budget by themselves.

## 2. Formula Comparison Tables

### A1. Gentler Multiplier: 1.10

Formula:

`next_requirement = int(previous_requirement * 1.10)`

| Level | XP Required From Previous Level | Cumulative XP |
| ---: | ---: | ---: |
| 1 | 0 | 0 |
| 2 | 100 | 100 |
| 3 | 110 | 210 |
| 4 | 121 | 331 |
| 5 | 133 | 464 |
| 6 | 146 | 610 |
| 7 | 160 | 770 |
| 8 | 176 | 946 |
| 9 | 193 | 1,139 |
| 10 | 212 | 1,351 |
| 11 | 233 | 1,584 |
| 12 | 256 | 1,840 |
| 13 | 281 | 2,121 |
| 14 | 309 | 2,430 |
| 15 | 339 | 2,769 |
| 16 | 372 | 3,141 |
| 17 | 409 | 3,550 |
| 18 | 449 | 3,999 |
| 19 | 493 | 4,492 |
| 20 | 542 | 5,034 |
| 21 | 596 | 5,630 |
| 22 | 655 | 6,285 |
| 23 | 720 | 7,005 |
| 24 | 792 | 7,797 |
| 25 | 871 | 8,668 |

Result:

- Level 20: 5,034 XP.
- Level 25: 8,668 XP.

Assessment:

- Very easy to fit inside one stage.
- Too flat for current room XP values unless enemy/room XP is heavily reduced.
- Late levels may feel too cheap.

### A2. Gentler Multiplier: 1.15

Formula:

`next_requirement = int(previous_requirement * 1.15)`

| Level | XP Required From Previous Level | Cumulative XP |
| ---: | ---: | ---: |
| 1 | 0 | 0 |
| 2 | 100 | 100 |
| 3 | 114 | 214 |
| 4 | 131 | 345 |
| 5 | 150 | 495 |
| 6 | 172 | 667 |
| 7 | 197 | 864 |
| 8 | 226 | 1,090 |
| 9 | 259 | 1,349 |
| 10 | 297 | 1,646 |
| 11 | 341 | 1,987 |
| 12 | 392 | 2,379 |
| 13 | 450 | 2,829 |
| 14 | 517 | 3,346 |
| 15 | 594 | 3,940 |
| 16 | 683 | 4,623 |
| 17 | 785 | 5,408 |
| 18 | 902 | 6,310 |
| 19 | 1,037 | 7,347 |
| 20 | 1,192 | 8,539 |
| 21 | 1,370 | 9,909 |
| 22 | 1,575 | 11,484 |
| 23 | 1,811 | 13,295 |
| 24 | 2,082 | 15,377 |
| 25 | 2,394 | 17,771 |

Result:

- Level 20: 8,539 XP.
- Level 25: 17,771 XP.

Assessment:

- Fits one stage better than 1.28.
- Still has exponential late growth, but mild enough for 8 rooms + boss.
- Current full-stage XP would overshoot Level 25 unless room/enemy XP budget is reduced or redistributed.

### B. Linear Curve: 100 + 50 Per Level

Formula:

`requirement_for_next_level = 100 + (current_level - 1) * 50`

| Level | XP Required From Previous Level | Cumulative XP |
| ---: | ---: | ---: |
| 1 | 0 | 0 |
| 2 | 100 | 100 |
| 3 | 150 | 250 |
| 4 | 200 | 450 |
| 5 | 250 | 700 |
| 6 | 300 | 1,000 |
| 7 | 350 | 1,350 |
| 8 | 400 | 1,750 |
| 9 | 450 | 2,200 |
| 10 | 500 | 2,700 |
| 11 | 550 | 3,250 |
| 12 | 600 | 3,850 |
| 13 | 650 | 4,500 |
| 14 | 700 | 5,200 |
| 15 | 750 | 5,950 |
| 16 | 800 | 6,750 |
| 17 | 850 | 7,600 |
| 18 | 900 | 8,500 |
| 19 | 950 | 9,450 |
| 20 | 1,000 | 10,450 |
| 21 | 1,050 | 11,500 |
| 22 | 1,100 | 12,600 |
| 23 | 1,150 | 13,750 |
| 24 | 1,200 | 14,950 |
| 25 | 1,250 | 16,200 |

Result:

- Level 20: 10,450 XP.
- Level 25: 16,200 XP.

Assessment:

- Very predictable.
- Easy to budget room rewards.
- May feel too uniform; late levels do not create much end-run pressure.

### C. Hybrid Curve: Linear Early, Mild Multiplier Late

Recommended candidate formula:

- Levels 1-10 use linear growth.
- After Level 10, use a mild multiplier.

Exact formula:

- `xp_to_next = 100 + (current_level - 1) * 40` while current level is below 10.
- After that, `xp_to_next = int(previous_requirement * 1.10)`.

| Level | XP Required From Previous Level | Cumulative XP |
| ---: | ---: | ---: |
| 1 | 0 | 0 |
| 2 | 100 | 100 |
| 3 | 140 | 240 |
| 4 | 180 | 420 |
| 5 | 220 | 640 |
| 6 | 260 | 900 |
| 7 | 300 | 1,200 |
| 8 | 340 | 1,540 |
| 9 | 380 | 1,920 |
| 10 | 420 | 2,340 |
| 11 | 462 | 2,802 |
| 12 | 508 | 3,310 |
| 13 | 558 | 3,868 |
| 14 | 613 | 4,481 |
| 15 | 674 | 5,155 |
| 16 | 741 | 5,896 |
| 17 | 815 | 6,711 |
| 18 | 896 | 7,607 |
| 19 | 985 | 8,592 |
| 20 | 1,083 | 9,675 |
| 21 | 1,191 | 10,866 |
| 22 | 1,310 | 12,176 |
| 23 | 1,441 | 13,617 |
| 24 | 1,585 | 15,202 |
| 25 | 1,743 | 16,945 |

Result:

- Level 20: 9,675 XP.
- Level 25: 16,945 XP.

Assessment:

- Fits an 8-room + boss run.
- Early game is understandable and controllable.
- Late game still climbs enough that Level 20-25 has weight.
- Easier to tune than a pure exponential and less flat than a pure linear curve.

## 3. Recommended XP Curve

Recommend **Option C: hybrid linear early + mild multiplier late**.

Recommended formula:

```text
if current_level < 10:
    xp_to_next = 100 + (current_level - 1) * 40
else:
    xp_to_next = int(previous_xp_to_next * 1.10)
```

Recommended cumulative targets:

- Level 20: 9,675 XP.
- Level 24: 15,202 XP.
- Level 25: 16,945 XP.

Why this fits:

- Level 20 can become the "Build mostly complete" point.
- Levels 20-25 still require meaningful additional XP.
- The full stage budget can target roughly 16,000-18,000 XP instead of 131,179 XP.
- It avoids requiring huge enemy counts.
- It preserves one card pick per level.

Important balancing note:

Under this curve, the current estimated 8-room + boss XP supply of about 23,893 XP would overshoot Level 25. The implementation pass should reduce and redistribute XP budget rather than using current output unchanged.

## 4. Recommended XP Pickup Tiers

Current LootSystem behavior:

- XP pickups use pickup type `"xp"`.
- Collection/magnet behavior is shared by all XP pickups.
- Current `_split_xp_amount` caps XP drops to at most 4 pickups per enemy.
- Current split is even-value, not tiered.

Recommended tier metadata:

| Tier ID | Value | Placeholder Name | Placeholder Color | Intended Drop Source |
| --- | ---: | --- | --- | --- |
| `xp_tiny` | 5 | Tiny XP Shard | Pale cyan | Remainders and very small rewards. |
| `xp_small` | 25 | Small XP Crystal | Cyan | Standard weak/normal enemy portions. |
| `xp_medium` | 75 | Medium XP Crystal | Blue | Strong normal enemies, room reward fragments. |
| `xp_large` | 200 | Large XP Crystal | Purple | Elites, miniboss-like enemies, large room rewards. |
| `xp_huge` | 500 | Huge XP Crystal | Gold | Boss, major room completion payout, special rewards. |

These values are intentionally compatible with the recommended full-run budget:

- Normal enemy XP can stay visually small.
- Elite and boss rewards can become fewer, higher-value crystals.
- Room completion XP can be represented without flooding the screen.

## 5. XP Tier Split Rule

Recommended splitter goal:

- Preserve exact XP value where practical.
- Keep pickup count low.
- Use higher tiers for higher-value rewards.
- Keep current magnet and collection behavior unchanged.
- Do not require final art.

Recommended algorithm:

1. Define ordered tiers from high to low:
   - 500
   - 200
   - 75
   - 25
   - 5

2. For XP amounts 1-24:
   - Use one exact-value fallback pickup or one `xp_tiny`-styled pickup carrying the exact value.
   - This preserves exact XP without creating many 5-value shards.

3. For XP amounts 25 and above:
   - Greedily split using the largest tier that does not exceed the remaining amount.
   - Prefer at most 4 pickups for enemy drops.
   - Prefer at most 6-8 pickups for room completion drops.

4. For awkward remainders:
   - If remainder is below 5, merge it into the previous smallest pickup.
   - If exact preservation would exceed pickup cap, merge the remainder upward into an existing pickup and keep the exact total value.

Example splits:

| XP Amount | Suggested Drops | Pickup Count |
| ---: | --- | ---: |
| 44 | 25 + 19 exact small/tiny fallback | 2 |
| 75 | 75 | 1 |
| 120 | 75 + 25 + 20 exact fallback | 3 |
| 220 | 200 + 20 exact fallback | 2 |
| 600 | 500 + 75 + 25 | 3 |
| 1,200 | 500 + 500 + 200 | 3 |

Implementation detail:

- Pickup value should remain authoritative for XP gain.
- Tier ID and color are presentation metadata only.
- Exact XP preservation matters more than forcing every pickup value to equal a tier value.

## 6. Room-By-Room Target Budget

Using the recommended hybrid curve:

| Segment | Target Level After Completion | Cumulative XP Target | Segment XP Budget | Purpose |
| --- | ---: | ---: | ---: | --- |
| Room 1 | Level 4 | 420 | 420 | Build discovery begins. |
| Room 2 | Level 7 | 1,200 | 780 | First direction forms. |
| Room 3 | Level 10 | 2,340 | 1,140 | Early build support and economy. |
| Room 4 | Level 13 | 3,868 | 1,528 | First 4-stage card can be completed if focused. |
| Room 5 | Level 17 | 6,711 | 2,843 | Build identity becomes clear. |
| Room 6 | Level 20 | 9,675 | 2,964 | Primary Build mostly complete. |
| Room 7 | Level 23 | 13,617 | 3,942 | Power expression begins. |
| Room 8 | Level 24 | 15,202 | 1,585 | Final refinement before boss. |
| Boss | Level 25 | 16,945 | 1,743 | Final test and final meaningful pick. |

Recommended variance band:

- Normal full clear: Level 24-25.
- Strong clear or bonus XP: Level 25-26.
- Missed optional XP: Level 22-23.

Important:

- Boss should not be required to unlock the final meaningful perk pick.
- Room 8 should already put the player around Level 24.
- Boss can finish Level 25 or provide final expression XP, but it should not be the only path to the last important card choice.

## 7. Progression Budget Ownership

Recommended ownership remains hybrid:

- Enemy XP provides moment-to-moment feedback.
- Room completion XP owns most of the predictable progression budget.
- Boss XP contributes to the endpoint but does not control world progression.

Why:

- Enemy XP only would make enemy count the progression budget.
- Room XP only would flatten combat rewards.
- Hybrid lets designers tune the 8-room stage without spawning more enemies just to feed XP.

Suggested split for later implementation:

- Normal enemy XP: lower share of total budget.
- Elite enemy XP: higher-value tiered drops.
- Room completion XP: main budget correction tool.
- Boss XP: meaningful but not required for Build completion.

## 8. Files Likely Affected Later

Likely implementation files:

- `entities/player.py`
  - Replace current `xp_to_next = int(xp_to_next * 1.28)` progression with recommended hybrid curve.

- `systems/loot_system.py`
  - Add XP tier definitions.
  - Replace even XP splitting with tier-aware splitting.
  - Preserve magnet and collection behavior.

- `entities/pickup.py`
  - Add optional tier/color metadata for XP pickups.
  - Preserve pickup value as the source of truth.

- `systems/combat_system.py`
  - Ensure enemy XP amounts route through tiered XP spawning without changing kill/reward correctness.

- `systems/room_system.py` or room flow owner
  - Later add room completion XP budget if approved.

- `game.py` or `systems/scene_system.py`
  - Later award room completion XP at the correct room-clear point if approved.

- `settings.py`
  - Store XP curve constants and XP tier values if constants are centralized.

- `tools/headless_checks.py`
  - Add checks for XP curve, tier splitting, and pickup count limits.

## 9. Implementation Phases

### Phase 1: XP curve only

- Add a helper for calculating XP required for the next level.
- Replace hardcoded multiplier behavior.
- Validate exact Level 1-25 table.
- Do not change room XP yet.

### Phase 2: XP pickup tier metadata and splitting

- Add XP tier definitions.
- Add tier-aware split function.
- Preserve exact XP value.
- Preserve current pickup collection/magnet behavior.
- Validate pickup counts.

### Phase 3: Room completion XP budget

- Add explicit room completion XP payout.
- Use target room budget table as the first tuning anchor.
- Keep boss timing room-based.
- Avoid level-triggered progression.

### Phase 4: Full progression validation

- Run a deterministic budget simulation.
- Confirm Level 20 around Room 6.
- Confirm Level 24 around Room 8.
- Confirm Level 24-25 before/around boss.
- Confirm one card pick per level remains intact.

## 10. Validation Checks

Required later checks:

1. XP curve table check:
   - Level 20 cumulative XP equals 9,675.
   - Level 25 cumulative XP equals 16,945.

2. Level-up card check:
   - Every level-up still increments pending perk picks by 1.

3. Pickup split check:
   - Split pickup values sum exactly to requested XP.
   - High XP rewards use higher-value crystals.
   - Normal enemy rewards do not create excessive pickup counts.

4. Magnet/collection check:
   - All XP tiers collect using existing pickup behavior.
   - Player receives the exact pickup value.

5. Room budget check:
   - Expected Room 6 level is around 20.
   - Expected Room 8 level is around 24.
   - Expected boss endpoint is around 24-25.

6. Boss independence check:
   - Boss appears after room progression, not level progression.
   - Underleveled players can still reach boss.
   - Slightly overleveled players do not trigger boss early.

## 11. Recommendation Summary

Recommended XP curve:

- Hybrid early linear + late mild multiplier.
- Level 20 target: 9,675 cumulative XP.
- Level 25 target: 16,945 cumulative XP.

Recommended pickup tiers:

- 5, 25, 75, 200, 500.
- Use tier metadata for color/name placeholders.
- Preserve exact XP value through pickup values.

Recommended progression budget:

- Room 6 should land around Level 20.
- Room 8 should land around Level 24.
- Boss should land around Level 25.
- Boss timing remains completely independent from player level.

