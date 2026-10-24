import pygame

from settings import SCREEN_WIDTH

_MINIMAP_PANEL = None


def draw_minimap(surface, player, enemies, room_obstacles=None, stage=None):
    if not pygame.key.get_pressed()[pygame.K_TAB]:
        return
    if stage is not None and not stage.active:
        return
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
    _draw_stage_route(panel, stage, size)

    surface.blit(panel, (x, y))


def _draw_stage_route(panel, stage, size):
    if getattr(stage, "nodes", None):
        _draw_stage_graph(panel, stage, size)
        return
    font = pygame.font.Font(None, 18)
    small = pygame.font.Font(None, 16)
    title = small.render("STAGE ROUTE", True, (160, 205, 230))
    panel.blit(title, (10, 8))

    nodes = list(getattr(stage, "nodes", ()))
    if not nodes:
        rooms = list(getattr(stage, "rooms", ())) if stage else []
        nodes = [type("RouteNode", (), {"room": room, "cleared": False, "discovered": True, "grid_pos": None}) for room in rooms]

    nodes = sorted(nodes, key=lambda node: getattr(node.room, "index", 0))
    current_pos = getattr(stage, "current_pos", None)
    active = bool(getattr(stage, "active", False))

    start_x = 18
    y = 72
    gap = 16
    radius = 8
    for i, node in enumerate(nodes):
        x = start_x + i * gap
        room = node.room
        is_current = active and node.grid_pos == current_pos
        is_completed = bool(getattr(node, "cleared", False))
        is_boss = bool(getattr(room, "boss", False))
        discovered = bool(getattr(node, "discovered", True)) or is_completed or is_current

        if i > 0:
            prev_x = start_x + (i - 1) * gap
            line_col = (70, 120, 145) if discovered else (38, 48, 58)
            pygame.draw.line(panel, line_col, (prev_x + radius, y), (x - radius, y), 2)

        color = (45, 55, 68)
        if discovered:
            color = _room_color(room)
        if is_completed:
            color = (70, 185, 115)
        if is_boss:
            color = (245, 185, 55) if discovered else (72, 55, 25)

        if is_current:
            pygame.draw.circle(panel, (95, 225, 255), (x, y), radius + 5, 2)
        pygame.draw.circle(panel, color, (x, y), radius)
        pygame.draw.circle(panel, (8, 14, 20), (x, y), radius, 1)

        label = "B" if is_boss else str(getattr(room, "index", i + 1))
        text = font.render(label, True, (235, 240, 245))
        panel.blit(text, text.get_rect(center=(x, y)))

    legend_y = 104
    legend = (
        ("C", (75, 130, 190)),
        ("T", (220, 175, 70)),
        ("E", (210, 95, 185)),
        ("B", (245, 185, 55)),
    )
    lx = 16
    for label, color in legend:
        pygame.draw.circle(panel, color, (lx, legend_y), 5)
        txt = small.render(label, True, (185, 200, 210))
        panel.blit(txt, (lx + 8, legend_y - 6))
        lx += 32


def _room_color(room):
    if bool(getattr(room, "boss", False)):
        return (245, 185, 55)
    room_type = getattr(getattr(room, "room_type", None), "name", "")
    if room_type == "TREASURE":
        return (220, 175, 70)
    if room_type == "ELITE":
        return (210, 95, 185)
    return (75, 130, 190)


def _draw_stage_graph(panel, stage, size):
    font = pygame.font.Font(None, 18)
    panel.blit(font.render("STAGE MAP", True, (180, 220, 240)), (10, 8))
    nodes = [node for node in stage.nodes if node.discovered or node.cleared]
    if not nodes:
        return
    xs = [n.grid_pos[0] for n in nodes]
    ys = [n.grid_pos[1] for n in nodes]
    step = min(27, (size - 40) / max(1, max(xs) - min(xs)), (size - 64) / max(1, max(ys) - min(ys)))
    mid_x = (min(xs) + max(xs)) / 2
    mid_y = (min(ys) + max(ys)) / 2
    positions = {n.grid_pos: (round(size / 2 + (n.grid_pos[0] - mid_x) * step), round(79 + (n.grid_pos[1] - mid_y) * step)) for n in nodes}
    for node in nodes:
        for neighbor in node.neighbors.values():
            if neighbor in positions:
                pygame.draw.line(panel, (85, 130, 160), positions[node.grid_pos], positions[neighbor], 2)
    for node in nodes:
        center = positions[node.grid_pos]
        current = stage.active and node.grid_pos == stage.current_pos
        color = (70, 185, 115) if node.cleared else _room_color(node.room)
        if current:
            pygame.draw.circle(panel, (100, 235, 255), center, 12, 2)
        pygame.draw.circle(panel, color, center, 8)
        label = "B" if node.room.boss else "T" if node.room.room_type.name == "TREASURE" else str(node.room.index)
        text = font.render(label, True, (245, 245, 255))
        panel.blit(text, text.get_rect(center=center))
    panel.blit(font.render("You: cyan ring", True, (130, 200, 220)), (10, size - 19))
