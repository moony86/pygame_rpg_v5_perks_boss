# systems/collision_system.py
from collections import defaultdict
import pygame

class CollisionSystem:
    """نظام تصادم ذكي يعتمد على شبكة الخلايا لتقليل عمليات فحص التصادم من O(N^2) إلى O(1)"""
    def __init__(self, cell_size=128):
        self.cell_size = cell_size
        self.grid = defaultdict(list)
        self.static_colliders = []

    def clear(self):
        self.static_colliders.clear()
        self.grid.clear()

    def _get_cells_for_rect(self, rect):
        """تحديد المربعات (الخلايا) التي يغطيها هذا المجسم"""
        start_x = rect.left // self.cell_size
        end_x = rect.right // self.cell_size
        start_y = rect.top // self.cell_size
        end_y = rect.bottom // self.cell_size

        for cx in range(start_x, end_x + 1):
            for cy in range(start_y, end_y + 1):
                yield (cx, cy)

    def add_rect(self, rect):
        self.static_colliders.append(rect)
        # تصنيف العقبة داخل الخلايا التي تقطعها
        for cell in self._get_cells_for_rect(rect):
            self.grid[cell].append(rect)

    def add_entity(self, entity):
        if hasattr(entity, "rect"):
            self.add_rect(entity.rect)

    def add_entities(self, entities):
        for entity in entities:
            self.add_entity(entity)

    def get_colliders(self):
        return self.static_colliders

    def get_nearby_colliders(self, rect):
        """إرجاع العقبات القريبة فقط من الكائن المحدد لتجنب فحص باقي الغرفة"""
        nearby = []
        for cell in self._get_cells_for_rect(rect):
            if cell in self.grid:
                for collider in self.grid[cell]:
                    if collider not in nearby:
                        nearby.append(collider)
        return (nearby)
