# BlueCube Player Power / Progression Audit

Scope: inventory and audit only. No gameplay changes were made.

## Executive Summary

BlueCube currently has a strong but highly stackable run-power model. Most power is permanent for the run and comes from three overlapping layers:

- Level-up perk cards, capped at 4 picks per perk, where the 4th pick becomes a legendary version.
- Shop upgrades from Blacksmith and Healer, paid with gold and mostly permanent for the run.
- Active skills replacing Q/dash behavior: Dash, Blast, Surge, and Ghost.

The largest balance risk is multiplicative stacking between flat bullet damage, `weapon_damage_multiplier`, Surge's `2x` damage, crit overflow, multishot, pierce, explosive rounds, and fire-rate scaling. Defense also has large stacking potential, but offense scales faster and has more multiplicative hooks.

## Core Power Formulas

| System | Formula / Value | Source |
|---|---:|---|
| Base bullet damage | `25 + player.damage_bonus` | `settings.py`, `systems/shooting_system.py` |
| Weapon damage multiplier | Multiplies projectile base damage, shop `Double Barrel` sets at least `2.0` | `systems/shooting_system.py`, `systems/upgrade_system.py` |
| Surge damage | Temporary `2x` projectile damage | `settings.py`, `systems/shooting_system.py` |
| Fire cooldown | `max(0.055, 0.30 / fire_rate_multiplier)` | `systems/shooting_system.py` |
| Surge fire rate | Temporary `1.45x` fire-rate multiplier | `settings.py` |
| Split shot damage | If projectile count > 1, multiply by `max(0.50, 1 - (count - 1) * 0.10)`, then by `split_damage_multiplier` | `systems/shooting_system.py` |
| Crit chance | Clamped to 100%, overflow adds to crit multiplier | `systems/shooting_system.py` |
| Base crit multiplier | `1.75` | `entities/player.py` |
| Room clear regen | `player.heal(player.regen_on_room_clear)` when returning hub | `systems/scene_system.py` |
| Curse reward | `reward_multiplier = 2` | `systems/room_system.py`, `game.py` |
| Normal enemy reward | `44 XP`, `8 gold`, dropped as pickups | `settings.py`, `systems/combat_system.py` |
| Elite reward | `5x XP`, `6x gold` | `systems/combat_system.py`, `game.py` |
| Boss reward | Immediate `600 XP`, `180 gold` | `settings.py`, `systems/combat_system.py` |

## Part 1 - Full Inventory

### Player Base Stats and Abilities

| ID / Name | Source | Obtained By | Effect | Numeric Value | Limit | Duration | Stacking | Category | Notes |
|---|---|---|---|---:|---|---|---|---|---|
| Base move speed | `entities/player.py`, `settings.py` | Base | Movement speed | `400` | N/A | Run baseline | Additive modifiers | Mobility | Modified by speed perks and Ghost |
| Base max HP | `settings.py` | Base | Max health | `200` | N/A | Run baseline | Additive modifiers | Defense / HP | Can be reduced by tradeoff perks |
| Damage bonus | `entities/player.py` | Base stat | Adds to projectile damage | `0` base | No direct cap | Run-long | Additive | Damage | Large number of sources |
| Fire-rate multiplier | `entities/player.py` | Base stat | Multiplies firing speed | `1.0` base | Cooldown floor `0.055s` | Run-long | Additive attribute, multiplicative with Surge | Attack Speed | Stacking can hit cooldown floor |
| Projectile count | `entities/player.py` | Base stat | Bullets per shot | `1` base | Perk cap 8 | Run-long | Additive | Projectile Count | Split damage mitigation applies |
| Pierce | `entities/player.py` | Base stat | Extra enemies hit per projectile | `0` base | No global cap, shop/perk caps | Run-long | Additive | Projectile Behavior | Hollow Point can reset to 0 |
| Crit chance | `entities/player.py` | Base stat | Chance for crit | `0.0` base | No hard cap; overflow converts to multiplier | Run-long | Additive | Crit | Overflow is a high-risk scaling hook |
| Crit multiplier | `entities/player.py` | Base stat | Crit damage multiplier | `1.75` base | No cap | Run-long | Additive plus crit-overflow | Crit | Can become very high |
| Knockback power | `entities/player.py` | Base stat | Scales projectile knockback | `1.0` base | No global cap | Run-long | Additive | Utility | Multiplies base projectile knockback 18 |
| Dash | `entities/player.py`, `settings.py` | Base Q ability | Burst movement plus invulnerability | speed `900`, duration `0.24s`, cooldown `5.5s`, invuln `0.74s` total | One active skill slot | Temporary | Modified by cooldown/invuln bonuses | Dash / Mobility | `try_dash()` routes through active skill |
| Blast | `game.py`, `settings.py` | Healer shop skill | Pushes enemies in radius | radius `330`, force `330` | One active skill slot | Instant | Replaces Q behavior | Utility | No damage |
| Surge | `entities/player.py`, `settings.py` | Healer shop skill | Damage/fire-rate buff | duration `5s`, damage `2x`, fire rate `1.45x` | One active skill slot | Temporary | Multiplicative with existing offense | Damage / Attack Speed | Very high DPS window |
| Ghost | `entities/player.py`, `settings.py` | Healer shop skill | Speed plus invulnerability | duration `2s`, speed `1.95x`, invulnerable during duration | One active skill slot | Temporary | Multiplicative speed | Mobility / Defense | Strong safety tool |

### Weapons

| ID | Name | Source | Obtained By | Effect | Numeric Value | Limit | Duration | Stacking | Category | Notes |
|---|---|---|---|---|---:|---|---|---|---|---|
| `pistol` | Pistol | `definitions/weapon_definitions.py`, `systems/weapon_system.py` | Base weapon, key 1 | Projectile attack intent | cooldown `0.30`; damage comes from projectile formula | N/A | Run-long | Uses player projectile stats | Damage / Projectile | Main beneficiary of most upgrades |
| `knife` | Knife | same | Base weapon, key 2 | Melee arc attack intent | damage `35`, cooldown `0.38`, range `85`, arc `105`, knockback `26` | N/A | Run-long | Does not use projectile stat stack | Melee | Less connected to progression |
| `sword` | Sword | same | Base weapon, key 3 | Melee rectangle attack intent | damage `55`, cooldown `0.55`, range `110`, width `54`, length `120`, knockback `34` | N/A | Run-long | Does not use projectile stat stack | Melee | Stronger than knife but has fewer build hooks |

### Loot, XP, Gold, and Leveling

| ID / Name | Source | Obtained By | Effect | Numeric Value | Limit | Duration | Stacking | Category | Notes |
|---|---|---|---|---:|---|---|---|---|---|
| Normal enemy XP | `settings.py`, `systems/combat_system.py` | Kill normal enemy, collect XP crystal | Grants XP | `44` base | N/A | Run economy | Multiplied by curse room | XP / Leveling | Physical pickup after death |
| Normal enemy gold | same | Kill normal enemy, collect coin | Grants gold | `8` base | N/A | Run economy | Multiplied by curse room | Loot / Gold | Physical pickup after death |
| Elite reward | `systems/combat_system.py` | Kill elite | Reward multiplier | XP `5x`, gold `6x` | N/A | Run economy | Also affected by room reward multiplier | XP / Gold | High payout |
| Curse room reward | `systems/room_system.py` | Enter curse room | Reward multiplier | `2x` | Room-limited | Room | Multiplicative | Loot / XP | Affects normal/elite drops |
| Boss reward | `settings.py`, `systems/combat_system.py` | Kill boss | Immediate reward | `600 XP`, `180 gold` | Boss kill | Immediate | Not pickup-routed | XP / Gold | Boss flow intentionally separate |
| XP pickup split | `systems/loot_system.py` | Enemy drops | Reduces XP spam | unit `50`, max `4` drops/enemy | Per enemy | Pickup lifetime | Preserves exact value | XP / Leveling | Good quality-of-life layer |
| Coin split | `systems/loot_system.py` | Enemy drops | Coin units | unit `10`, remainder preserved | Per enemy | Pickup lifetime | Preserves exact value | Loot / Gold | `8g -> one 8-value coin` |
| Magnet pickup | `entities/pickup.py` | Near pickup | Pulls loot to player | radius `100`, delay `0.28s` | N/A | Pickup lifetime | N/A | Pickup / Magnet | Room clear can force collection pull |
| Level up | `entities/player.py` | XP reaches threshold | Adds pending perk choices | starts `100 XP`, next threshold `*1.28` | No hard level cap | Run-long | Exponential threshold | XP / Leveling | Each level creates one pending card |

## Part 2 - Build Categories

| Category | Features |
|---|---|
| Damage | Power Core, Heavy Rounds, Hollow Point, Glass Cannon, Kinetic Rounds, Needle Rounds legendary, Explosive Rounds legendary, Impact Drive legendary, Sharpen Blade, Double Barrel, Surge |
| Attack Speed | Rapid Fire, Overclock, Explosive Rounds tradeoff/legendary, Rapid Trigger, Surge |
| Crit | Critical Spark, Hollow Point legendary, crit overflow rule |
| Projectile Count | Split Shot, Legendary Split Shot |
| Projectile Behavior | Piercing Bullets, Piercing Tips, Explosive Rounds perk/shop, Bullet Speed Boost, Impact Drive, Impact Core, Hollow Point pierce reset |
| Melee | Knife, Sword; currently few/no perk/shop hooks |
| Dash / Mobility | Dash, Scout Boots, Phantom Step, Ghost |
| Defense / HP | Vital Core, Second Wind, Max Health shop, Glass Cannon tradeoff, Phantom Step tradeoff |
| Healing / Regen | Battle Recovery, Second Wind, Room Regen, Heal shop, room-clear regen |
| Loot / Gold | Enemy gold, elite multiplier, curse reward, boss gold |
| XP / Leveling | Enemy XP, elite multiplier, curse reward, boss XP, level thresholds |
| Pickup / Magnet | LootSystem magnet, forced room-clear pickup |
| Luck / Rarity | No explicit luck/rarity stat; perk option selection is random with tag diversity |
| Utility | Blast, knockback, projectile speed, pierce, Ghost invulnerability |
| Unknown / unclear | Synergy labels are displayed/identified but do not appear to change effects |

## Part 3 - Max Stack Analysis

Estimates assume all currently possible relevant shop upgrades and perk picks are maxed, including 3 normal picks plus 1 legendary pick per perk where applicable.

### Max Damage Build

| Metric | Estimate |
|---|---:|
| Possible additive damage bonus from damage-related perks/shop | About `+489` |
| Base projectile damage before multipliers | `25 + 489 = 514` |
| With Double Barrel | `1028` |
| With Surge | `2056` before crit/split |
| With max crit estimate | Up to `~6270` per crit projectile if crit multiplier reaches about `3.05` |

Expected strength: Extremely high.  
OP risk: Critical.  
Weak risk: Low.  
Exploit loop: More damage -> faster kills -> more XP/gold -> more cards/shop upgrades -> even more damage.  
Depends on: Damage perks, shop damage, Double Barrel, Surge, crit overflow.

### Max Fire-Rate Build

| Source | Max Contribution |
|---|---:|
| Rapid Fire | `+1.45` fire-rate multiplier |
| Overclock | `+1.90` |
| Rapid Trigger shop | `+0.48` |
| Heavy Rounds net | `-0.18` if maxed |
| Explosive Rounds net | `-0.30` if maxed |
| Approx run-long multiplier | `~4.35x` |
| With Surge | `~6.31x` effective |
| Cooldown result | Hits `0.055s` floor during high stacking |

Expected strength: Very high, especially with on-hit/explosive/pierce.  
OP risk: High due to cooldown floor and projectile count interaction.  
Weak risk: Low.  
Exploit loop: Fast kill speed accelerates XP/gold acquisition.  
Depends on: Rapid Fire, Overclock, Rapid Trigger, Surge.

### Max Multishot / Projectile Build

| Metric | Estimate |
|---|---:|
| Split Shot normal picks | Projectile count can rise from `1` to `4` over 3 normal picks |
| Legendary Split | Can reach `5` in normal max path; code cap allows up to `8` |
| Spread | Up to `30` degrees after 4 split picks, code caps `48` |
| Split damage multiplier | Legendary adds `+0.25`; count mitigation still applies |

Expected strength: High when paired with damage, crit, pierce, and explosive.  
OP risk: High as an amplifier, not by itself.  
Weak risk: Medium if picked without damage because split damage mitigation reduces per-bullet impact.  
Exploit loop: More bullets means more pierce/explosive coverage and more crit rolls.  
Depends on: Split Shot, damage build, pierce, explosive rounds.

### Max Crit Build

| Metric | Estimate |
|---|---:|
| Critical Spark chance | `3 * 0.30 + 0.80 = 1.70` |
| Base crit multiplier | `1.75` |
| Critical Spark legendary multiplier | `+0.35` |
| Hollow Point legendary multiplier | `+0.25` |
| Overflow chance contribution | `+0.70` multiplier from crit overflow |
| Effective crit multiplier estimate | `~3.05` |

Expected strength: Very high because crit overflow has no hard cap.  
OP risk: Critical when combined with max damage and multishot.  
Weak risk: Low after enough picks; medium early due to randomness.  
Exploit loop: Overflow turns excess chance into damage, so crit never becomes wasteful.  
Depends on: Critical Spark, Hollow Point, multishot.

### Max Dash / Mobility Build

| Source | Effect |
|---|---|
| Base dash | speed `900`, duration `0.24s`, cooldown `5.5s`, invulnerable at least `0.74s` |
| Scout Boots max | `+160` movement speed and dash cooldown reset on legendary |
| Phantom Step max | `+110` movement speed, net health penalty from normal picks, legendary `+0.20s` dash invulnerability |
| Ghost skill | `2s` invulnerability and `1.95x` movement |
| Overclock legendary | skill cooldown multiplier can reduce toward `0.55` floor |

Expected strength: High.  
OP risk: Medium-high if Ghost plus skill cooldown reduction becomes frequent invulnerability.  
Weak risk: Low.  
Exploit loop: Mobility reduces damage taken, allowing glass-cannon offense.  
Depends on: Scout Boots, Phantom Step, Ghost, Overclock legendary.

### Max Tank / HP Build

| Source | Max Contribution |
|---|---:|
| Vital Core | `3 * 48 + 110 = +254 max HP`, plus healing |
| Second Wind | `3 * 20 + 55 = +115 max HP` |
| Max Health shop | `6 * 18 = +108 max HP` |
| Base HP | `200` |
| Approx max before tradeoffs | `677 HP` |

Expected strength: Strong but less multiplicative than offense.  
OP risk: Medium.  
Weak risk: Low.  
Exploit loop: High HP plus regen reduces shop healing pressure.  
Depends on: Vital Core, Second Wind, Max Health shop.

### Max Regen / Healing Build

| Source | Max Contribution |
|---|---:|
| Base room clear regen | `10` |
| Battle Recovery | `3 * 24 + 70 = +142` |
| Second Wind | `3 * 10 + 30 = +60` |
| Room Regen shop | `4 * 12 = +48` |
| Approx room-clear heal | `260` |
| Heal shop | `45 HP` for `18 gold` repeatedly |

Expected strength: Very high sustain between rooms.  
OP risk: High if room clear is reliable.  
Weak risk: Medium during boss fights where room-clear healing does not help.  
Exploit loop: Sustain allows spending gold on offense rather than healing.  
Depends on: Room clears, Healer shop, HP pool.

### Max Loot / Gold Build

Current direct player power features: none beyond reward sources.  
Expected strength: Economy depends mostly on kill speed and room type, not gold-specific upgrades.  
OP risk: Indirect high because offense increases gold acquisition.  
Weak risk: Medium because no gold-focused build identity exists.  
Exploit loop: Curse room/elite rewards plus high DPS accelerates shop completion.  
Depends on: Reward multipliers, enemy counts, shop prices.

### Max XP / Leveling Build

Current direct XP modifiers: none beyond reward sources.  
Expected strength: XP gain depends on kill speed and reward multipliers.  
OP risk: Indirect high because high DPS accelerates level/card acquisition.  
Weak risk: Medium because no XP-build choices exist.  
Exploit loop: Damage -> XP -> perks -> damage.  
Depends on: Enemy density, elite rewards, curse room multiplier.

### Obvious Hybrid Build

Best current hybrid: Damage + Fire Rate + Split Shot + Crit + Double Barrel + Surge, with enough HP/regen to survive.

Expected strength: Extreme.  
OP risk: Critical.  
Weak risk: Low.  
Main issue: Nearly every offensive layer multiplies or amplifies every other offensive layer, while melee and utility do not participate equally.

## Part 4 - Current Perk/Card System

### Perk Cards

| Key | Name | Description | Implementation | Max Pick Behavior | Tags | Current Rarity | Recommendation |
|---|---|---|---|---|---|---|---|
| `rapid_fire` | Fire Rate Boost | +30% faster shooting | `+0.30 fire_rate_multiplier`; legendary `+0.55` | 3 normal + 1 legendary = `+1.45` | offense, fire_rate | None explicit | Keep base, cap stronger |
| `heavy_rounds` | Heavy Damage Rounds | +14 damage, -10% fire rate | `+14 damage`, fire rate `-0.10`; legendary `+32 damage`, `+0.12 fire rate` | Net `+74 damage`, `-0.18 fire rate` | offense, damage | None | Keep base/tradeoff |
| `power_core` | Damage Boost | +12 damage | `+12`; legendary `+35` | `+71 damage` | offense, damage | None | Keep base, maybe simpler damage card |
| `hollow_point` | Hollow Point | +20 damage, pierce becomes 0 | `+20`, set pierce `0`; legendary `+45`, pierce `0`, `+0.25 crit mult` | `+105 damage`, pierce reset risk | offense, damage, tradeoff | None | Convert to synergy or legendary |
| `glass_cannon` | Glass Cannon | +25 damage, -40 max health | `+25`, reduce max health 40; legendary `+60`, reduce 40 | `+135 damage`, up to `-160 HP` but floor 30 per reduction | offense, damage, tradeoff | None | Convert to rare/legendary |
| `split_shot` | Extra Projectile | +1 bullet, lower damage | +projectile count/spread; legendary +count/spread and `+0.25 split_damage_multiplier` | Count increases with caps | offense, projectile | None | Keep base, require clearer scaling |
| `needle_rounds` | Piercing Bullets | +1 pierce | `+1 pierce`; legendary `+3 pierce`, `+8 damage` | `+6 pierce`, `+8 damage` | offense, pierce | None | Keep base |
| `kinetic_rounds` | Bullet Speed Boost | +8 damage, +70 speed | `+8 damage`, `+70 projectile speed`; legendary `+24`, `+180` | `+48 damage`, `+390 speed` | offense, damage, speed | None | Keep utility/damage hybrid |
| `critical_spark` | Critical Chance Boost | +30% crit chance | `+0.30`; legendary `+0.80`, `+0.35 crit mult` | `+1.70 crit chance`, overflow active | offense, crit | None | Needs cap/rarity |
| `overclock` | Overclock | +40% faster shooting, -15 HP | `+0.40 fire rate`, `-15 HP`; legendary `+0.70`, skill cooldown `*0.80` to floor 0.55 | `+1.90 fire rate`, `-45 HP`, skill cooldown reduction | offense, fire_rate, tradeoff | None | Convert legendary effect to synergy |
| `explosive_rounds` | Explosive Rounds | Bullets explode, -15% fire rate | Sets explosive true, fire rate `-0.15`; legendary explosive true, `+0.15 fire rate`, `+10 damage` | Duplicate normal picks mostly repeat flag and stack penalty | offense, explosive, tradeoff | None | Redesign; dead duplicate risk |
| `impact_drive` | Bullet Knockback | +45% pushback | `+0.45 knockback_power`; legendary `+1.20`, `+8 damage` | `+2.55 knockback_power`, `+8 damage` | offense, utility | None | Keep utility |
| `vital_core` | Max Health Boost | +48 HP, heal 24 | `+48 HP`, heal 24; legendary `+110 HP`, full heal | `+254 HP` | defense, health | None | Keep base |
| `battle_recovery` | Room Clear Healing | +24 after each room | `+24 regen`; legendary `+70 regen`, `+35 HP`, heal 35 | `+142 regen`, `+35 HP` | defense, regen | None | Keep but cap sustain |
| `second_wind` | Second Wind | +20 HP, +10 regen | normal `+20 HP`, `+10 regen`; legendary `+55 HP`, `+30 regen`, heal 40 | `+115 HP`, `+60 regen` | defense, health, regen | None | Keep hybrid |
| `scout_boots` | Move Speed Boost | +30 speed | `+30 speed`; legendary `+70 speed`, reset dash cooldown | `+160 speed` | mobility, speed | None | Keep base |
| `phantom_step` | Phantom Step | +20 speed, -20 HP | `+20 speed`, `-20 HP`; legendary `+50 speed`, `+0.20s dash invuln` | `+110 speed`, `-60 HP`, dash invuln bonus | mobility, speed, tradeoff | None | Keep as mobility tradeoff |

### Roll and Synergy Behavior

| Topic | Current State |
|---|---|
| Card roll count | 3 options |
| Availability | Perks with `perk_counts[key] < PERK_PICK_LIMIT` |
| Pick limit | `PERK_PICK_LIMIT = 4` |
| Legendary behavior | Option becomes legendary when `taken >= 3`, so 4th pick applies `legendary_apply` |
| Synergy system | Tags are compared to previous picked tags and a label may be displayed |
| Synergy power | No implemented mechanical bonus found; labels only |
| Late weak cards | Yes. Any under-picked card can appear late regardless of build direction |
| Duplicate/dead cards | `explosive_rounds` repeated normals re-set the same boolean and mostly apply repeated fire-rate penalties |
| Overpowered combinations | Damage + fire rate + crit overflow + split shot + Double Barrel + Surge |

## Part 5 - Shop Upgrade System

### Blacksmith

| Key | Name | Base Cost | Scaling | Max Level | Effect | Total Max Effect | Overlaps With |
|---|---|---:|---:|---:|---|---|---|
| `damage` | Sharpen Blade | 30 | `cost * 1.72^level` | 6 | `+5 damage_bonus` | `+30 damage` | Many damage perks |
| `pierce` | Piercing Tips | 45 | same | 3 | `+1 pierce` | `+3 pierce` | Needle Rounds |
| `firerate` | Rapid Trigger | 45 | same | 4 | `+0.12 fire_rate_multiplier` | `+0.48` | Rapid Fire, Overclock |
| `weapon_double` | Double Barrel | 120 | same | 1 | `weapon_damage_multiplier = max(..., 2.0)` | `2x projectile damage` | All projectile damage |
| `explosive_rounds` | Explosive Rounds | 150 | same | 1 | `explosive_rounds = True` | Explosive bullets | Explosive Rounds perk |
| `knockback` | Impact Core | 80 | same | 4 | `+0.55 knockback_power` | `+2.20` | Impact Drive |

### Healer

| Key | Name | Cost | Scaling | Max Level | Effect | Total Max Effect | Overlaps With |
|---|---|---:|---|---|---|---|---|
| `heal` | Heal | 18 | No scaling | Repeatable | Heal `45` | Gold-limited | Regen/HP sustain |
| `maxhp` | Max Health | 38 | `cost * 1.72^level` | 6 | `+18 max HP`, heal 18 | `+108 HP` | Vital Core, Second Wind |
| `regen` | Room Regen | 35 | same | 4 | `+12 room-clear regen` | `+48 regen` | Battle Recovery, Second Wind |
| `skill_blast` | Skill: Blast | 70 | No scaling | No tracked max level | Sets active skill | Replaces Q | Utility |
| `skill_surge` | Skill: Surge | 80 | No scaling | No tracked max level | Sets active skill | Replaces Q | Damage/fire-rate |
| `skill_ghost` | Skill: Ghost | 90 | No scaling | No tracked max level | Sets active skill | Replaces Q | Mobility/defense |

Shop overlap risk: Blacksmith upgrades can make generic damage/fire-rate/pierce cards feel less special, but the bigger issue is the opposite: shop upgrades multiply and stabilize already-strong perk builds. `Double Barrel` is the strongest single shop upgrade because it multiplies all projectile damage.

## Part 6 - Dash / Q Ability Audit

| Aspect | Current State |
|---|---|
| Default cooldown | `5.5s` |
| Dash duration | `0.24s` |
| Dash speed | `900` |
| Invulnerability | `DASH_DURATION + 0.50 + dash_invuln_bonus`, so base about `0.74s` |
| Damage | None |
| Skill routing | `try_dash()` calls `try_active_skill()`, so Blast/Surge/Ghost replace default dash |
| Cooldown modifier | `skill_cooldown_multiplier`, mainly from Overclock legendary, floor logic in perk effect at `0.55` |
| Perk interactions | Scout Boots resets dash cooldown on legendary; Phantom Step adds speed and legendary dash invuln |
| Current feel | Mechanically strong: long invulnerability relative to movement burst |
| Balance risk | Ghost and reduced skill cooldown can create frequent safety windows |
| Future hooks | Dash damage, dash afterimage, dash reload, dash crit, dash shield, dash pickup magnet, dash cooldown refund on kill |

## Part 7 - Problems & Risks

| Priority | Problem | Why It Matters | Suggested Direction |
|---|---|---|---|
| P0 | Projectile offense has too many multiplicative layers | Damage, Double Barrel, Surge, crit, multishot, fire-rate, pierce, explosive all amplify each other | Add caps or move some effects into exclusive/synergy/legendary tiers |
| P0 | Crit overflow has no hard ceiling | Excess crit chance remains useful forever by becoming multiplier | Cap overflow or reserve overflow for legendary-only |
| P0 | `Double Barrel` is a cheap global projectile damage multiplier | Makes flat damage cards and Surge much stronger | Increase cost, add requirement, or redesign as projectile behavior |
| P1 | Surge is both `2x` damage and `1.45x` fire rate | Huge temporary DPS multiplier | Make it build-defining with clearer tradeoff/cooldown |
| P1 | Explosive Rounds perk has dead duplicate behavior | Repeated normal picks mostly re-set boolean and stack fire-rate penalty | Convert to staged upgrade path |
| P1 | Melee has almost no progression support | Knife/Sword do not benefit from bullet damage, crit, pierce, projectile count | Add separate melee card family later |
| P1 | Sustain can become very high after room clear | Regen build can undo attrition between rooms | Cap room-clear healing or make it conditional |
| P1 | Gold/XP builds are not real build paths | Economy progression is passive result of killing faster | Add future economy cards only after offense caps |
| P2 | Shop skill purchases can be repeated without tracked ownership | They spend gold each time and re-equip skill | Add owned/equipped distinction later |
| P2 | Synergy labels do not provide mechanics | Player may expect a bonus from synergy text | Either implement synergy cards or remove label until real |

## Part 8 - Proposed Future Card Architecture

Recommended model:

- Base Cards: common, max level 1-3, small additive improvements.
- Synergy Cards: unlocked by tag combinations, max level 1, build-specific, stronger than base.
- Legendary Cards: rare, max level 1, build-defining, often exclusive.

### Current Perk Recommendations

| Current Perk | Recommended Layer | Tags | Max Level | Rarity | Requirements | Exclusivity / Notes |
|---|---|---|---:|---|---|---|
| Fire Rate Boost | Base | offense, fire_rate | 3 | Common | None | Keep simple |
| Heavy Damage Rounds | Base or Synergy | offense, damage, tradeoff | 3 | Common/Uncommon | None | Good tradeoff card |
| Damage Boost | Base | offense, damage | 3 | Common | None | Core baseline |
| Hollow Point | Synergy | damage, crit, anti_pierce | 1 | Rare | Damage + Crit | Conflicts with pierce builds |
| Glass Cannon | Legendary | damage, tradeoff | 1 | Rare/Legendary | At least 2 damage cards | Exclusive with tank legendary |
| Extra Projectile | Base -> Synergy finisher | projectile, multishot | 3 base + 1 synergy | Common/Rare | None | Legendary should be separate card |
| Piercing Bullets | Base | projectile, pierce | 3 | Common | None | Good projectile utility |
| Bullet Speed Boost | Base | projectile, speed, damage | 3 | Common | None | Keep modest |
| Critical Chance Boost | Base | crit | 3 | Common | None | Overflow should require legendary |
| Overclock | Synergy | fire_rate, cooldown, tradeoff | 1 | Rare | Fire-rate + mobility or fire-rate + damage | Strong identity card |
| Explosive Rounds | Legendary | explosive, aoe | 1 | Legendary | Damage + projectile behavior | Make single acquisition, not repeatable |
| Bullet Knockback | Base / Utility | utility, knockback | 3 | Common | None | Useful but not build-defining |
| Max Health Boost | Base | defense, health | 3 | Common | None | Keep |
| Room Clear Healing | Base / Synergy | defense, regen | 3 | Common | None | Cap or conditionalize |
| Second Wind | Synergy | defense, health, regen | 1 | Rare | Health + regen | Good tank synergy |
| Move Speed Boost | Base | mobility, speed | 3 | Common | None | Keep |
| Phantom Step | Synergy | mobility, evasion, tradeoff | 1 | Rare | Speed + dash | Good mobility identity |

### Proposed Card Data Fields

| Field | Purpose |
|---|---|
| `id` | Stable card key |
| `name` | Display name |
| `tier` | base, synergy, legendary |
| `rarity` | common, uncommon, rare, legendary |
| `tags` | Build classification |
| `requires_tags` | Unlock requirements for synergy/legendary |
| `excludes_tags` | Prevent incompatible builds |
| `max_level` | Independent from global pick limit |
| `effects` | Data-driven mutation descriptors |
| `tradeoffs` | Explicit negative effects |
| `weight` | Roll weight |
| `min_room` / `min_level` | Progression gating |

## Top 10 Immediate Balance Fixes

1. Cap or redesign crit overflow.
2. Reprice or redesign `Double Barrel`.
3. Split Surge into a clearer active-skill build choice with stronger tradeoff.
4. Fix Explosive Rounds duplicate picks.
5. Add separate melee scaling before adding more melee weapons.
6. Put hard caps on effective fire-rate multiplier before cooldown floor dominates.
7. Reduce stacking between flat damage and global damage multipliers.
8. Add ownership checks for shop skills so re-buying is not ambiguous.
9. Cap room-clear regen or make part of it conditional.
10. Make synergy labels either mechanical or purely hidden until synergy cards exist.

## Top 10 Design Opportunities

1. True melee card family for knife/sword.
2. Projectile archetypes: pierce, explosive, crit, multishot as distinct paths.
3. Economy cards after offense is capped: bonus coin, magnet, shop discount.
4. Dash cards: cooldown refund, shield dash, ghost dash, dash reload.
5. Defensive archetypes: armor, barrier, regen, max HP, emergency heal.
6. Legendary exclusions to force meaningful build identity.
7. Synergy cards unlocked by tag combinations instead of passive labels.
8. Rarity-weighted card rolls.
9. Late-game roll filtering to reduce weak off-build options.
10. Card collection UI showing build tags and unlock progress.

## Suggested Next Implementation Phase

Do not rebalance numbers first. The safer next phase is architecture/data cleanup for cards:

1. Create card schema fields for tier, rarity, max level, requirements, exclusions, and effect descriptors.
2. Keep existing cards behavior-compatible while mapping them into the new schema.
3. Add validation that no card has duplicate id, missing effect, impossible requirement, or dead duplicate behavior.
4. Add a read-only card debug panel showing currently eligible cards and why.
5. Only then rebalance numbers and roll weights.

## Suggested Pixel-Art Card List To Draw First

1. Damage Boost / Power Core
2. Fire Rate Boost / Rapid Fire
3. Extra Projectile / Split Shot
4. Critical Spark
5. Piercing Bullets
6. Explosive Rounds
7. Glass Cannon
8. Vital Core
9. Room Clear Healing
10. Scout Boots
11. Phantom Step
12. Surge Skill
13. Ghost Skill
14. Blast Skill
15. Sword / Melee Mastery future card
16. Coin Magnet / Economy future card

