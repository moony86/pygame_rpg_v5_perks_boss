import pygame


def handle_perk_select_events(game, event):
    if game.perk_input_lock > 0:
        return

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        choose_perk_by_mouse(game, event.pos)

    elif event.type == pygame.KEYDOWN:
        if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
            index = int(event.unicode) - 1
            choose_perk(game, index)


def choose_perk_by_mouse(game, mouse_pos):
    for index, rect in enumerate(game.perk_card_rects):
        if rect.collidepoint(mouse_pos):
            choose_perk(game, index)
            break


def choose_perk(game, index):
    perk = game.perks.apply(game.player, index)

    if not perk:
        return

    game.player.consume_pending_level_up()
    game.message = f"Perk: {perk['name']}"
    game.events.emit("menu_select")

    game.player.invulnerable_timer = max(
        game.player.invulnerable_timer,
        0.5,
    )

    game.effects.ring(
        game.player.rect.center,
        radius=130,
        life=0.55,
    )

    game.state = game.previous_state
    game.open_perk_select_if_needed()
