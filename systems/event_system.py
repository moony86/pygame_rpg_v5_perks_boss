class EventSystem:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_name, handler):
        if event_name not in self.listeners:
            self.listeners[event_name] = []

        self.listeners[event_name].append(handler)

    def emit(self, event_name, data=None):
        if data is None:
            data = {}

        handlers = self.listeners.get(event_name, [])

        for handler in handlers:
            handler(data)

    def clear(self):
        self.listeners.clear()