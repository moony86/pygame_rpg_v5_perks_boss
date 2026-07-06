import pygame

from settings import MAP_SIZE, SCREEN_WIDTH

_MINIMAP_PANEL = None


def draw_minimap(surface, player, enemies, room_obstacles=None, stage=None):
    global _MINIMAP_PANEL
    size = 150
    margin = 14
    x = SCREEN_WIDTH - size - margin
    y = margin + 280
    if _MINIMAP_PANEL is None:
        _MINIMAP_PANEL = pygame.Surface((size, size), pygame.SRCALPHA)
        _MINIMAP_PANEL.fill((4, 8, 12, 95))
        pygame.draw.rect(_MINIMAP_PANEL, (90, 130, 160, 120), (0, 0, size, size), 1, border_radius=4)
    panel = _MINIMAP_PANEL.copy()
    if getattr(stage, "active", False) and getattr(stage, "nodes", None):
        _draw_stage_map(panel, stage, size)
        surface.blit(panel, (x, y))
        return

    def map_pos(world_pos):
        return (
            int(max(0, min(size - 1, world_pos[0] / MAP_SIZE * size))),
            int(max(0, min(size - 1, world_pos[1] / MAP_SIZE * size))),
        )

    if room_obstacles:
        for rect in room_obstacles:
            rx = int(rect.x / MAP_SIZE * size)
            ry = int(rect.y / MAP_SIZE * size)
            rw = max(1, int(rect.width / MAP_SIZE * size))
            rh = max(1, int(rect.height / MAP_SIZE * size))
            pygame.draw.rect(panel, (150, 160, 170, 70), (rx, ry, rw, rh))

    px, py = map_pos(player.rect.center)
    pygame.draw.circle(panel, (70, 210, 255, 230), (px, py), 4)

    for enemy in enemies:
        if not enemy.alive:
            continue
        ex, ey = map_pos(enemy.rect.center)
        color = (255, 70, 70, 210)
        type_name = getattr(getattr(enemy, "type", None), "name", "")
        if type_name == "BOSS":
            color = (255, 210, 60, 240)
        elif type_name == "ELITE":
            color = (255, 80, 200, 230)
        pygame.draw.circle(panel, color, (ex, ey), 2)

    surface.blit(panel, (x, y))


def _draw_stage_map(panel, stage, size):
    nodes = list(stage.nodes)
    xs = [node.grid_pos[0] for node in nodes]
    ys = [node.grid_pos[1] for node in nodes]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(1, max_x - min_x)
    span_y = max(1, max_y - min_y)
    margin = 18

    def node_pos(node):
        nx = (node.grid_pos[0] - min_x) / span_x
        ny = (node.grid_pos[1] - min_y) / span_y
        return (
            round(margin + nx * (size - margin * 2)),
            round(margin + ny * (size - margin * 2)),
        )

    for node in nodes:
        if not node.discovered:
            continue
        start = node_pos(node)
        for target_pos in node.neighbors.values():
            target = stage.node_by_pos[target_pos]
            if not target.discovered:
                continue
            pygame.draw.line(panel, (80, 100, 120, 150), start, node_pos(target), 2)

    for node in nodes:
        pos = node_pos(node)
        if not node.discovered:
            pygame.draw.circle(panel, (25, 30, 38, 180), pos, 7)
            continue
        color = (75, 120, 165, 230)
        if node.cleared:
            color = (80, 190, 120, 235)
        if node.room.boss:
            color = (235, 180, 60, 245) if node.discovered else (35, 30, 20, 160)
        if node.grid_pos == stage.current_pos:
            pygame.draw.circle(panel, (90, 220, 255, 240), pos, 10, 2)
        pygame.draw.circle(panel, color, pos, 6)
