"""Offline frozen-resource validation, explicitly separate from human playtests."""
import json
from pathlib import Path


def run(report):
    import pygame
    from game import Game
    from systems.hub_presentation import HUB, art, background
    from systems.scene_system import enter_hub
    from ui.hub import draw
    from systems.object_catalog import sprite
    from definitions.perk_definitions import PERK_DEFINITIONS
    game = Game()
    game.draw()
    assert background((1920, 1080)) is not None, 'Missing hub background'
    for role in HUB['npcs']:
        if role != 'portal':
            assert art(role) is not None, role
    for card in PERK_DEFINITIONS:
        assert sprite('card_' + card['key']) is not None, card['key']
    for key in ('boss_turret','fx_speed_wake'):
        assert sprite(key) is not None, key
    from systems.class_audio import CUES
    from systems.class_appearance import SKINS
    for key in SKINS.values():
        assert sprite(key) is not None, key
    for values in CUES.values():
        for cue in (values['shoot'], values['impact']):
            assert (game.audio.sounds_path / (cue + '.wav')).is_file(), cue
            if game.audio.enabled:
                assert cue in game.audio.sounds, cue
    from systems.stage_progression import TUNING
    assert TUNING['max_difficulty']>=1
    enter_hub(game)
    game.draw()
    for npc in game.npcs:
        game.player.rect.center = (npc.rect.centerx, npc.rect.bottom + 35)
        game.dialogue.show(npc.name, 'Interaction smoke check')
        draw(game.screen, game)
    game.stage.start_stage()
    for _ in range(10):
        game.run_frame(1/60)
    game.reset_run()
    Path(report).write_text(json.dumps({'ok': True, 'frozen_resources': True,
                                      'checks': ['menu', 'hub_art', 'all_card_art', 'all_npc_panels', 'siege_and_speed_art', 'class_skins', 'class_audio', 'progression_config', 'combat_frames', 'reset']}, indent=2), encoding='utf-8')
    pygame.quit()
