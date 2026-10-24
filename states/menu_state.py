from game_state import GameState
import pygame
from config import CONFIG, save_preferences
from ui.front_end import ACTIONS, OPTIONS


def handle_menu_events(game, event):
    def activate(action):
        game.audio.play('menu_select')
        if action == 'start':
            game.reset_run()
            game.state = GameState.HUB
        elif action == 'quit':
            game.quit()
        else:
            game.menu_page = action
            game.menu_focus = 0

    def save():
        game.audio.apply_volumes()
        game.music.apply_volume()
        game.menu_status = 'Settings saved.' if save_preferences() else 'Applied, but settings could not be saved.'

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            game.menu_page = 'main'
            game.menu_focus = 0
        elif event.key in (pygame.K_UP,pygame.K_DOWN,pygame.K_TAB):
            count = len(OPTIONS) if game.menu_page=='settings' else len(ACTIONS)
            game.menu_focus = (game.menu_focus + (-1 if event.key==pygame.K_UP else 1)) % count
        elif game.menu_page=='main' and event.key in (pygame.K_RETURN,pygame.K_SPACE):
            activate(ACTIONS[game.menu_focus])
        elif game.menu_page=='settings' and event.key in (pygame.K_LEFT,pygame.K_RIGHT,pygame.K_RETURN,pygame.K_SPACE):
            key=OPTIONS[game.menu_focus]
            if key.endswith('_volume'):
                if event.key in (pygame.K_LEFT,pygame.K_RIGHT):
                    CONFIG[key]=max(0.,min(1.,round(CONFIG[key]+(-.05 if event.key==pygame.K_LEFT else .05),2)))
            else:
                CONFIG[key]=not CONFIG[key]
            save()
        return
    click = event.type==pygame.MOUSEBUTTONDOWN and event.button==1
    dragging = event.type==pygame.MOUSEMOTION and event.buttons[0]
    if event.type==pygame.MOUSEBUTTONUP and event.button==1 and game.menu_page=='settings':
        save()
    if not (click or dragging):
        return
    if game.menu_page=='main' and click:
        for index,key in enumerate(ACTIONS):
            if game.menu_buttons[key].collidepoint(event.pos):
                game.menu_focus=index
                activate(key)
                return
    elif game.menu_page in ('settings','controls'):
        if click and game.menu_back.collidepoint(event.pos):
            game.menu_page='main'
            game.menu_focus=0
            return
        if game.menu_page=='settings':
            for index,key in enumerate(OPTIONS):
                rect=game.menu_option_rects[key]
                if rect.collidepoint(event.pos):
                    game.menu_focus=index
                    if key.endswith('_volume'):
                        if event.pos[0] >= rect.x+260:
                            CONFIG[key]=max(0.,min(1.,(event.pos[0]-rect.x-280)/200))
                            game.audio.apply_volumes()
                            game.music.apply_volume()
                    elif click:
                        CONFIG[key]=not CONFIG[key]
                        save()
