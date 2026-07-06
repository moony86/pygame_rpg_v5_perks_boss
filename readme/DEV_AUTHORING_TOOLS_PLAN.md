# BlueCube Developer Authoring Tools Plan

This plan keeps BlueCube developer tooling incremental. Do not build a full
editor until the runtime dev overlay has stayed stable through normal
development use.

## Phase 1: Runtime Dev Overlay

Status: implemented.

Scope:

- F12 developer overlay.
- Runtime info display.
- Debug toggles.
- Safe debug drawing.
- Explicit dev commands.
- Release guard through `DEV_TOOLS_ENABLED`.

Out of scope:

- Layout editing.
- JSON export/import.
- Wave authoring.
- Boss scripting tools.

## Phase 2: Room Layout Authoring

Scope:

- Show obstacles, spawn zones, and portals.
- Select and move rectangles only while dev mode is enabled.
- Export room layout JSON.
- Keep exported layouts inactive unless explicitly loaded.

Safety rules:

- No gameplay layout changes by default.
- No automatic loading in production.
- No balance changes hidden inside the editor.

## Phase 3: Enemy Test Lab

Scope:

- Select enemy type.
- Spawn one enemy near player.
- Show HP, speed, behavior type, draw profile, and threat cost.
- Test one enemy at a time.

Safety rules:

- No permanent enemy definition edits.
- No mass spawning beyond explicit dev commands.

## Phase 4: Wave Designer

Scope:

- Inspect current wave plan.
- Export/import wave presets.
- Display wave budget, composition, active limit, state, and spawn queue.

Safety rules:

- No balance changes without explicit confirmation.
- Imported presets should be dev-only until promoted intentionally.

## Phase 5: Boss Test Lab

Scope:

- Jump to boss.
- Force boss phase.
- Show cooldowns, selected action, phase state, shield, and summon state.

Safety rules:

- Boss behavior remains code-owned until a separate boss definition phase.
- Forced phases are debug-only and must not leak into normal run flow.
