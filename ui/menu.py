import pygame

from settings import SCREEN_WIDTH


def draw_menu(surface, game):
    surface.fill((32, 32, 32))

    title_rect = game.menu_title_surf.get_rect(center=(SCREEN_WIDTH // 2, 150))
    surface.blit(game.menu_title_surf, title_rect)

    hint_rect = game.menu_hint_surf.get_rect(center=(SCREEN_WIDTH // 2, 220))
    surface.blit(game.menu_hint_surf, hint_rect)

    pygame.draw.rect(surface, (50, 50, 50), game.rect_new_run, border_radius=8)
    pygame.draw.rect(surface, (0, 255, 0), game.rect_new_run, 2, border_radius=8)

    text_nr_rect = game.text_new_run.get_rect(center=game.rect_new_run.center)
    surface.blit(game.text_new_run, text_nr_rect)

    pygame.draw.rect(surface, (50, 50, 50), game.rect_quit, border_radius=8)
    pygame.draw.rect(surface, (255, 0, 0), game.rect_quit, 2, border_radius=8)

    text_q_rect = game.text_quit.get_rect(center=game.rect_quit.center)
    surface.blit(game.text_quit, text_q_rect)
