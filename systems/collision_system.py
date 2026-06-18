class CollisionSystem:
    def __init__(self):
        self.static_colliders = []

    def clear(self):
        self.static_colliders.clear()

    def add_rect(self, rect):
        self.static_colliders.append(rect)

    def add_entity(self, entity):
        if hasattr(entity, "rect"):
            self.static_colliders.append(entity.rect)

    def add_entities(self, entities):
        for entity in entities:
            self.add_entity(entity)

    def get_colliders(self):
        return self.static_colliders
