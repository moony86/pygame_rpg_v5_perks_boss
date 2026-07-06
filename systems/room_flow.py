from systems.room_system import RoomType


ROOM_START_COUNTDOWN = 3.0


class RoomFlowSystem:
    def __init__(self):
        self.countdown_timer = 0.0
        self.countdown_active = False
        self.room_clear_time = None
        self.run_time = 0.0

    def reset_run(self):
        self.countdown_timer = 0.0
        self.countdown_active = False
        self.room_clear_time = None
        self.run_time = 0.0

    def clear_scene(self):
        self.countdown_timer = 0.0
        self.countdown_active = False
        self.room_clear_time = None

    def start_for_room(self, room_type):
        self.room_clear_time = None
        self.countdown_active = room_type in (RoomType.COMBAT, RoomType.CURSE, RoomType.SURVIVAL, RoomType.ELITE)
        self.countdown_timer = ROOM_START_COUNTDOWN if self.countdown_active else 0.0

    def update_run_timer(self, dt):
        self.run_time += dt

    def update_countdown(self, dt):
        if not self.countdown_active:
            return False
        self.countdown_timer = max(0.0, self.countdown_timer - dt)
        if self.countdown_timer <= 0:
            self.countdown_active = False
            return True
        return False

    def advance_countdown(self, dt):
        if not self.countdown_active:
            return dt, False

        remaining_before = self.countdown_timer
        self.countdown_timer = max(0.0, self.countdown_timer - dt)
        if self.countdown_timer > 0:
            return 0.0, False

        self.countdown_active = False
        return max(0.0, dt - remaining_before), True

    def room_can_advance(self):
        return not self.countdown_active

    def countdown_label(self):
        if not self.countdown_active:
            return ""
        if self.countdown_timer <= 0:
            return "GO"
        return str(max(1, int(self.countdown_timer + 0.999)))

    def mark_room_clear(self, room_time):
        self.room_clear_time = room_time
        return self.room_clear_time
