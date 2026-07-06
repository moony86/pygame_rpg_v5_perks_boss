# Data-Driven Readiness Review

This review evaluates whether the current Python definition modules are ready
to be externalized to JSON or YAML later. This is not an implementation plan for
loading external files yet.

## Summary

JSON/YAML should not be introduced yet. The project now has useful Python
definition modules, but several definitions still reference Python enums,
callables, tuples, and runtime systems. The safest next phase is to stabilize
schemas and route all definition access through the registry before external
file loading.

## Weapon Definitions

- Safe to externalize now: partial.
- Stable data: weapon id, display name, attack type, cooldown, melee damage,
  melee range, arc degrees, knockback.
- Still depends on Python logic: weapon classes still build attack requests;
  projectile behavior is handled by `ShootingSystem`; `Player` still manually
  registers weapon classes.
- Risk of JSON too early: external data could imply that adding a weapon is
  data-only, but a new attack type still requires Python code in the weapon
  layer and Game/combat routing.
- Suggested schema shape:

```json
{
  "id": "knife",
  "display_name": "Knife",
  "attack_type": "melee_arc",
  "cooldown": 0.38,
  "attack": {
    "damage": 35,
    "range": 85,
    "arc_degrees": 105,
    "knockback": 26
  }
}
```

## Enemy Definitions

- Safe to externalize now: no, except for a small subset.
- Stable data: id, display name, category, behavior type, draw profile, threat
  cost.
- Still depends on Python logic: definitions use `EnemyType` enum keys; enemy
  stat construction, AI behavior, attack actions, draw branches, boss rules,
  wave pools, and boss summon pools remain procedural.
- Risk of JSON too early: externalizing enemy definitions now would create two
  sources of truth because `Enemy` still computes most stats and behavior from
  branches. Enum serialization also needs a stable string mapping first.
- Suggested schema shape:

```json
{
  "id": "ranged_three",
  "display_name": "Triple Ranged",
  "category": "ranged",
  "behavior_type": "ranged",
  "draw_profile": "ranged",
  "threat_cost": 5,
  "enemy_type": "RANGED_THREE"
}
```

## Room Definitions

- Safe to externalize now: yes for static metadata only.
- Stable data: id, display name, title, message, color, spawn multiplier, enemy
  difficulty.
- Still depends on Python logic: room order, target kill formulas, survival time
  formula, reward multiplier rule, clear rules, scene setup, obstacle generation,
  and treasure/boss content setup remain in Python.
- Risk of JSON too early: low for metadata, but high if progression and reward
  logic are moved before their schema is clear.
- Suggested schema shape:

```json
{
  "id": "curse",
  "display_name": "Curse",
  "title": "CURSE ROOM",
  "message": "High risk, double reward.",
  "color": [150, 70, 220],
  "spawn_multiplier": 1.65,
  "enemy_difficulty": 1.2
}
```

## Perk Definitions

- Safe to externalize now: partial.
- Stable data: key, name, description, legendary description, tags, synergy tag
  pairs.
- Still depends on Python logic: all perk effects are callables in
  `PerkSystem`; some effects are simple stat adds, while others perform caps,
  tradeoffs, healing, or custom mutations.
- Risk of JSON too early: data-only perk entries would not describe effects, so
  adding a perk would still require Python changes. Moving effects into JSON too
  early would require inventing a small effect DSL before the stat model is
  stable.
- Suggested schema shape:

```json
{
  "key": "rapid_fire",
  "name": "Fire Rate Boost",
  "desc": "+30% faster shooting",
  "legendary_desc": "+55% faster shooting",
  "tags": ["offense", "fire_rate"],
  "effect_id": "rapid_fire"
}
```

## Upgrade Definitions

- Safe to externalize now: partial.
- Stable data: shop role, option name, base cost, key, max levels, base costs.
- Still depends on Python logic: `UpgradeSystem.buy()` contains all purchase
  effects, skill equip behavior, max-level exceptions, healing messages, and
  cost scaling.
- Risk of JSON too early: externalizing options is easy, but externalizing
  effects before a stat/effect schema exists would duplicate logic or create an
  unsafe mini-language.
- Suggested schema shape:

```json
{
  "shops": {
    "blacksmith": [
      {"name": "Sharpen Blade", "base_cost": 30, "key": "damage"}
    ]
  },
  "max_levels": {
    "damage": 6
  },
  "base_costs": {
    "damage": 30
  }
}
```

## Definition Registry

- Safe to externalize now: no.
- Stable data: registry shape is useful as a central access point, with
  `require_*` lookup helpers and basic validation.
- Still depends on Python logic: current systems mostly import definition
  modules directly; validation only checks for empty keys; the registry does not
  yet own schema validation, duplicate ID checks, enum/string conversion, or
  migration from raw module imports.
- Risk of JSON too early: adding file loading now would bypass weak validation
  and scatter parsing concerns into gameplay code.
- Suggested schema direction: keep `DefinitionRegistry` as the single future
  loader/validator. Add explicit validators before any external file parsing.

## Recommended Next Engineering Step

Before JSON/YAML, route current systems through `DefinitionRegistry` in small
safe steps and strengthen validation:

1. Add duplicate ID and required-field validation for all definition categories.
2. Change one low-risk system at a time to use the registry.
3. Add headless checks that validate registry contents.
4. Only then consider read-only JSON/YAML loading for room and weapon metadata
   first.

The first externalization candidates should be room metadata and weapon numeric
data. Enemy, perk, and upgrade definitions need more Python-side schema work
before they are safe to move out of Python.
