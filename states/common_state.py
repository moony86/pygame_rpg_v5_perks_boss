from game_state import GameState


def handle_escape_key(game):
    if game.state in (
        GameState.ROOM,
        GameState.BOSS,
        GameState.HUB,
    ):
        game.previous_state = game.state
        game.state = GameState.PAUSED

    elif game.state == GameState.PAUSED:
        game.state = game.previous_state

    else:
        game.quit()
