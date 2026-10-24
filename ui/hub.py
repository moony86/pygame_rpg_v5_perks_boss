"""Scene labels and contextual interaction panel, not a second HUD dashboard."""
import pygame
from systems.hub_presentation import HUB, art
from systems.world_utils import nearest_npc
from systems.upgrade_system import UPGRADES
from ui.common import fitted_text

INK = (11, 20, 30)
TEXT = (224, 237, 243)
MUTED = (156, 182, 193)


def shop_rows(game, role):
    return [pygame.Rect(1190, 330 + i * 72, 610, 64)
            for i in range(len(UPGRADES.get(role, ())))]


def buy(game, npc, index):
    before = game.player.gold
    game.message = game.upgrades.buy(game.player, npc.role, index)
    game.dialogue.show(npc.name, game.message)
    if game.player.gold < before:
        game.events.emit('npc_purchase')


def handle_click(game, event):
    npc = nearest_npc(game.player, game.npcs)
    if not npc or not game.dialogue.active or game.dialogue.current_speaker != npc.name:
        return False
    for i, rect in enumerate(shop_rows(game, npc.role)):
        if rect.collidepoint(event.pos):
            buy(game, npc, i)
            return True
    return False


def draw(surface, game):
    font = game.font
    if getattr(game.player, 'tea_state', None) == 'holding':
        label = font.render('[T] Drink tea — a quiet break before the trial', True, TEXT)
        surface.blit(label, label.get_rect(midbottom=(surface.get_width()//2, 960)))
    selected = nearest_npc(game.player, game.npcs)
    for npc in game.npcs:
        config = HUB['npcs'].get(npc.role)
        if not config:
            continue
        pos = game.camera.apply_rect(npc.rect).midbottom
        title = font.render(config['label'], True, config['color'] if npc is selected else MUTED)
        rect = title.get_rect(midtop=(pos[0], pos[1] + 18))
        pygame.draw.rect(surface, INK, rect.inflate(18, 8), border_radius=5)
        surface.blit(title, rect)
        if npc is selected:
            label = '[E] ' + ('Enter challenge' if game.gatekeeper_ready else config['action'])
            rendered = font.render(label, True, TEXT)
            target = rendered.get_rect(midbottom=(pos[0], pos[1] - 124))
            pygame.draw.rect(surface, INK, target.inflate(22, 12), border_radius=6)
            surface.blit(rendered, target)
    if not selected or not game.dialogue.active or game.dialogue.current_speaker != selected.name:
        return
    options = UPGRADES.get(selected.role, ())
    if not options:
        return
    config = HUB['npcs'][selected.role]
    panel = pygame.Rect(1160, 190, 670, 180 + len(options) * 72)
    pygame.draw.rect(surface, INK, panel, border_radius=12)
    pygame.draw.line(surface, config['color'], (1185, 208), (1800, 208), 3)
    portrait = art(selected.role)
    if portrait:
        surface.blit(portrait, (1180, 218))
    surface.blit(game.big_font.render(config['label'], True, config['color']), (1340, 228))
    surface.blit(font.render(f'Gold {game.player.gold}  /  Click or keys 1-{len(options)}', True, MUTED), (1340, 286))
    for i, ((name, base, key), rect) in enumerate(zip(options, shop_rows(game, selected.role))):
        level = game.upgrades.get_level(key)
        maxed = key != 'heal' and not key.startswith('skill_') and level >= game.upgrades.get_max_level(key)
        cost = game.upgrades.get_cost(key, base)
        affordable = game.player.gold >= cost and not maxed
        pygame.draw.rect(surface, (27, 43, 53), rect, border_radius=7)
        icon = 'card_' + key
        from systems.object_catalog import sprite, catalog
        if key == 'heal':
            icon = 'heal_potion'
        elif icon not in catalog()['objects']:
            icon = 'shot_charge' if 'shot_charge' in catalog()['objects'] and key.startswith('skill_') else 'pistol'
        image = sprite(icon, (40, 40))
        if image:
            surface.blit(image, (rect.x + 12, rect.y + 12))
        display_name = {'power_rounds': 'Power Rounds', 'weapon_double': 'Damage Amplifier'}.get(key, name)
        text = fitted_text(font, f'{i+1}  {display_name}', TEXT if affordable else MUTED, 370)
        surface.blit(text, (rect.x + 66, rect.y + 8))
        effects = {'power_rounds': '+5 bullet damage', 'needle_rounds': '+1 enemy pierced',
                   'rapid_fire': '+12% fire-rate modifier', 'weapon_double': 'Weapon damage at least x2',
                   'impact_drive': '+0.55 knockback', 'vital_core': '+18 max HP, heal 18',
                   'battle_recovery': '+12 healing per clear', 'heal': 'Restore 45 HP'}
        info = 'Replaces Dash' if key.startswith('skill_') else effects.get(key, '')
        surface.blit(fitted_text(font, info, MUTED, 410), (rect.x + 66, rect.y + 33))
        price = font.render('MAX' if maxed else f'{cost} G', True, config['color'] if affordable else MUTED)
        surface.blit(price, price.get_rect(midright=(rect.right - 14, rect.centery)))
