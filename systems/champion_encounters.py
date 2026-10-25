"""First enemy-identity prototype: shared damage rules, finite escort, readable attacks."""
import pygame
from systems.room_bounds import current_room_rect


def sync_escorts(enemies, solids, player_rect=None):
    from entities.enemy import Enemy, EnemyType
    additions = []
    for leader in tuple(enemies):
        if leader.type != EnemyType.ELITE or not leader.alive or leader.escort_spawned:
            continue
        leader.escort_spawned = True
        for offset in ((-95, 65), (95, 65)):
            guard = Enemy(0, 0, EnemyType.CHASER_TANK, leader.difficulty)
            guard.champion_owner = leader
            guard.max_health = max(1, round(leader.max_health * .22))
            guard.health = guard.max_health
            found = False
            for delta in (offset, (-offset[0], -offset[1]), (0, 130), (130, 0)):
                guard.rect.center = pygame.Vector2(leader.rect.center) + delta
                if (current_room_rect().contains(guard.rect)
                        and not any(guard.rect.colliderect(wall) for wall in solids)
                        and (player_rect is None or not guard.rect.colliderect(player_rect.inflate(90, 90)))
                        and not guard.rect.colliderect(leader.rect)
                        and not any(guard.rect.colliderect(other.rect) for other in additions)):
                    found = True
                    break
            if found:
                leader.escort_guards.append(guard)
                leader.escort_had_guards = True
                additions.append(guard)
    enemies.extend(additions)


def guards_alive(enemy):
    return [guard for guard in enemy.escort_guards
            if guard.alive and getattr(guard, 'champion_owner', None) is enemy]


def update_elite(enemy, dt, player_rect):
    remaining = guards_alive(enemy)
    if enemy.escort_had_guards and not remaining and not enemy.escort_broken:
        enemy.escort_broken = True
        enemy.elite_state = 'stagger'
        enemy.elite_timer = .8
    enemy.escort_had_guards |= bool(remaining)
    delta = pygame.Vector2(player_rect.center) - enemy.rect.center
    direction = delta.normalize() if delta.length_squared() else pygame.Vector2(1, 0)
    state = enemy.elite_state
    if state == 'chase':
        if delta.length() < 390 and enemy.attack_cooldown <= 0 and enemy._has_line_of_sight():
            enemy.elite_state = 'warn_one'
            enemy.elite_timer = .55
            enemy.windup_direction = direction
        else:
            enemy._move(enemy._obstacle_seek_direction(direction), dt)
        return
    enemy.elite_timer = max(0., enemy.elite_timer - dt)
    if state.startswith('strike'):
        enemy._move_vector(enemy.windup_direction * 640 * min(dt, enemy.elite_move_remaining))
        enemy.rect.clamp_ip(current_room_rect())
        enemy.elite_move_remaining = max(0., enemy.elite_move_remaining-dt)
    if enemy.elite_timer > 0:
        return
    if state.startswith('warn'):
        enemy.elite_state = 'strike_one' if state == 'warn_one' else 'strike_two'
        enemy.elite_timer = .22
        enemy.elite_move_remaining = .22
    elif state == 'strike_one':
        enemy.elite_state = 'warn_two'
        enemy.elite_timer = .38
        enemy.windup_direction = direction
        return {'type': 'champion_slam', 'enemy': enemy, 'radius': 78}
    elif state == 'strike_two':
        enemy.elite_state = 'recover'
        enemy.elite_timer = .7
        return {'type': 'champion_slam', 'enemy': enemy, 'radius': 78}
    else:
        enemy.elite_state = 'chase'
        enemy.attack_cooldown = .25


def draw(enemy, surface, camera):
    from systems.sigil_presentation import draw as sigil
    center = camera.apply_pos(pygame.Vector2(enemy.rect.center))
    if enemy.type.name == 'BRUTE':
        opened = enemy.windup_action == 'brute_charge' or enemy.brute_stop_timer > 0
        sigil(surface, 'fx_dash_charge' if opened else 'fx_airstrike_target',
              center, 42 if opened else 76, 240 if opened else 110)
        if opened:
            sigil(surface, 'fx_impact', center, 28, 230)
        if enemy.brute_slam_pending > 0:
            sigil(surface, 'fx_airstrike_target', center, 220, 230)
    elif enemy.type.name == 'ELITE':
        for guard in guards_alive(enemy):
            point = camera.apply_pos(pygame.Vector2(guard.rect.center))
            pygame.draw.line(surface, (155, 108, 205), center, point, 2)
        if guards_alive(enemy):
            sigil(surface, 'fx_vampire_aura', center, 105, 180)
        if enemy.elite_state.startswith('warn'):
            from systems.ranged_presentation import draw_telegraph
            draw_telegraph(surface, center, enemy.windup_direction, 220,
                           enemy.elite_timer, .55 if enemy.elite_state == 'warn_one' else .38,
                           enemy._anim)
