# Run / Build Progression Design Audit

Scope: progression structure only. This audit does not redesign individual perks, rebalance cards, or change gameplay code.

## 1. Current Progression Estimate

### Current XP and pick rules

- Normal enemy kill: 44 XP.
- Elite kill: 220 XP.
- Boss kill: 600 XP.
- Treasure room loot enemy, if fully killed after a hit: about 60 XP each.
- Player starts at level 1 with 100 XP required for the first level-up.
- Each level-up creates one pending perk/card pick.
- XP requirement grows by `int(current_requirement * 1.28)` after each level.
- Each perk can currently be picked up to 4 times.

### Current room structure in code

The visible run frame suggests 8 rooms plus boss through `ROOMS_TO_BOSS = 8`, but the actual hub gate logic is different:

- First boss gate: room 6.
- Second boss gate: room 9.
- After defeating the first boss, `room_number` advances to 7.
- After defeating the second boss, the run ends in win state.

That means the currently reachable full run is approximately:

Room 1 -> Room 2 -> Room 3 -> Room 4 -> Room 5 -> Boss 1 -> Room 7 -> Room 8 -> Boss 2

Rooms 6 and 9 are not normal playable rooms in the current gate flow.

### Expected XP and card picks

Estimates below use the current wave builder over seeded wave compositions and assume full room clears. Enemy counts vary because threat-budget rooms roll enemy compositions.

| Segment | Type | Expected XP | Expected Rewarded Enemies | Expected Cumulative Picks |
| --- | --- | ---: | ---: | ---: |
| Room 1 | Combat | ~2,821 | ~64 | 8 |
| Room 2 | Combat | 6,600 | 150 | 13 |
| Room 3 | Treasure | ~120 | 2 | 13 |
| Room 4 | Elite | 1,540 | 7 | 14 |
| Room 5 | Combat | ~2,623 | ~60 | 14 |
| Boss 1 | Boss | 600 | 1 | 15 |
| Room 7 | Combat | ~5,680 | ~129 | 16 |
| Room 8 | Elite | 1,540 | 7 | 16 |
| Boss 2 | Boss | 600 | 1 | 16 |

Approximate current result:

- Picks before first boss: about 14 to 15.
- Picks across the full currently reachable run: about 16.
- Final level after full run: about level 17.
- Total XP across current reachable run: about 22,124 XP.

If the game were instead treated as a literal room 1 through room 8 plus one boss sequence, the estimate would be about 17 picks by the final boss. The actual code path is close in total picks, but the distribution is front-loaded differently because the first boss occurs at room 6.

## 2. Problems With Current XP/Card Pacing

### Pacing is extremely front-loaded

Room 1 alone can grant roughly 8 perk picks. Room 2 can bring the player to roughly 13 total picks. This means the player can complete several 4-stage cards before the run has established a stable build arc.

### The first boss arrives after build maturity, not during build formation

By the first boss gate, the player may already have enough picks to complete three full 4-stage cards, with extra picks left over. This makes the first boss less of an early build checkpoint and more of a fight against an already-developed build.

### Four-stage cards are realistic, but too easy to complete early

The current structure supports 4-stage cards numerically. The issue is not scarcity. The issue is that 4-stage cards can finish so early that their progression stages may not feel like a run-long commitment.

### The run has too few decision beats for the number of picks

The current expected full-run pick count is around 16. That is enough to complete four full 4-stage cards if rolls cooperate. In a short run, that compresses identity selection, card completion, and late-game payoff into the first half of the run.

### Room count and boss-gate count disagree

`ROOMS_TO_BOSS = 8`, HUD framing, and some room planning imply an 8-room arc. Hub gate logic currently sends the first boss at room 6 and the second boss at room 9. Before card redesign continues, the intended run frame needs to be made explicit.

### XP is tied heavily to enemy count spikes

Room 2 has a fixed 150 enemies and therefore 6,600 XP. This single room provides a very large share of the early build. Progression currently depends more on enemy volume than on room/stage milestones.

## 3. Recommended Run Structure

Recommendation: B) one stage = 8 rooms + boss, full run = multiple stages.

Reasoning:

- A single 8-room plus boss run is too short for 4-stage cards, hybrid builds, shop purchases, and boss escalation to all breathe.
- Endless room progression would make card identity harder to judge because there is no fixed completion target.
- A staged run gives the game a clear build arc without requiring a new card progression framework.

Recommended high-level structure:

- Stage 1: build identity selection and first card completions.
- Stage 2: build consolidation, hybrid support, and secondary card completion.
- Stage 3: final build expression, legendary picks, and final boss pressure.

Perks and shop upgrades should persist across stages for the duration of a run. Resetting upgrades between stages would undermine build completion and make shop choices feel temporary. Stage transitions should reset room-local state, enemies, projectiles, pickups, and temporary scene state, not the player's build.

## 4. Recommended Number of Rooms/Stages

Recommended full run:

- 3 stages.
- Each stage has 8 rooms plus a boss.
- Total structure: 24 rooms plus 3 bosses.

Recommended stage composition:

- 5 combat rooms.
- 1 treasure or economy room.
- 1 elite room.
- 1 special pressure room, such as survival or curse.
- 1 stage boss.

This creates enough space for card identity, shop economy, and boss scaling to be evaluated without turning the game into an endless format.

## 5. Recommended Card Picks Per Stage

Target card-pick pacing:

| Stage | Recommended Picks During Stage | Cumulative Picks Target | Build Role |
| --- | ---: | ---: | --- |
| Stage 1 | 5 to 6 | 5 to 6 | Choose primary identity and complete or nearly complete one core card. |
| Stage 2 | 5 to 6 | 10 to 12 | Complete primary build package and add hybrid support. |
| Stage 3 | 4 to 6 | 14 to 18 | Finish late synergies, legendary picks, and final build expression. |

Recommended boss timing:

- Boss 1 should happen when the player has about 5 to 6 picks.
- Boss 2 should happen when the player has about 10 to 12 picks.
- Final boss should happen when the player has about 14 to 18 picks.

The current game reaches about 13 picks by the end of room 2, so the XP curve is much faster than this target.

## 6. Recommended Full Build Completion Target

Define a "full Build" as:

- One primary 4-stage card completed.
- One or two supporting 4-stage cards completed or nearly completed.
- One hybrid or utility card partially developed.
- Shop upgrades supporting the chosen direction.

Recommended full-run target:

- Minimum viable build: 8 to 10 picks.
- Complete focused build: 12 to 14 picks.
- Complete build with hybrid expression: 16 to 18 picks.

This means a 4-stage card should be realistic, but not automatic in the first two rooms. One completed 4-stage card should feel like a Stage 1 achievement; multiple completed 4-stage cards should belong to Stage 2 or later.

## 7. What Must Change Before Continuing Card Redesign

Before more single-card redesign work continues, progression ownership should be decided and documented:

1. Decide the real run frame.

Recommended decision: one stage is 8 rooms plus boss, and one full run is 3 stages.

2. Align boss gate logic with the chosen frame.

Current mismatch: `ROOMS_TO_BOSS = 8`, but the first boss gate is room 6 and the second boss gate is room 9.

3. Set target card-pick pacing per stage.

Recommended target: about 5 to 6 picks per stage, about 16 to 18 picks across a full run.

4. Rework XP pacing around stage milestones.

The current room 1 and room 2 XP output is too high for a staged build arc. XP should stop granting most of the run's card picks before the first boss.

5. Decide whether card picks are earned only through XP or also through room/boss rewards.

The current pure XP model makes enemy count the dominant build-pacing lever. A milestone-assisted model would make stage design easier to tune.

6. Keep perks and shop upgrades persistent across the full run.

Build identity depends on continuity. Reset only scene-local and temporary state between stages.

7. Revisit card redesign only after progression targets are fixed.

Card identity cannot be judged reliably while the game grants enough early picks to complete several cards almost immediately.

