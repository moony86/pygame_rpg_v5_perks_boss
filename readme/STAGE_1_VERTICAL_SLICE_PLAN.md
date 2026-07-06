# Stage 1 Vertical Slice Plan

Scope: planning only. No code, balance, card, enemy, music, or room logic changes are made by this document.

Goal: make the current single-stage run feel like a coherent 8 rooms + boss experience using existing systems as much as possible.

Approved run structure:

- One full run = one stage.
- Stage = Room 1 through Room 8, then Boss.
- Boss timing is room-based, not level-based.
- Player should reach about Level 20 around Room 6.
- Player should reach about Level 24-25 around Room 8 / Boss.
- One card pick per level remains unchanged.

## 1. Room 1-8 Identity And Purpose

| Room | Current Best Fit | Purpose | Player Experience Goal |
| ---: | --- | --- | --- |
| 1 | Combat | Onboarding fight | Learn movement, shooting, pickups, first card rhythm. Low danger, clear feedback. |
| 2 | Combat | First pressure check | More enemies, but still readable. Player starts forming a build direction. |
| 3 | Treasure | Reward / breather | Short nonstandard room that breaks combat pacing and reinforces loot chase. |
| 4 | Elite | First skill check | Introduce elite pressure as a midpoint exam. Player should have a partial build. |
| 5 | Combat | Build identity room | Standard combat with enough pressure for the chosen build to become visible. |
| 6 | Combat | Build completion checkpoint | Target Level 20. Primary build should feel mostly online by room end. |
| 7 | Combat | Power expression | Larger combat pressure. Player should enjoy the completed build under load. |
| 8 | Elite | Final pre-boss test | Last refinement, high tension, validates build before boss. |
| Boss | Boss | Final build test | Boss tests movement, damage uptime, sustain, and room-learned reactions. |

## 2. Enemy Pressure Curve

Use existing enemies and wave systems. Do not add enemy types yet.

Recommended pressure shape:

| Segment | Pressure Role | Existing Tools To Use |
| --- | --- | --- |
| Rooms 1-2 | Basic chase and ranged awareness | Chasers, early ranged, simple wave pacing. |
| Room 3 | Low combat / chase reward | Loot enemies only. |
| Room 4 | First elite spike | Existing elite room. |
| Rooms 5-6 | Mixed pressure | Chasers, ranged variants, jumpers, controlled density. |
| Room 7 | Peak normal-room pressure | Higher density and mixed enemy roles, but no new mechanics. |
| Room 8 | Final elite pressure | Existing elite room as pre-boss gate. |
| Boss | Pattern test | Existing boss. |

Design intent:

- Rooms 1-2 should not complete most of the build.
- Rooms 5-6 should be where the build becomes reliable.
- Rooms 7-8 should be where the player expresses the build, not still searches for it.
- Enemy count should not be raised just to feed XP.

## 3. XP Target Per Room

Use the current XP curve and room completion XP budget as the anchor.

| Room | Target Level After Room | Expected Cumulative XP | Current Budget Role |
| ---: | ---: | ---: | --- |
| 1 | 4 | 420 | Discovery begins. |
| 2 | 7 | 1,200 | Early direction forms. |
| 3 | 10 | 2,340 | First support picks. |
| 4 | 13 | 3,868 | First focused card path can be near completion. |
| 5 | 16 | 5,896 | Build identity becomes clear. |
| 6 | 20 | 9,675 | Primary build mostly complete. |
| 7 | 22 | 12,176 | Power expression begins. |
| 8 | 24 | 15,202 | Final pre-boss refinement. |
| Boss | 24-25 | Boss XP / remaining pickups | Final build test, not required to unlock boss. |

XP ownership:

- Enemy XP remains meaningful moment-to-moment feedback.
- Room completion XP owns pacing accuracy.
- Boss timing must stay independent from player level.

## 4. Music Assignment Per Room Segment

Use the current MusicSystem MVP.

| Segment | Music Key | Purpose |
| --- | --- | --- |
| Hub before Room 1 | `hub` | Reset, shop, dialogue, preparation. |
| Rooms 1-3 | `room` | Early exploration and build discovery. |
| Rooms 4-6 | `room` | Same track for MVP; pressure comes from waves, not music layering yet. |
| Rooms 7-8 | `room` | Keep MVP simple. Future pass may add intensity, but not now. |
| Boss | `boss` | Clear transition into final test. |
| Win / death | stop music | End-state clarity. |

Do not implement layered music yet. Do not claim crossfade beyond the current fade-out/fade-in behavior.

## 5. Boss Entrance Timing

Boss entrance should remain:

Room 1 -> Room 2 -> Room 3 -> Room 4 -> Room 5 -> Room 6 -> Room 7 -> Room 8 -> Boss -> End

Rules:

- Boss appears after Room 8 is cleared.
- Boss does not check player level.
- Underleveled players can still reach boss.
- Slightly overleveled players do not trigger boss early.
- Boss is the final build test, not the build completion gate.

## 6. What Must Be Implemented First

Priority order:

1. Verify route consistency.

Ensure the live route is exactly Rooms 1-8, then Boss, then run end.

2. Verify room XP pacing in live play.

Confirm Room 6 lands near Level 20 and Room 8 lands near Level 24 in real gameplay, not only simulation.

3. Verify Room 1 and Room 2 pacing.

Make sure early rooms no longer grant most of the build.

4. Verify enemy pressure without adding new enemies.

Use existing wave composition and current enemy behavior. Only tune if playtest shows an obvious pacing mismatch.

5. Verify music assets and state transitions.

Ensure `hub_theme.ogg`, `room_theme.ogg`, and `boss_01.ogg` exist or accept silent fallback for missing tracks.

6. Verify dev tools support.

F12 should expose enough visibility for room number, XP, level, pending cards, FPS/profiler, and current music/debug state where practical.

## 7. What Must NOT Be Added Yet

Do not add:

- New stages.
- New enemy types.
- New card or perk redesigns.
- New build identities.
- Layered music.
- New boss phases.
- New room types.
- New economy systems.
- New reward systems beyond current XP/pickup flow.
- Procedural world renderer rewrites.
- Major wave architecture changes.

The vertical slice should prove that the existing systems can produce a complete, readable, satisfying first run before expanding scope.

