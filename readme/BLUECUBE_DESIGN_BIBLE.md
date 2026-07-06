# BlueCube Design Bible v0.2

## Purpose

This document is the authoritative design reference for BlueCube progression, cards, perks, upgrades, weapons, rewards, and future combat identity work.

BlueCube is not designed around random upgrades.

BlueCube is designed around Combat Identities.

The player should finish a run thinking:

> "I became something."

Not:

> "My numbers became bigger."

## Core Vision

BlueCube is a fast-paced action roguelite where every run gradually evolves into a unique combat identity.

Cards exist to shape identity.

Numbers exist only to support identity.

## Core Design Rules

These rules override future feature proposals.

1. Identity before Numbers.
2. Guide the player. Never lock the player.
3. Depth before Breadth. Improve existing identities before creating new ones.
4. No Fake Choices. Every card choice should represent a meaningful decision.
5. Every Build must have a Fantasy, Strength, and Weakness.
6. Every Card must reinforce at least one Build.
7. Every Build must create memorable moments.
8. More Decisions. Less Numbers.
9. If a Build requires more than three sentences to explain, it is probably too complicated.

Avoid obvious choices such as:

- `+10 Damage`
- `+11 Damage`

These are numerical comparisons, not identity choices.

## Official Build Identities

Only these identities currently exist.

No additional identities may be considered official until explicitly promoted into this Design Bible.

### 1. Gunslinger

**Fantasy**

"I never stop shooting."

**Success Moment**

"The entire room is filled with my bullets."

**Strength**

Continuous fire, projectile volume, and momentum.

**Weakness**

Loses momentum if interrupted.

**Tags**

- `gun`
- `projectile`
- `fire_rate`
- `momentum`
- `streak`

### 2. Ninja

**Fantasy**

"You can't catch me."

**Success Moment**

"I dashed through the entire enemy group without taking damage."

**Strength**

Dash, speed, close-range burst, and aggressive mobility.

**Weakness**

Must stay close to danger.

**Tags**

- `dash`
- `speed`
- `mobility`
- `evade`
- `close_range`
- `shuriken`

### 3. Engineer

**Fantasy**

"My machines fight for me."

**Success Moment**

"I barely shoot anymore because my machines control the battlefield."

**Strength**

Turrets, drones, automation, battlefield control, and setup-based power.

**Weakness**

Weak early game. Requires setup.

**Tags**

- `turret`
- `drone`
- `tesla`
- `automation`
- `trap`

### 4. Vampire

**Fantasy**

"The battlefield feeds me."

**Success Moment**

"The more enemies appear, the harder I become to kill."

**Strength**

Life steal, souls, healing, summons, and sustain through combat.

**Weakness**

Needs kills to scale.

**Tags**

- `blood`
- `lifesteal`
- `heal`
- `soul`
- `summon`

## Hybrid Rule

Hybrid builds are allowed.

However, one Build should remain dominant.

Approximate philosophy:

- 80% Primary Identity
- 20% Secondary Identity

The goal is to enrich an identity, not erase it.

## Feature Acceptance Rule

Before implementing any of the following:

- perk
- card
- upgrade
- weapon mechanic
- shop item
- NPC reward
- progression
- loot mechanic
- room mechanic
- legendary
- synergy

The feature must answer:

1. Which Build Identity does this belong to?
2. Does it reinforce that Build Fantasy?
3. Does it invalidate another Build?
4. Does it follow the Core Design Rules?

Only then can implementation begin.

## Future Identities

The following remain experimental only.

Do not design around them yet.

- Berserker
- Treasure Hunter
- Stormcaller
- Commander
- Demolitionist

These may be promoted later only after the first four identities are proven fun.

## Current Development Priority

Do not create new builds.

Current priority is to deepen the existing four identities:

- Gunslinger
- Ninja
- Engineer
- Vampire

Future perk/card restructuring should be evaluated using this Design Bible before implementation.

When unsure, prefer making an existing build deeper instead of creating a new build.

## Design Status

**Official Builds**

- Gunslinger
- Ninja
- Engineer
- Vampire

**Experimental Builds**

- Berserker
- Treasure Hunter
- Stormcaller
- Commander
- Demolitionist

**Current Development Focus**

Refine and restructure the current perk/card ecosystem around the four official Combat Identities.

Do not add new build identities during the current phase.

**Future Review Items**

- Validate that every existing card supports at least one official Build.
- Identify cards that are only numerical upgrades and redesign them around identity.
- Define build-specific base cards, synergies, and legendary cards.
- Ensure hybrid cards enrich a primary identity without erasing its weakness.
- Promote future identities only after the first four identities are proven fun.

