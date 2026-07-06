from collections import deque
from contextlib import contextmanager
from time import perf_counter


class FrameProfiler:
    def __init__(self, enabled=False, history=90):
        self.enabled = enabled
        self.history = history
        self.samples = {}
        self.current = {}
        self.frame_index = 0
        self.frame_start = None
        self.spikes = deque(maxlen=12)

    def begin_frame(self):
        if not self.enabled:
            return
        self.current = {}
        self.frame_index += 1
        self.frame_start = perf_counter()

    def end_frame(self, state="-", enemies=0, projectiles=0, pickups=0, effects=0):
        if not self.enabled or self.frame_start is None:
            return
        frame_ms = (perf_counter() - self.frame_start) * 1000.0
        self.add("frame total", frame_ms)
        if frame_ms <= 25.0:
            return
        largest_name = "-"
        largest_ms = 0.0
        for name, value in self.current.items():
            if name == "frame total":
                continue
            if value > largest_ms:
                largest_name = name
                largest_ms = value
        self.spikes.append({
            "frame_ms": frame_ms,
            "largest_name": largest_name,
            "largest_ms": largest_ms,
            "state": state,
            "enemies": enemies,
            "projectiles": projectiles,
            "pickups": pickups,
            "effects": effects,
        })

    @contextmanager
    def section(self, name):
        if not self.enabled:
            yield
            return
        start = perf_counter()
        try:
            yield
        finally:
            self.add(name, (perf_counter() - start) * 1000.0)

    def add(self, name, milliseconds):
        if not self.enabled:
            return
        self.current[name] = self.current.get(name, 0.0) + milliseconds
        bucket = self.samples.setdefault(name, deque(maxlen=self.history))
        bucket.append(milliseconds)

    def lines(self, limit=12):
        if not self.enabled:
            return ["Profiler disabled"]
        rows = []
        for name, values in self.samples.items():
            if not values:
                continue
            latest = self.current.get(name, values[-1])
            avg = sum(values) / len(values)
            peak = max(values)
            ordered = sorted(values)
            p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
            rows.append((avg, f"{name}: {latest:.2f}ms avg {avg:.2f} p95 {p95:.2f} peak {peak:.2f}"))
        rows.sort(reverse=True, key=lambda item: item[0])
        if not rows:
            return ["Profiler warming up"]
        lines = [line for _avg, line in rows[:limit]]
        if self.spikes:
            spike = self.spikes[-1]
            lines.append(
                "Spike: "
                f"{spike['frame_ms']:.1f}ms {spike['largest_name']}={spike['largest_ms']:.1f}ms "
                f"{spike['state']} e{spike['enemies']} p{spike['projectiles']} "
                f"x{spike['pickups']} fx{spike['effects']}"
            )
        return lines
