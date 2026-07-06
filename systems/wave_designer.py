import json
from collections import Counter
from pathlib import Path

from settings import DEV_TOOLS_ENABLED
from systems.definition_registry import definition_registry


WAVE_REPORT_SCHEMA = "bluecube.wave_report.v1"
DEFAULT_EXPORT_PATH = Path("wave_report.json")


class WaveDesigner:
    def __init__(self, game):
        self.game = game
        self.visible = False
        self.spawn_history = []
        self._known_enemy_ids = set()
        self.message = "Wave designer ready"

    def toggle(self):
        if not DEV_TOOLS_ENABLED:
            return
        self.visible = not self.visible
        self.message = f"wave designer {'on' if self.visible else 'off'}"

    def update(self):
        if not DEV_TOOLS_ENABLED or not self.visible:
            return
        for enemy in getattr(self.game, "enemies", []):
            enemy_id = id(enemy)
            if enemy_id in self._known_enemy_ids:
                continue
            self._known_enemy_ids.add(enemy_id)
            enemy_type = getattr(enemy, "type", None)
            if getattr(enemy, "dev_lab_enemy", False):
                source = "enemy_lab"
            elif self.game.state.name == "ROOM":
                source = "wave_runtime"
            else:
                source = self.game.state.name.lower()
            self.spawn_history.append({
                "enemy_type": enemy_type.name if enemy_type else "-",
                "source": source,
                "room": self.game.room_number,
                "wave_index": getattr(self.game.waves, "current_wave_index", 0),
            })
            self.spawn_history = self.spawn_history[-120:]

    def snapshot(self):
        waves = self.game.waves
        wave = self.current_wave()
        composition = self.enemy_composition(wave)
        current_wave_number = waves.current_wave_number() if hasattr(waves, "current_wave_number") else 0
        active_limit = self.active_limit(wave)
        return {
            "schema": WAVE_REPORT_SCHEMA,
            "current_room": self.game.room_number,
            "current_room_type": getattr(getattr(self.game.rooms, "room_type", None), "name", None),
            "wave": {
                "current_wave": current_wave_number,
                "wave_index": getattr(waves, "current_wave_index", 0),
                "total_waves": len(getattr(waves, "waves", [])),
                "wave_state": getattr(waves, "wave_state", "-"),
                "wave_budget": self._wave_value(wave, "threat_budget"),
                "remaining_budget": self._wave_value(wave, "threat_remaining"),
                "threat_budget": self._wave_value(wave, "threat_budget"),
                "enemies_alive": len(getattr(self.game, "enemies", [])),
                "active_limit": active_limit,
                "spawn_interval": getattr(waves, "spawn_delay", None),
                "spawn_delay": self._wave_value(wave, "delay"),
                "spawn_timer": getattr(waves, "spawn_timer", None),
                "break_timer": getattr(waves, "wave_timer", None) if getattr(waves, "wave_state", "") in ("break", "incoming") else 0.0,
                "enemies_left_to_spawn": getattr(waves, "enemies_left_to_spawn", 0),
                "spawn_burst_size": getattr(waves, "spawn_burst_size", 0),
                "label": self._wave_value(wave, "label"),
                "flavour": self._wave_value(wave, "flavour"),
            },
            "enemy_composition": composition,
            "remaining_spawn_queue": self.remaining_spawn_queue(wave),
            "timeline": self.timeline(),
            "spawn_history": list(self.spawn_history),
        }

    def current_wave(self):
        waves = getattr(self.game.waves, "waves", [])
        index = getattr(self.game.waves, "current_wave_index", 0)
        if 0 <= index < len(waves):
            return waves[index]
        return None

    def active_limit(self, wave):
        if wave is None:
            return None
        waves = self.game.waves
        if hasattr(waves, "_current_active_limit"):
            return waves._current_active_limit(wave)
        return wave.get("active_limit")

    def enemy_composition(self, wave):
        if wave is None:
            return []
        alive_count = Counter(
            getattr(enemy, "type", None)
            for enemy in getattr(self.game, "enemies", [])
            if getattr(enemy, "alive", True)
        )
        queue_count = Counter(wave.get("spawn_queue", []))
        rows = []
        enemy_types = set(wave.get("types", [])) | set(alive_count) | set(queue_count)
        enemy_types = {enemy_type for enemy_type in enemy_types if enemy_type is not None}
        for enemy_type in sorted(enemy_types, key=lambda item: item.name):
            definition = definition_registry.enemies.get(enemy_type)
            current_count = alive_count.get(enemy_type, 0)
            remaining_count = queue_count.get(enemy_type, 0)
            rows.append({
                "enemy_type": enemy_type.name,
                "display_name": definition.display_name if definition else enemy_type.name,
                "current_count": current_count,
                "remaining_count": remaining_count,
                "threat_cost": definition.threat_cost if definition else None,
            })
        return rows

    def remaining_spawn_queue(self, wave):
        if wave is None:
            return []
        return [enemy_type.name for enemy_type in wave.get("spawn_queue", [])]

    def timeline(self):
        waves = getattr(self.game.waves, "waves", [])
        timeline = []
        for index, wave in enumerate(waves):
            timeline.append({
                "type": "spawn",
                "wave_index": index,
                "label": wave.get("label", f"Wave {index + 1}"),
                "count": wave.get("count", 0),
                "delay": wave.get("delay"),
            })
            if index < len(waves) - 1:
                timeline.append({
                    "type": "break",
                    "wave_index": index,
                    "label": "Break",
                })
        timeline.append({"type": "complete", "wave_index": len(waves), "label": "Complete"})
        return timeline

    def lines(self):
        data = self.snapshot()
        wave = data["wave"]
        return [
            f"Current Room: {data['current_room']}",
            f"Room Type: {data['current_room_type']}",
            f"Current Wave: {wave['current_wave']} / {wave['total_waves']}",
            f"Wave Index: {wave['wave_index']}",
            f"Wave State: {wave['wave_state']}",
            f"Wave Budget: {wave['wave_budget']}",
            f"Remaining Budget: {wave['remaining_budget']}",
            f"Enemies Alive: {wave['enemies_alive']}",
            f"Active Limit: {wave['active_limit']}",
            f"Spawn Interval: {wave['spawn_interval']}",
            f"Spawn Delay: {wave['spawn_delay']}",
            f"Spawn Timer: {wave['spawn_timer']}",
            f"Break Timer: {wave['break_timer']}",
            f"Threat Budget: {wave['threat_budget']}",
        ]

    def export(self, path=DEFAULT_EXPORT_PATH):
        export_path = Path(path)
        export_path.write_text(json.dumps(self.snapshot(), indent=2), encoding="utf-8")
        self.message = f"exported {export_path}"
        return export_path

    def _wave_value(self, wave, key):
        if wave is None:
            return None
        return wave.get(key)
