import pygame
from settings import WHITE, BLACK


def wrap_text(font, text, max_width):
    lines = []
    for paragraph in str(text).splitlines() or [""]:
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}".strip()
            if current and font.size(candidate)[0] > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    return lines


def fitted_text(font, text, color, max_width):
    rendered = font.render(text, True, color)
    if rendered.get_width() > max_width:
        scale = max_width / rendered.get_width()
        rendered = pygame.transform.smoothscale(rendered, (max_width, max(1, round(rendered.get_height() * scale))))
    return rendered


def draw_text(surface, font, text, x, y, color=WHITE, center=False):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()

    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    surface.blit(rendered, rect)


def draw_bar(surface, x, y, w, h, ratio, fg, bg=(70, 70, 70)):
    ratio = max(0, min(1, ratio))

    pygame.draw.rect(surface, bg, (x, y, w, h), border_radius=4)
    pygame.draw.rect(surface, fg, (x, y, int(w * ratio), h), border_radius=4)
    pygame.draw.rect(surface, BLACK, (x, y, w, h), 2, border_radius=4)
