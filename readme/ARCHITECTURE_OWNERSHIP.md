# Architecture Ownership

This document defines internal ownership boundaries for the project. It is a
developer contract for future refactors. It does not describe player-facing
design, visuals, balance, or game feel.

## Core Rule

Each system should have one primary responsibility. A system may collaborate
with others, but it should not directly own unrelated rules, rendering, state
transitions, rewards, audio, or input unless those are its explicit domain.

## Game

- Current responsibility: creates the Pygame application, owns the main loop,
  composes systems, stores active world lists, routes update/draw work, handles
  some combat actions, handles some scene transitions, handles viewport scaling,
  emits audio events, and draws some world/UI elements directly.
- Should own: application lifetime, top-level system composition, main loop
  timing, high-level state delegation, window/viewport presentation.
- Must not own: enemy attack pattern resolution, melee hit rules, room content
  construction, spawn safety algorithms, UI drawing details, combat rewards,
  enemy crowding policy, weapon behavior.
- Current violations: `Game.update()` interprets enemy action dictionaries,
  calls projectile and melee systems, updates room/wave/spawn behavior, resolves
  enemy crowding, handles boss outcomes, and opens perk selection. `Game.draw()`
  contains world, HUD, portal, hint, dialogue, minimap, and dev panel drawing
  decisions.
- Future target: `Game` becomes a composition root and thin loop. Runtime
  behavior moves into focused controllers/resolvers while `Game` keeps only
  orchestration and presentation handoff.

## Player

- Current responsibility: owns player state, progression fields, perk/upgrade
  mutation targets, movement, direct keyboard polling, weapon switching, active
  skill timers, damage/healing, aiming, sprite loading, and rendering.
- Should own: player state, health/resources/progression data, current weapon
  reference, cooldown/timer state, movement state after input intent is provided.
- Must not own: direct keyboard polling, global input mapping, combat hit
  resolution, enemy damage, rewards, scene state, global audio, room state.
- Current violations: `Player.handle_movement_input()` polls Pygame keys
  directly; player rendering and sprite asset management live inside the entity;
  active skill intent and some skill effects are split between `Player` and
  `Game`.
- Future target: player receives movement/weapon/skill intents from
  `InputSystem`; player exposes state and attack requests but does not know
  about game-wide systems.

## Enemy

- Current responsibility: owns enemy type enum, stat construction, AI behavior,
  boss phase state, attack request creation, movement, damage state, animation
  state, sprite loading, drawing, health bars, and windup indicators.
- Should own: per-enemy runtime state, position, health, current behavior state,
  and production of behavior intents.
- Must not own: full enemy catalog metadata, wave threat costs, spawn pools,
  projectile construction, global effects/audio, reward rules, UI rendering
  policy beyond temporary legacy drawing.
- Current violations: one class branches on every enemy type for stats,
  behavior, attack intent, drawing, boss display, and animation. Enemy metadata
  is duplicated in wave/spawn systems.
- Future target: introduce enemy definition data first, then gradually separate
  behavior and rendering behind stable interfaces.

## CombatSystem

- Current responsibility: projectile-vs-enemy collision, enemy bullet damage,
  contact damage, boss shield handling, boss anti-kite pressure, elite guard
  spawn trigger, rewards, loot reward rules, knockback, effects, and audio calls.
- Should own: damage resolution, hit detection outcomes, contact damage, death
  detection, and combat result reporting.
- Must not own: enemy spawning policy, boss encounter scripting, reward economy
  constants beyond combat result calculation, audio playback policy, visual
  effects policy, room progression.
- Current violations: spawns an elite guard during boss combat, directly awards
  XP/gold, triggers effects/audio, and contains boss-specific phase/shield rules.
- Future target: return combat results/events. Keep hit resolution here, move
  reward application, boss scripting, and side effects behind separate handlers.

## Weapon System

- Current responsibility: defines `Weapon`, `PistolWeapon`, and `KnifeWeapon`.
  Weapons return simple attack dictionaries.
- Should own: weapon identity, cooldown, and attack intent description.
- Must not own: damage application, enemy mutation, XP/gold rewards, global
  audio, room/game state, projectile list mutation.
- Current violations: `KnifeWeapon` encodes melee numeric details directly and
  reads player state to build the attack request. This is acceptable as a
  temporary foundation but should become a clearer attack request contract.
- Future target: weapon classes return typed attack requests. Adding a weapon
  should not require editing `Player` or `Game` beyond registration.

## ShootingSystem

- Current responsibility: gun cooldown, projectile damage calculation, crit
  calculation, spread, projectile creation, player gun animation trigger, and
  optional audio playback.
- Should own: projectile attack execution from a shooting request, projectile
  cooldown, projectile creation rules.
- Must not own: global audio policy, player rendering/animation, reward rules,
  enemy hit resolution, room/game state.
- Current violations: triggers player gun animation and optionally plays audio.
  It reads many raw player stat fields directly.
- Future target: consume a weapon/projectile request and player stat snapshot,
  then append projectiles or return created projectiles. Side effects should be
  emitted as events/results.

## RoomSystem

- Current responsibility: chooses normal room type, tracks room timer/banner
  timer, reward multiplier, target kills, survival time, and room metadata.
- Should own: room type selection, room metadata, room-local timers, room clear
  criteria as pure state/rule checks.
- Must not own: enemy spawning, scene transitions, player movement, audio,
  effects, portal placement, boss entry.
- Current violations: stores some spawn/difficulty metadata that is not fully
  authoritative because wave/spawn systems duplicate room-specific behavior.
- Future target: become the source of room rules and expose those rules to
  scene/wave/spawn systems without performing their work.

## WaveSystem

- Current responsibility: builds wave plans, threat budgets, enemy pools,
  survival wave configuration, wave state machine, spawn timing, active limits,
  wave messages, and enemy construction fallback.
- Should own: wave planning and wave runtime progression.
- Must not own: safe spawn position algorithms, direct enemy construction when
  a factory is available, UI display policy, room selection, player rewards.
- Current violations: combines pure planning with runtime spawning and
  user-facing message text; contains enemy metadata and pool rules that overlap
  with enemy/spawn ownership.
- Future target: split internally into plan builder and runtime state machine.
  Keep wave messages as data results until a UI/message layer consumes them.

## SpawnSystem

- Current responsibility: tracks spawn timers/room info, can choose enemy type,
  can create enemies, and provides safe spawn positions around the camera/player.
- Should own: safe spawn position selection only.
- Must not own: room progression, spawn cadence, enemy type selection, enemy
  construction, wave composition, difficulty rules.
- Current violations: `update()` is a legacy spawn cadence path that overlaps
  with `WaveSystem`; `_choose_type()` duplicates enemy pool logic.
- Future target: retire runtime spawning from this system. Expose a small API
  for safe positions that wave/scene code can call.

## SceneSystem

- Current responsibility: transitions between hub, room, and boss; resets world
  lists; builds NPCs; configures collision; starts room/wave/spawn state; creates
  treasure enemies and boss enemy; emits scene audio events.
- Should own: scene transitions and scene setup/teardown.
- Must not own: enemy behavior, combat rules, reward rules, weapon rules,
  low-level spawn safety, UI drawing, balance tuning.
- Current violations: constructs treasure/boss enemies directly, sets messages,
  emits audio events, and coordinates several systems through the full `game`
  object.
- Future target: remain the transition coordinator but delegate content creation
  to factories/rules and communicate side effects through events/results.

## InputSystem

- Current responsibility: reads Pygame events, handles quit/resize, delegates
  state-specific handlers, lets dev panel intercept events, and calls scene
  transition handlers indirectly through state modules.
- Should own: translating raw input events into game commands or state handler
  calls.
- Must not own: gameplay rules, room/boss progression, direct combat resolution,
  rendering, audio, rewards.
- Current violations: state handlers called by input perform scene transitions;
  continuous movement input is still polled directly by `Player`.
- Future target: all input, including movement/weapon/skill commands, is
  translated outside entities and passed into runtime systems as intents.

## EffectsSystem

- Current responsibility: manages floating text and ring effects, updates and
  draws them.
- Should own: short-lived visual effect objects and their lifecycle.
- Must not own: combat decisions, rewards, audio, game state, room progression.
- Current violations: mostly clean. The main coupling is that gameplay systems
  call it directly instead of emitting effect requests.
- Future target: consume effect requests/events so combat and scene systems do
  not need direct references for every visual side effect.

## AudioSystem

- Current responsibility: initializes mixer, resolves bundled resource paths,
  loads sounds, plays one-shot sounds, plays/stops music, applies volumes.
- Should own: loading and playback of audio assets.
- Must not own: decisions about when gameplay events happen, combat logic, room
  logic, UI state, enemy/player state.
- Current violations: mostly clean. Some systems still call audio directly,
  while others use events.
- Future target: audio subscribes to domain events or receives explicit audio
  requests from a single mediator.

## DevTools

- Current responsibility: `DevPanel` draws a developer overlay, handles dev
  input, mutates player speed and weapon positioning globals, changes scenes,
  spawns/clears/kills enemies, triggers shots, and grants health/gold/XP.
- Should own: developer-only commands and inspection controls.
- Must not own: production gameplay logic, hidden permanent tuning changes,
  module-level global mutation without explicit command boundaries.
- Current violations: directly mutates `entities.player` module constants and
  game state. It imports scene functions and enemy types directly.
- Future target: route all dev actions through explicit `DevCommands` methods so
  debug tooling does not bypass ownership boundaries.

## UI Modules

- Current responsibility: draw menu, pause, perk screen, HUD, shop hints, end
  screen, room banner, minimap, common drawing helpers, and dev panel.
- Should own: rendering of UI surfaces from supplied state/data.
- Must not own: gameplay state mutation, combat rules, spawning, progression,
  audio playback, room selection.
- Current violations: most UI modules are draw-only, but `ui.dev_panel` is both
  UI and command execution. `systems.ui` is a legacy duplicate helper candidate.
- Future target: normal UI remains pure rendering; developer UI delegates to
  dev commands; shared helpers live under `ui.common`.
