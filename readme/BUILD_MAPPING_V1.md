# BlueCube Build Mapping v1

References:

- `BLUECUBE_DESIGN_BIBLE.md`
- `PLAYER_POWER_AUDIT.md`
- Current perk, upgrade, weapon, player, loot, and progression definitions

Scope:

- Design classification only.
- No implementation proposed.
- No balance proposed.
- No new cards, perks, mechanics, weapons, or systems invented.

## Purpose

This document maps all existing BlueCube progression elements to the four official Combat Identities:

- Gunslinger
- Ninja
- Engineer
- Vampire

Classification options:

- Gunslinger
- Ninja
- Engineer
- Vampire
- Shared
- Unassigned

This document is intended to become the reference for future card-system restructuring.

## High-Level Findings

| Build | Current Completion | Summary |
|---|---:|---|
| Gunslinger | 70% | Strongly supported by existing projectile, fire-rate, crit, pierce, multishot, and pistol systems. Mostly needs identity restructuring, not new gameplay systems. |
| Ninja | 45% | Partially supported by dash, speed, Ghost, knife, sword, and close-range weapons. Needs card restructuring and likely future mechanics for close-range burst/reward identity. |
| Engineer | 5% | Mostly unsupported. Current game has no turret, drone, trap, tesla, or automation gameplay. Requires actual new gameplay mechanics later. |
| Vampire | 35% | Partially supported by HP, healing, regen, loot/XP-on-kill economy, and sustain. Lacks lifesteal, souls, summons, or kill-fed scaling mechanics. |

## Build Analysis

## Gunslinger

**Current Completion**

70%

**Core Fantasy**

"I never stop shooting."

**Current Supporting Systems**

- Pistol projectile system.
- Fire-rate multiplier.
- Projectile count and spread.
- Pierce.
- Crit chance and crit multiplier.
- Projectile speed.
- Explosive projectiles.
- Projectile knockback.
- Gun shooting animation and shooting audio.
- Surge active skill as a temporary projectile-DPS amplifier.

**Current Cards**

- Fire Rate Boost
- Heavy Damage Rounds
- Damage Boost
- Hollow Point
- Glass Cannon
- Extra Projectile
- Piercing Bullets
- Bullet Speed Boost
- Critical Chance Boost
- Overclock
- Explosive Rounds
- Bullet Knockback

**Current Shop Upgrades**

- Sharpen Blade
- Piercing Tips
- Rapid Trigger
- Double Barrel
- Explosive Rounds
- Impact Core

**Current Skills**

- Surge

**Current Weapons**

- Pistol

**Missing Pieces**

- Momentum/streak mechanics are not currently implemented.
- No explicit reward for uninterrupted shooting.
- No explicit penalty/recovery loop when interrupted.
- No card architecture separating projectile volume, rhythm, and streak styles.

**Conflicting Systems**

- Generic damage cards can support Gunslinger but currently read as raw number upgrades.
- Surge is very broadly useful and can become a generic DPS button rather than a Gunslinger identity tool.
- Explosive Rounds could become Engineer-adjacent later, but currently behaves as projectile offense.

**Recommended Existing Cards To Move Into This Build**

- Fire Rate Boost
- Extra Projectile
- Piercing Bullets
- Bullet Speed Boost
- Critical Chance Boost
- Overclock
- Heavy Damage Rounds
- Hollow Point
- Explosive Rounds, temporarily
- Bullet Knockback, temporarily

**What Should Remain Shared**

- Generic Damage Boost / Power Core
- Some generic damage shop upgrades until card restructuring creates clearer identities
- Base XP/gold/leveling systems

## Ninja

**Current Completion**

45%

**Core Fantasy**

"You can't catch me."

**Current Supporting Systems**

- Base dash.
- Dash invulnerability.
- Dash ghost trail.
- Movement speed stat.
- Ghost active skill.
- Knife melee weapon.
- Sword melee weapon.
- Close-range melee hit logic.
- Blast active skill as close-range control.

**Current Cards**

- Move Speed Boost
- Phantom Step
- Overclock, secondary due skill cooldown legendary behavior
- Glass Cannon, possible but currently too generic

**Current Shop Upgrades**

- Skill: Ghost
- Skill: Blast
- Max Health, as a safety fallback
- Heal, as recovery support

**Current Skills**

- Dash
- Ghost
- Blast

**Current Weapons**

- Knife
- Sword

**Missing Pieces**

- No shuriken mechanic.
- No dash reward loop beyond movement/invulnerability.
- No dodge reward.
- No close-range burst cards.
- No melee-specific scaling cards.
- No card identity around "stay near danger."

**Conflicting Systems**

- Knife and sword do not benefit from most existing offensive progression.
- Phantom Step and Scout Boots support mobility, but not close-range burst.
- Ghost is defensive mobility and could blur Ninja with general survival if not framed carefully.

**Recommended Existing Cards To Move Into This Build**

- Move Speed Boost
- Phantom Step
- Potentially Overclock as hybrid only, if skill cooldown becomes a Ninja secondary hook
- Glass Cannon only if reframed around close-range risk later

**What Should Remain Shared**

- Base Dash
- Heal
- Max Health
- Basic movement speed as a player stat

## Engineer

**Current Completion**

5%

**Core Fantasy**

"My machines fight for me."

**Current Supporting Systems**

- No direct turret, drone, trap, tesla, or automation mechanics currently exist.
- Projectile knockback and explosive projectile behavior could later become Engineer-adjacent, but they are not machines or setup tools now.
- Developer prefab architecture exists, but it is not player progression gameplay.

**Current Cards**

- None directly.
- Explosive Rounds and Bullet Knockback are only weak candidates if future restructuring reframes them.

**Current Shop Upgrades**

- None directly.
- Impact Core and Explosive Rounds are possible weak candidates, but currently behave as gun/projectile upgrades.

**Current Skills**

- None directly.
- Blast is area control, but not automation/setup.

**Current Weapons**

- None directly.

**Missing Pieces**

- Turrets.
- Drones.
- Traps.
- Tesla effects.
- Automation scaling.
- Setup time / weak early-game tradeoff.
- Cards that place, improve, trigger, or automate tools.

**Conflicting Systems**

- Existing projectile upgrades may be tempting to classify as Engineer, but doing so would dilute the Engineer fantasy.
- No existing progression can produce the Engineer success moment: "My machines control the battlefield."

**Recommended Existing Cards To Move Into This Build**

- None as primary Engineer cards.

**What Should Remain Shared**

- Explosive Rounds should remain Shared or temporary Gunslinger until real Engineer mechanics exist.
- Bullet Knockback / Impact Core should remain Shared utility until automation tools exist.

## Vampire

**Current Completion**

35%

**Core Fantasy**

"The battlefield feeds me."

**Current Supporting Systems**

- Room-clear healing.
- Max health stacking.
- Heal shop.
- HP sustain through returning to hub.
- XP/gold rewards from kills.
- Loot pickups generated by deaths.
- Elite and curse reward multipliers.

**Current Cards**

- Max Health Boost
- Room Clear Healing
- Second Wind

**Current Shop Upgrades**

- Heal
- Max Health
- Room Regen

**Current Skills**

- None directly.
- Ghost can support survival but does not express feeding, blood, souls, lifesteal, or summons.

**Current Weapons**

- None directly.

**Missing Pieces**

- Lifesteal.
- Souls.
- Kill-fed temporary scaling.
- Summons.
- Healing from kills or nearby deaths.
- Risky "weak before kills start" ramp identity.

**Conflicting Systems**

- Current healing is mostly post-room or shop-based, not battlefield-fed.
- Max HP can make Vampire feel like a generic tank rather than a death-fed identity.
- Loot/XP/gold are kill rewards but not Vampire power without a mechanic that converts death into sustain or scaling.

**Recommended Existing Cards To Move Into This Build**

- Room Clear Healing
- Second Wind
- Max Health Boost, partially

**What Should Remain Shared**

- Heal shop can remain Shared until Vampire has lifesteal/soul mechanics.
- Max Health may remain Shared or become hybrid Vampire/Shared.
- Base loot and XP systems should remain Shared.

## Existing Progression Classification

### Perk Cards

| Existing Perk | Gunslinger | Ninja | Engineer | Vampire | Shared | Classification |
|---|---:|---:|---:|---:|---:|---|
| Fire Rate Boost | X |  |  |  |  | Gunslinger |
| Heavy Damage Rounds | X |  |  |  |  | Gunslinger |
| Damage Boost |  |  |  |  | X | Shared |
| Hollow Point | X |  |  |  |  | Gunslinger |
| Glass Cannon | X | X |  |  |  | Gunslinger / Ninja hybrid |
| Extra Projectile | X |  |  |  |  | Gunslinger |
| Piercing Bullets | X |  |  |  |  | Gunslinger |
| Bullet Speed Boost | X | X |  |  |  | Gunslinger / Ninja hybrid |
| Critical Chance Boost | X |  |  |  |  | Gunslinger |
| Overclock | X | X |  |  |  | Gunslinger / Ninja hybrid |
| Explosive Rounds | X |  |  |  | X | Gunslinger, Shared until Engineer exists |
| Bullet Knockback | X |  |  |  | X | Shared utility / Gunslinger |
| Max Health Boost |  |  |  | X | X | Vampire / Shared |
| Room Clear Healing |  |  |  | X |  | Vampire |
| Second Wind |  |  |  | X | X | Vampire / Shared |
| Move Speed Boost |  | X |  |  |  | Ninja |
| Phantom Step |  | X |  |  |  | Ninja |

### Shop Upgrades

| Shop Upgrade | Gunslinger | Ninja | Engineer | Vampire | Shared | Classification |
|---|---:|---:|---:|---:|---:|---|
| Sharpen Blade |  |  |  |  | X | Shared |
| Piercing Tips | X |  |  |  |  | Gunslinger |
| Rapid Trigger | X |  |  |  |  | Gunslinger |
| Double Barrel | X |  |  |  |  | Gunslinger |
| Explosive Rounds | X |  |  |  | X | Gunslinger / Shared until Engineer exists |
| Impact Core | X |  |  |  | X | Shared utility / Gunslinger |
| Heal |  |  |  | X | X | Vampire / Shared |
| Max Health |  |  |  | X | X | Vampire / Shared |
| Room Regen |  |  |  | X |  | Vampire |
| Skill: Blast |  | X |  |  | X | Ninja / Shared control |
| Skill: Surge | X |  |  |  |  | Gunslinger |
| Skill: Ghost |  | X |  |  |  | Ninja |

### Active Skills

| Active Skill | Gunslinger | Ninja | Engineer | Vampire | Shared | Classification |
|---|---:|---:|---:|---:|---:|---|
| Dash |  | X |  |  | X | Ninja / Shared base ability |
| Blast |  | X |  |  | X | Ninja / Shared control |
| Surge | X |  |  |  |  | Gunslinger |
| Ghost |  | X |  |  |  | Ninja |

### Weapons

| Weapon | Gunslinger | Ninja | Engineer | Vampire | Shared | Classification |
|---|---:|---:|---:|---:|---:|---|
| Pistol | X |  |  |  |  | Gunslinger |
| Knife |  | X |  |  |  | Ninja |
| Sword |  | X |  |  |  | Ninja |

### Passive Mechanics and Player Stats

| Mechanic / Stat | Gunslinger | Ninja | Engineer | Vampire | Shared | Classification |
|---|---:|---:|---:|---:|---:|---|
| Base move speed |  | X |  |  | X | Shared / Ninja |
| Base max HP |  |  |  | X | X | Shared / Vampire |
| Damage bonus | X |  |  |  | X | Shared / Gunslinger |
| Fire-rate multiplier | X |  |  |  |  | Gunslinger |
| Projectile count | X |  |  |  |  | Gunslinger |
| Pierce | X |  |  |  |  | Gunslinger |
| Crit chance | X |  |  |  |  | Gunslinger |
| Crit multiplier | X |  |  |  |  | Gunslinger |
| Projectile knockback | X |  |  |  | X | Shared utility / Gunslinger |
| Projectile speed | X | X |  |  | X | Shared / Gunslinger / Ninja |
| Explosive bullets | X |  |  |  | X | Gunslinger / Shared until Engineer exists |
| Dash invulnerability |  | X |  |  |  | Ninja |
| Skill cooldown multiplier | X | X |  |  | X | Shared / Gunslinger / Ninja |
| Room-clear regen |  |  |  | X |  | Vampire |
| Dash ghost trail |  | X |  |  |  | Ninja feel support |

### Room Rewards, Loot, and Progression

| System | Gunslinger | Ninja | Engineer | Vampire | Shared | Classification |
|---|---:|---:|---:|---:|---:|---|
| Normal enemy XP drops |  |  |  |  | X | Shared |
| Normal enemy gold drops |  |  |  |  | X | Shared |
| Elite reward multiplier |  |  |  | X | X | Shared / Vampire-adjacent |
| Curse reward multiplier |  |  |  |  | X | Shared |
| Boss reward |  |  |  |  | X | Shared |
| Loot magnet |  |  |  |  | X | Shared |
| Forced room-clear loot collection |  |  |  |  | X | Shared |
| Level-up card choices |  |  |  |  | X | Shared progression |
| Perk pick limit / legendary 4th pick |  |  |  |  | X | Shared card architecture |
| Synergy labels | X | X |  | X | X | Shared incomplete architecture |
| Room start countdown |  |  |  |  | X | Shared flow |
| Run timer / room timer |  |  |  |  | X | Shared flow |

## Matrix: Perks, Shop Upgrades, Active Skills, Weapons

Legend:

- `P` = Primary fit
- `S` = Secondary or hybrid fit
- `T` = Temporary fit until a better identity/system exists
- blank = Does not currently belong

| Element | Type | Gunslinger | Ninja | Engineer | Vampire | Shared |
|---|---|---:|---:|---:|---:|---:|
| Fire Rate Boost | Perk | P |  |  |  |  |
| Heavy Damage Rounds | Perk | P |  |  |  |  |
| Damage Boost | Perk | S |  |  |  | P |
| Hollow Point | Perk | P |  |  |  |  |
| Glass Cannon | Perk | P | S |  |  |  |
| Extra Projectile | Perk | P |  |  |  |  |
| Piercing Bullets | Perk | P |  |  |  |  |
| Bullet Speed Boost | Perk | P | S |  |  |  |
| Critical Chance Boost | Perk | P |  |  |  |  |
| Overclock | Perk | P | S |  |  |  |
| Explosive Rounds | Perk | P |  | T |  | S |
| Bullet Knockback | Perk | S |  | T |  | P |
| Max Health Boost | Perk |  |  |  | S | P |
| Room Clear Healing | Perk |  |  |  | P |  |
| Second Wind | Perk |  |  |  | P | S |
| Move Speed Boost | Perk |  | P |  |  |  |
| Phantom Step | Perk |  | P |  |  |  |
| Sharpen Blade | Shop | S |  |  |  | P |
| Piercing Tips | Shop | P |  |  |  |  |
| Rapid Trigger | Shop | P |  |  |  |  |
| Double Barrel | Shop | P |  |  |  |  |
| Explosive Rounds | Shop | P |  | T |  | S |
| Impact Core | Shop | S |  | T |  | P |
| Heal | Shop |  |  |  | S | P |
| Max Health | Shop |  |  |  | S | P |
| Room Regen | Shop |  |  |  | P |  |
| Skill: Blast | Shop |  | S |  |  | P |
| Skill: Surge | Shop | P |  |  |  |  |
| Skill: Ghost | Shop |  | P |  |  |  |
| Dash | Active Skill |  | P |  |  | S |
| Blast | Active Skill |  | S |  |  | P |
| Surge | Active Skill | P |  |  |  |  |
| Ghost | Active Skill |  | P |  |  |  |
| Pistol | Weapon | P |  |  |  |  |
| Knife | Weapon |  | P |  |  |  |
| Sword | Weapon |  | P |  |  |  |

## Direct Answers

### 1. Can the current game support all four Builds without adding new systems?

No.

The current game can meaningfully support Gunslinger and partially support Ninja and Vampire. It cannot currently support Engineer as an official build fantasy because no existing gameplay creates turrets, drones, traps, tesla effects, automation, setup tools, or machines that fight for the player.

### 2. Which Build is closest to completion?

Gunslinger.

Existing projectile, fire-rate, multishot, pierce, crit, explosive, pistol, and Surge systems already produce most of the Gunslinger fantasy: continuous shooting and room-filling projectile volume.

### 3. Which Build requires only card restructuring?

Gunslinger is closest to requiring only card restructuring.

Ninja requires card restructuring plus likely future close-range reward mechanics. Vampire requires card restructuring plus likely future death-fed mechanics. Engineer cannot be solved by card restructuring alone.

### 4. Which Build requires actual new gameplay mechanics?

Engineer clearly requires new gameplay mechanics.

Vampire also likely requires new gameplay mechanics to become more than generic HP/regen. Specifically, it needs lifesteal, soul, summon, or death-fed scaling mechanics.

Ninja may require new mechanics for dash rewards, close-range burst, dodge rewards, or shuriken identity, but it has enough base systems to begin restructuring.

### 5. Which current cards should become Shared instead of belonging to one Build?

Recommended Shared cards:

- Damage Boost
- Bullet Knockback
- Max Health Boost
- Second Wind, possibly Shared/Vampire hybrid

Temporary Shared cards until better identities exist:

- Explosive Rounds
- Bullet Speed Boost, if not committed to Gunslinger

### 6. Which current cards have no identity and should eventually be redesigned?

Cards with weak or unclear identity:

- Damage Boost: pure number increase; should become Shared baseline or be redesigned.
- Heavy Damage Rounds: currently a number tradeoff; can become Gunslinger if framed around rhythm/slow heavy shots.
- Power Core / Damage Boost: no fantasy beyond higher damage.
- Bullet Knockback: utility effect but no official build fantasy yet.
- Explosive Rounds: useful but not clearly Gunslinger, Ninja, Engineer, or Vampire in current implementation.
- Max Health Boost: defensive number increase; may be Shared or Vampire-adjacent but does not currently express "battlefield feeds me."

Cards with identity but incomplete support:

- Room Clear Healing: Vampire-adjacent but happens after combat, not from battlefield death.
- Second Wind: Vampire-adjacent sustain, but generic defensive value.
- Glass Cannon: risk/reward fantasy exists, but not clearly tied to one official build.

## Restructuring Reference Summary

| Identity | Existing System Support | Card Restructure Enough? | Needs New Mechanics? |
|---|---|---:|---:|
| Gunslinger | Strong | Yes | Not immediately |
| Ninja | Partial | Partly | Eventually |
| Engineer | Almost none | No | Yes |
| Vampire | Partial sustain only | Partly | Likely |

## Final Classification Notes

The current card ecosystem is heavily biased toward projectile offense. Most offensive cards should initially be reviewed through the Gunslinger lens, but not all should remain there permanently.

The safest restructuring order is:

1. Map and clean Gunslinger from existing projectile cards.
2. Map Ninja from existing dash/speed/melee tools.
3. Map Vampire from healing/sustain tools.
4. Leave Engineer mostly empty until actual automation mechanics exist.

This document does not propose implementation. It only classifies what already exists.

