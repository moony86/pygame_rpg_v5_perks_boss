# Collection feedback

Reuses existing coin, XP, potion, dash, stopwatch, blood and ring PNG assets;
no new generated art or third-party assets. Six independent `fx_collect_*`
bindings expose icon size, tint, opacity, frames/FPS and lifetime in Level Studio.

- Coins and XP gain a short actual-displacement streak only while magnetized.
- Real pickups create an icon, short ground pulse and colored value near the hero.
- Events of the same type within .18s merge into one displayed number.
- Only one pulse per type is visible (six types maximum). Subsequent batches
  replace the fading previous batch; no queue of old rewards accumulates.
- Active types use consecutive rows; a single special pickup stays close to the hero.
- Healing displays actual HP restored, or HP FULL, without changing potion consumption.
- Time stop keeps its existing activation and duration; dash still refills the same
  charges and applies its original buffs. Blood orbs display actual blood gained.
- No XP/gold/heal amounts, RNG, magnet behavior, drops, sounds or respawn rules changed.
- Reset clears collection feedback. Draw does not advance timers or mutate players.

The game remains a desktop product; this is not a mobile UI implementation.
Validation: `tools/check_collection_feedback.py`, demo/object/headless regressions,
native visual contact sheet, private browser pickup interaction test.
