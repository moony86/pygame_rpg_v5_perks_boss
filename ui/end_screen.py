from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GREEN, DARK_GRAY
from ui.common import draw_text


def draw_end_screen(surface, big_font, font, title, subtitle):
    surface.fill(DARK_GRAY)

    draw_text(
        surface,
        big_font,
        title,
        SCREEN_WIDTH // 2,
        SCREEN_HEIGHT // 2 - 70,
        WHITE,
        center=True,
    )

    draw_text(
        surface,
        font,
        subtitle,
        SCREEN_WIDTH // 2,
        SCREEN_HEIGHT // 2 - 20,
        WHITE,
        center=True,
    )

    draw_text(
        surface,
        font,
        "Press Enter to Restart | Esc to Quit",
        SCREEN_WIDTH // 2,
        SCREEN_HEIGHT // 2 + 40,
        GREEN,
        center=True,
    )
