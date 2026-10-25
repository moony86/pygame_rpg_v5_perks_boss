import random

import pygame

from settings import (
    ENEMY_DAMAGE,
    ENEMY_CONTACT_COOLDOWN,
    ENEMY_XP_REWARD,
    ENEMY_GOLD_REWARD,
    JUMPER_DAMAGE,
    BOSS_XP_REWARD,
    BOSS_GOLD_REWARD,
    BOSS_DAMAGE,
    PROJECTILE_KNOCKBACK_COOLDOWN,
)
from entities.enemy import Enemy, EnemyType
from entities.projectile import Projectile
from systems.room_bounds import current_room_rect

LOOT_HIT_GOLD_REWARD = 35
LOOT_HIT_XP_REWARD = 12
LOOT_ESCAPE_KILL_BONUS_MULTIPLIER = 4
PROJECTILE_ENEMY_HURTBOX_INFLATE = 10


def shown_damage(enemy, fallback):
    if enemy.type in (EnemyType.BRUTE, EnemyType.ELITE):
        return round(enemy.last_damage)
    return fallback


class CombatSystem:
    def __init__(self):
        self.player_contact_timer = 0.0
        self.projectile_pool = None

    def _make_projectile(self,x,y,direction,damage,**kwargs):
        if self.projectile_pool is not None:
            return self.projectile_pool.acquire(x,y,direction,damage,**kwargs)
        return Projectile(x,y,direction,damage,**kwargs)

    def reset(self):
        self.player_contact_timer = 0.0

    def _parry_boss_orbs(self,player,projectiles,enemies,bullets,effects,audio,feel):
        from systems.boss_encounter import TUNING
        if not getattr(player,'ninja_dash_charges_enabled',False) or getattr(player,'ninja_parry_timer',0)<=0:
            return
        origin=pygame.Vector2(player.rect.center)
        for bullet in bullets:
            if not bullet.alive or not getattr(bullet,'parryable',False):
                continue
            if not player.rect.inflate(TUNING['parry_range']*2,TUNING['parry_range']*2).clipline(bullet.previous_pos,bullet.pos):
                continue
            if player.dash_direction.dot(-bullet.direction)<.45:
                continue
            boss=next((e for e in enemies if id(e)==bullet.owner_id and e.alive and getattr(e,'encounter',None)),None)
            if boss is None:
                continue
            bullet.kill()
            player.ninja_parry_timer=0.
            boss.encounter.parried()
            direction=pygame.Vector2(boss.rect.center)-origin
            shot=self._make_projectile(origin.x,origin.y,direction,
                boss.max_health*TUNING['reflected_damage_ratio'],speed=1100,source='boss_parry')
            shot.reflected_owner_id=id(boss)
            shot.visual_style='magic'
            shot.remaining_life=5.
            projectiles.append(shot)
            player.refill_dash_charge(1)
            if audio:
                audio.play('ninja_parry')
            if effects:
                effects.message('PARRY!',player.rect.midtop,color=(150,245,255))
                effects.ring(origin,color=(145,240,255),radius=95,life=.25,width=5)
            if feel:
                feel.hit_stop(.07)
            break

    def pressure_boss_after_long_range_hit(self, boss, player):
        if getattr(boss,'encounter',None) is not None:
            return
        if boss.type != EnemyType.BOSS or getattr(boss, "anti_kite_timer", 0) > 0:
            return

        boss_pos = pygame.Vector2(boss.rect.center)
        player_pos = pygame.Vector2(player.rect.center)
        distance = boss_pos.distance_to(player_pos)
        if distance < 520:
            return

        direction = player_pos - boss_pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        if distance > 620:
            boss.windup_timer = 0.0
            boss.windup_action = None
        boss.leap_velocity = direction.normalize() * (560 + boss.phase * 130 + boss.difficulty * 18)
        boss.leap_timer = 0.16 + boss.phase * 0.02
        boss.attack_cooldown = min(getattr(boss, "attack_cooldown", 0.0), 0.38)
        boss.anti_kite_timer = 0.62

    def update(self, dt, player, projectiles, enemies, enemy_bullets, effects=None, audio=None, reward_multiplier=1, enemy_factory=None, loot_system=None, feel=None, spatial_grid=None):
        for enemy in enemies:
            if getattr(enemy,'encounter',None) is not None:
                enemy.encounter.advance_damage_budget(dt)
        self._parry_boss_orbs(player,projectiles,enemies,enemy_bullets,effects,audio,feel)
        if self.player_contact_timer > 0:
            self.player_contact_timer = max(0, self.player_contact_timer - dt)

        kills = 0
        boss_killed = False
        kill_rewarded_ids = set()
        targets=[enemy for enemy in enemies if not (getattr(enemy,'encounter',None) and enemy.encounter.airborne)]

        direct_kills = []
        direct_kills.extend(self._update_dash_strike(player, projectiles, targets, effects, audio, feel))
        direct_kills.extend(self._update_vampire_trail(dt, player, targets, effects, audio))
        direct_kills.extend(self._update_engineer_blades(dt, player, targets, effects, audio, spatial_grid=spatial_grid if len(targets)==len(enemies) else None))
        direct_kills.extend(self._update_engineer_bomber(dt, player, targets, effects, audio))
        direct_kills.extend(self._update_engineer_airstrike(dt, player, targets, effects, audio))
        direct_kills.extend(self._update_blood_bat(dt, player, targets, effects, audio))
        self._update_vampire_wounds(dt, enemies)
        self._update_blood_orbs(dt, player, effects)
        self._update_engineer_helper_projectile(dt, player, projectiles, targets, effects, audio)
        for enemy in direct_kills:
            if id(enemy) in kill_rewarded_ids:
                continue
            kill_rewarded_ids.add(id(enemy))
            kills += 1
            if enemy.type == EnemyType.BOSS:
                boss_killed = True
            self._reward_enemy_kill(player, enemy, enemy_bullets, reward_multiplier, loot_system, feel, effects)

        for projectile in projectiles:
            if not projectile.alive:
                continue
            candidates = spatial_grid.nearby_rect(projectile.rect, padding=96) if spatial_grid is not None else enemies
            for enemy in candidates:
                if getattr(enemy,'encounter',None) and enemy.encounter.airborne:
                    continue
                if not enemy.alive or not projectile.can_hit(enemy):
                    continue
                hit_rect = enemy.rect.inflate(PROJECTILE_ENEMY_HURTBOX_INFLATE, PROJECTILE_ENEMY_HURTBOX_INFLATE)
                if projectile.rect.colliderect(hit_rect):
                    if enemy.type == EnemyType.BOSS and enemy.phase == 1 and getattr(enemy,'encounter',None) is None:
                        if feel:
                            feel.normal_hit()
                        self.pressure_boss_after_long_range_hit(enemy, player)
                        self._apply_sanguine_wound(player, enemy, effects)
                        self._apply_vampire_hit_feed(player, enemy, effects)
                        enemy.shield -= projectile.damage
                        enemy.hit_flash = 0.08

                        if effects:
                            effects.damage_number(projectile.damage, enemy.rect.midtop, critical=projectile.critical)
                            if hasattr(effects,'projectile_hit'):
                                effects.projectile_hit(projectile,projectile.pos,enemy,shield=True)
                            elif hasattr(effects,'impact'):
                                effects.impact(enemy.rect.center,critical=projectile.critical)
                            effects.ring(enemy.rect.center, radius=38, life=0.18, width=2)
                        
                        if audio:
                            audio.play("hit")

                        projectile.register_hit(enemy)

                        if enemy.shield <=0:
                            enemy.shield = 0
                            enemy.phase = 2
                            if feel:
                                feel.boss_phase()

                            if effects:
                                effects.ring(enemy.rect.center, radius=150, life=0.65, width=5)
                                effects.message("SHIELD BROKEN", enemy.rect.midtop)
                            
                            if audio:
                                audio.play("boss_phase")

                        break

                    encounter=getattr(enemy,'encounter',None)
                    if getattr(projectile,'source','')=='boss_parry':
                        if id(enemy)!=getattr(projectile,'reflected_owner_id',None):
                            continue
                        killed=enemy.take_damage(projectile.damage,reflected=True)
                    else:
                        killed = enemy.take_damage(projectile.damage)
                    if enemy.type == EnemyType.BRUTE and enemy.last_damage <= 0:
                        projectile.register_hit(enemy)
                        if effects:
                            effects.projectile_hit(projectile, projectile.pos, enemy, shield=True)
                        if audio:
                            audio.play('boss_guard')
                        break
                    if encounter is not None and encounter.last_damage<=0:
                        projectile.register_hit(enemy)
                        if encounter.block_feedback_timer<=0:
                            encounter.block_feedback_timer=.35
                            if audio:
                                audio.play('boss_guard')
                            if effects:
                                effects.message('CORE SATURATED' if encounter.state=='exposed' else 'GUARDED',enemy.rect.midtop,color=(125,195,235))
                        break
                    self._apply_sanguine_wound(player, enemy, effects)
                    self._apply_vampire_hit_feed(player, enemy, effects)
                    if feel:
                        feel.normal_hit()
                    if enemy.type == EnemyType.BOSS:
                        self.pressure_boss_after_long_range_hit(enemy, player)
                    if (
                        enemy.type == EnemyType.BOSS
                        and encounter is None
                        and not killed
                        and not getattr(enemy, "half_health_elite_spawned", False)
                        and enemy.health <= enemy.max_health * 0.5
                    ):
                        enemy.half_health_elite_spawned = True
                        elite_difficulty = max(1.0, enemy.difficulty * 0.72)
                        if enemy_factory is not None:
                            elite = enemy_factory(enemy.rect.centerx + 120, enemy.rect.centery + 80, EnemyType.ELITE, elite_difficulty)
                        else:
                            elite = Enemy(enemy.rect.centerx + 120, enemy.rect.centery + 80, EnemyType.ELITE, difficulty=elite_difficulty)
                        enemies.append(elite)
                        if effects:
                            effects.ring(elite.rect.center, radius=110, life=0.65, width=5)
                            effects.message("ELITE GUARD SPAWNED", elite.rect.midtop)
                        if audio:
                            audio.play("boss_phase")
                    if getattr(projectile, "knockback", 0) > 0 and getattr(enemy, "knockback_timer", 0) <= 0 and enemy.type != EnemyType.BOSS:
                        push = projectile.direction * projectile.knockback
                        enemy.rect.x += round(push.x)
                        enemy.rect.y += round(push.y)
                        enemy.rect.clamp_ip(current_room_rect())
                        enemy.knockback_timer = PROJECTILE_KNOCKBACK_COOLDOWN
                    if enemy.type == EnemyType.LOOT:
                        player.add_gold(LOOT_HIT_GOLD_REWARD)
                        player.add_xp(LOOT_HIT_XP_REWARD)
                        if effects:
                            effects.message(f"+{LOOT_HIT_GOLD_REWARD}g +{LOOT_HIT_XP_REWARD}xp", enemy.rect.midtop)
                    if effects:
                        effects.damage_number(round(encounter.last_damage) if encounter else shown_damage(enemy, projectile.damage), enemy.rect.midtop, critical=projectile.critical)
                        if hasattr(effects,'projectile_hit'):
                            effects.projectile_hit(projectile,projectile.pos,enemy)
                        elif hasattr(effects,'impact'):
                            effects.impact(enemy.rect.center,critical=projectile.critical)
                        effects.ring(enemy.rect.center, radius=38 if getattr(projectile, "explosive", False) else 26, life=0.18, width=3 if getattr(projectile, "explosive", False) else 2)
                    if getattr(projectile, "explosive", False):
                        explosion_radius = getattr(projectile, "explosion_radius", 95)
                        splash_ratio = getattr(projectile, "explosion_splash_ratio", 1 / 3)
                        splash_damage = max(1, int(projectile.damage * splash_ratio))
                        for splash_enemy in enemies:
                            if splash_enemy is enemy or not splash_enemy.alive or splash_enemy.type == EnemyType.BOSS:
                                continue
                            dx = splash_enemy.rect.centerx - enemy.rect.centerx
                            dy = splash_enemy.rect.centery - enemy.rect.centery
                            if dx * dx + dy * dy <= explosion_radius * explosion_radius:
                                splash_enemy.take_damage(splash_damage)
                                if effects and hasattr(effects,'projectile_hit'):
                                    effects.projectile_hit(projectile,splash_enemy.rect.center,splash_enemy)
                    if audio:
                        from systems.class_audio import impact_cue
                        audio.play(impact_cue(projectile))
                    projectile.register_hit(enemy)

                    if killed and id(enemy) not in kill_rewarded_ids:
                        kill_rewarded_ids.add(id(enemy))
                        kills += 1
                        boss_killed = enemy.type == EnemyType.BOSS
                        self._reward_enemy_kill(player, enemy, enemy_bullets, reward_multiplier, loot_system, feel, effects, audio)
                    break

        for bullet in enemy_bullets:
            if bullet.alive and getattr(bullet, "can_damage", True) and bullet.rect.colliderect(player.rect):
                if player.take_damage(bullet.damage):
                    if feel:
                        feel.player_hit()
                    bullet.kill()
                    if effects:
                        if hasattr(effects,'projectile_hit'):
                            effects.projectile_hit(bullet,bullet.pos,player)
                        effects.ring(player.rect.center, radius=45, life=0.22, width=3)
                    if audio:
                        audio.play("player_hurt")

        if self.player_contact_timer <= 0:
            for enemy in enemies:
                if enemy.alive and not getattr(enemy,'is_boss_eye',False) and not (getattr(enemy,'encounter',None) and enemy.encounter.airborne) and player.rect.colliderect(enemy.rect):
                    if enemy.type == EnemyType.BOSS:
                        damage = BOSS_DAMAGE
                    elif getattr(enemy, "leap_timer", 0) > 0:
                        damage = JUMPER_DAMAGE
                    else:
                        damage = ENEMY_DAMAGE
                    damage = int(damage * getattr(enemy, "damage_multiplier", 1.0))
                    if getattr(enemy,'encounter',None) is not None:
                        damage=24+enemy.phase*2
                    if player.take_damage(damage):
                        if feel:
                            feel.player_hit()
                        self.player_contact_timer = ENEMY_CONTACT_COOLDOWN
                        if effects:
                            effects.ring(player.rect.center, radius=45, life=0.22, width=3)
                        if audio:
                            audio.play("player_hurt")
                    break

        return kills, boss_killed

    def _update_dash_strike(self, player, projectiles, enemies, effects=None, audio=None, feel=None):
        killed_enemies = []
        damage = getattr(player, "dash_strike_damage", 0)
        if damage <= 0 or not (getattr(player, "dash_timer", 0) > 0 or getattr(player, "dash_strike_active_this_frame", False)):
            return killed_enemies
        hit_ids = getattr(player, "dash_strike_hit_ids", set())
        restore = getattr(player, "dash_strike_cooldown_restore", 0.0)
        for enemy in enemies:
            if not enemy.alive or id(enemy) in hit_ids or getattr(enemy, "type", None) == EnemyType.BOSS:
                continue
            swept_hit = enemy.rect.inflate(player.rect.width + 18, player.rect.height + 18).clipline(
                getattr(player, "dash_previous_center", player.rect.center), player.rect.center)
            if not player.rect.inflate(18, 18).colliderect(enemy.rect) and not swept_hit:
                continue
            hit_ids.add(id(enemy))
            momentum = getattr(player, "ninja_momentum", 0.0)
            total_damage = damage + int(damage * 0.55 * momentum)
            killed = enemy.take_damage(total_damage)
            if enemy.type == EnemyType.BRUTE and enemy.last_damage <= 0:
                if effects:
                    effects.impact(enemy.rect.center)
                continue
            if hasattr(player, "trigger_sword_attack"):
                player.trigger_sword_attack()
            player.grant_dash_refund(restore + 0.20 * momentum)
            self._spawn_ninja_shuriken(player, projectiles, enemy)
            if effects:
                effects.damage_number(shown_damage(enemy, total_damage), enemy.rect.midtop, critical=False)
                effects.ring(enemy.rect.center, radius=44, life=0.18, width=3)
                if hasattr(effects, "slash"):
                    slash_dir = getattr(player, "dash_direction", pygame.Vector2(1, 0))
                    if slash_dir.length_squared() == 0:
                        slash_dir = pygame.Vector2(1, 0)
                    slash_dir = slash_dir.normalize()
                    slash_side = pygame.Vector2(-slash_dir.y, slash_dir.x)
                    center = pygame.Vector2(enemy.rect.center)
                    effects.slash(center - slash_dir * 36 - slash_side * 24, center + slash_dir * 42 + slash_side * 24)
            if audio:
                audio.play("hit")
            if killed:
                killed_enemies.append(enemy)
            elif getattr(player, "ninja_chain_active", False):
                previous = player.rect.copy()
                previous.center = player.dash_previous_center
                if (player.rect.colliderect(enemy.rect)
                        and not previous.colliderect(enemy.rect)
                        and not any(previous.colliderect(wall) for wall in player.ninja_dash_solids)):
                    player.rect.center = previous.center
                player.finish_ninja_chain()
        if killed_enemies and getattr(player, "ninja_dash_charges_enabled", False):
            for enemy in killed_enemies:
                if effects:
                    center = pygame.Vector2(enemy.rect.center)
                    side = pygame.Vector2(-player.dash_direction.y, player.dash_direction.x)
                    effects.slash(center - side * 38, center + side * 38,
                                  color=(213, 174, 255), life=0.22, width=9)
                    effects.ring(center, color=(185, 125, 255), radius=58, life=0.20, width=3)
                if feel:
                    feel.hit_stop(0.060)
            # One new leg per simulation frame; no charge spent and no hit-id reset.
            player.ninja_chain_kills += len(killed_enemies) - 1
            player.try_ninja_finisher_chain(enemies)
        return killed_enemies

    def _update_vampire_wounds(self, dt, enemies):
        for enemy in enemies:
            timer = getattr(enemy, "vampire_wound_timer", 0.0)
            if timer <= 0:
                continue
            timer = max(0.0, timer - dt)
            enemy.vampire_wound_timer = timer
            if timer <= 0:
                enemy.vampire_wound_stacks = 0

    def _apply_sanguine_wound(self, player, enemy, effects=None):
        stacks_per_hit = getattr(player, "vampire_wound_stacks_per_hit", 0)
        max_stacks = getattr(player, "vampire_wound_max_stacks", 0)
        if stacks_per_hit <= 0 or max_stacks <= 0 or not getattr(enemy, "alive", False):
            return
        current = getattr(enemy, "vampire_wound_stacks", 0)
        enemy.vampire_wound_stacks = min(max_stacks, current + stacks_per_hit)
        enemy.vampire_wound_timer = getattr(player, "vampire_wound_duration", 5.0)
        if effects:
            effects.ring(enemy.rect.center, color=(210, 30, 70), radius=18 + 5 * enemy.vampire_wound_stacks, life=0.14, width=2)

    def _update_blood_orbs(self, dt, player, effects=None):
        orbs = getattr(player, "vampire_blood_orbs", [])
        if not orbs:
            return
        center = pygame.Vector2(player.rect.center)
        attract_radius = player.vampire_orb_attraction_radius() if hasattr(player, "vampire_orb_attraction_radius") else getattr(player, "vampire_orb_attract_radius", 96)
        collect_radius = max(32, min(64, int(attract_radius * 0.30)))
        kept = []
        for orb in orbs:
            orb["life"] -= dt
            if orb["life"] <= 0:
                continue
            direction = center - orb["pos"]
            distance = direction.length()
            if distance <= collect_radius:
                gained = player.add_blood(orb["value"], source="orb")
                heal = getattr(player, "vampire_orb_heal", 0)
                if heal > 0 and gained > 0:
                    player.heal(heal + (1 if getattr(player, "vampire_feast_timer", 0) > 0 else 0))
                if effects and gained:
                    if hasattr(effects,'collect_pickup'):
                        effects.collect_pickup('blood',gained,player.rect.center)
                    else:
                        effects.message(f"BLOOD ORB +{gained}", player.rect.midtop)
                continue
            if distance <= attract_radius and distance > 0:
                orb["vel"] += direction.normalize() * (520 + attract_radius * 1.5) * dt
            orb["vel"] *= max(0.0, 1.0 - 2.8 * dt)
            orb["pos"] += orb["vel"] * dt
            kept.append(orb)
        player.vampire_blood_orbs = kept

    def _spawn_blood_orb(self, player, enemy, value=None, effects=None):
        if getattr(player, "vampire_orb_drop_chance", 0.0) <= 0:
            return False
        if len(getattr(player, "vampire_blood_orbs", [])) >= getattr(player, "vampire_orb_cap", 16):
            return False
        if random.random() > getattr(player, "vampire_orb_drop_chance", 0.0):
            return False
        amount = value if value is not None else getattr(player, "vampire_orb_value", 1)
        if amount <= 0:
            return False
        angle = random.uniform(0, 360)
        player.vampire_blood_orbs.append({
            "pos": pygame.Vector2(enemy.rect.center),
            "vel": pygame.Vector2(1, 0).rotate(angle) * random.uniform(90, 150),
            "value": int(amount),
            "life": 8.0,
        })
        if effects:
            effects.ring(enemy.rect.center, color=(230, 35, 75), radius=34, life=0.24, width=3)
        return True

    def _update_blood_bat(self, dt, player, enemies, effects=None, audio=None):
        killed_enemies = []
        if not getattr(player, "vampire_bat_enabled", False):
            player.vampire_bat_state = "inactive"
            player.vampire_bat_pos.update(player.rect.center)
            return killed_enemies

        state = getattr(player, "vampire_bat_state", "inactive")
        if state == "inactive":
            player.vampire_bat_state = "ready"
            player.vampire_bat_pos.update(player.rect.center)
            player.vampire_bat_chain_kills = 0
            return killed_enemies
        if state == "cooldown":
            player.vampire_bat_timer = max(0.0, player.vampire_bat_timer - dt)
            rest = pygame.Vector2(player.rect.center) + pygame.Vector2(36, -48)
            player.vampire_bat_pos += (rest - player.vampire_bat_pos) * min(1.0, dt * 7.0)
            if player.vampire_bat_timer <= 0:
                player.vampire_bat_state = "ready"
            return killed_enemies
        if state == "ready":
            player.vampire_bat_search_timer = max(0.0, getattr(player, "vampire_bat_search_timer", 0.0) - dt)
            if player.vampire_bat_search_timer > 0:
                return killed_enemies
            player.vampire_bat_search_timer = 0.05
            target = self._acquire_bat_target(player, enemies)
            if target is None:
                return killed_enemies
            player.vampire_bat_target_id = id(target)
            player.vampire_bat_target_pos.update(target.rect.center)
            player.vampire_bat_state = "diving"
            return killed_enemies
        if state == "returning":
            if self._move_bat_toward(player, pygame.Vector2(player.rect.center), dt) <= 24:
                if player.vampire_bat_carried_blood > 0:
                    gained = player.add_blood(player.vampire_bat_carried_blood, source="bat")
                    if effects and gained:
                        effects.message(f"BAT +{gained}", player.rect.midtop)
                player.vampire_bat_carried_blood = 0
                player.vampire_bat_chain_kills = 0
                player.vampire_bat_state = "cooldown"
                cooldown = player.vampire_bat_rest_cooldown() if hasattr(player, "vampire_bat_rest_cooldown") else getattr(player, "vampire_bat_cooldown", 3.0)
                player.vampire_bat_timer = cooldown
            return killed_enemies
        if state == "feeding":
            player.vampire_bat_timer = max(0.0, player.vampire_bat_timer - dt)
            if player.vampire_bat_timer <= 0:
                cap = max(1, getattr(player, "vampire_bat_chain_cap", 1))
                if getattr(player, "vampire_bat_chain_kills", 0) >= cap:
                    player.vampire_bat_state = "returning"
                    return killed_enemies
                target = self._acquire_bat_target(player, enemies)
                if target is None:
                    player.vampire_bat_state = "returning"
                    return killed_enemies
                player.vampire_bat_target_id = id(target)
                player.vampire_bat_target_pos.update(target.rect.center)
                player.vampire_bat_state = "diving"
            return killed_enemies
        if state != "diving":
            return killed_enemies

        target = next((enemy for enemy in enemies if enemy.alive and id(enemy) == player.vampire_bat_target_id), None)
        if target is None:
            player.vampire_bat_state = "returning"
            return killed_enemies
        player.vampire_bat_target_pos.update(target.rect.center)
        if self._move_bat_toward(player, pygame.Vector2(target.rect.center), dt) > 22:
            return killed_enemies
        damage = max(1, int(getattr(player, "vampire_bat_damage", 1)))
        if getattr(player, "vampire_blood_moon_timer", 0) > 0:
            damage = int(damage * 1.25)
        killed = target.take_damage(damage)
        if target.type != EnemyType.BRUTE or target.last_damage > 0:
            player.vampire_bat_carried_blood = min(4, player.vampire_bat_carried_blood + getattr(player, "vampire_bat_feed_value", 1))
        if effects:
            effects.damage_number(shown_damage(target, damage), target.rect.midtop, critical=False)
            effects.ring(target.rect.center, color=(230, 40, 80), radius=36, life=0.18, width=3)
        if audio:
            audio.play("hit")
        if killed:
            killed_enemies.append(target)
            player.vampire_bat_chain_kills = getattr(player, "vampire_bat_chain_kills", 0) + 1
        player.vampire_bat_state = "feeding"
        player.vampire_bat_timer = 0.08
        return killed_enemies

    def _acquire_bat_target(self, player, enemies):
        player_center = pygame.Vector2(player.rect.center)
        candidates = [
            enemy for enemy in enemies
            if enemy.alive
            and getattr(enemy, "vampire_wound_stacks", 0) > 0
            and player_center.distance_squared_to(enemy.rect.center) <= 700 * 700
        ]
        if not candidates:
            return None

        def score(enemy):
            stacks = getattr(enemy, "vampire_wound_stacks", 0)
            missing = 1.0 - max(0.0, enemy.health / max(1, enemy.max_health))
            distance = player_center.distance_to(enemy.rect.center)
            boss_bonus = 0.3 if getattr(enemy, "type", None) == EnemyType.BOSS else 0.0
            return (stacks + missing + boss_bonus, -distance)

        return max(candidates, key=score)

    def _move_bat_toward(self, player, target_pos, dt):
        direction = target_pos - player.vampire_bat_pos
        distance = direction.length()
        if distance > 0:
            speed = getattr(player, "vampire_bat_speed", 420)
            player.vampire_bat_pos += direction.normalize() * min(distance, speed * dt)
        return player.vampire_bat_pos.distance_to(target_pos)

    def _update_vampire_trail(self, dt, player, enemies, effects=None, audio=None):
        killed_enemies = []
        if not getattr(player, "vampire_trail_enabled", False):
            return killed_enemies
        player.vampire_trail_timer = max(0.0, getattr(player, "vampire_trail_timer", 0.0) - dt)
        moving = getattr(player, "move_direction", pygame.Vector2()).length_squared() > 0.01
        if not moving:
            return killed_enemies
        timer = max(0.0, getattr(player, "vampire_trail_timer", 0.0))
        if timer > 0:
            player.vampire_trail_timer = max(0.0, timer)
            return killed_enemies
        cap = getattr(player, "vampire_trail_harvest_cap", 0)
        if getattr(player, "vampire_blood_moon_timer", 0) > 0:
            cap += 1
        if cap <= 0:
            return killed_enemies
        player.vampire_trail_hit_ids.clear()
        player.vampire_trail_harvested_this_dash = 0
        hit_ids = getattr(player, "vampire_trail_hit_ids", set())
        radius = max(0, int(getattr(player, "vampire_trail_radius", 72)))
        harvest_rect = player.rect.inflate(radius, radius)
        for enemy in enemies:
            if not enemy.alive or id(enemy) in hit_ids or getattr(enemy, "vampire_wound_stacks", 0) <= 0:
                continue
            if not harvest_rect.colliderect(enemy.rect):
                continue
            if enemy.type == EnemyType.BRUTE and not (enemy.windup_action == 'brute_charge' or enemy.brute_stop_timer > 0):
                continue
            hit_ids.add(id(enemy))
            player.vampire_trail_harvested_this_dash += 1
            enemy.vampire_wound_stacks = max(0, getattr(enemy, "vampire_wound_stacks", 0) - 1)
            gained = player.add_blood(getattr(player, "vampire_trail_harvest_value", 1), source="trail")
            damage = 8 + 4 * getattr(player, "vampire_trail_level", 1)
            killed = enemy.take_damage(damage)
            if effects:
                effects.damage_number(shown_damage(enemy, damage), enemy.rect.midtop, critical=False)
                effects.ring(enemy.rect.center, color=(255, 45, 90), radius=46, life=0.18, width=3)
                if gained:
                    effects.message(f"TRAIL +{gained}", enemy.rect.midtop)
            if audio:
                audio.play("hit")
            if killed:
                killed_enemies.append(enemy)
            if player.vampire_trail_harvested_this_dash >= cap:
                break
        if player.vampire_trail_harvested_this_dash > 0:
            interval = getattr(player, "vampire_trail_interval", 0.75)
            if getattr(player, "vampire_blood_moon_timer", 0) > 0:
                interval *= 0.75
            player.vampire_trail_timer = max(0.10, interval)
        return killed_enemies

    def _update_engineer_helper_projectile(self, dt, player, projectiles, enemies, effects=None, audio=None):
        if not getattr(player, "engineer_helper_enabled", False):
            return None
        if getattr(player, "engineer_helper_timer", 0.0) > 0:
            return None
        living = [
            enemy for enemy in enemies
            if enemy.alive and getattr(enemy, "type", None) != EnemyType.BOSS
        ]
        if not living:
            player.engineer_drone_target_id = None
            return None
        player_center = pygame.Vector2(player.rect.center)
        gun_range = getattr(player, "engineer_gun_range", 500)
        in_range = [
            enemy for enemy in living
            if pygame.Vector2(enemy.rect.center).distance_squared_to(player_center) <= gun_range * gun_range
        ]
        if not in_range:
            player.engineer_drone_target_id = None
            return None
        in_range.sort(key=lambda enemy: pygame.Vector2(enemy.rect.center).distance_squared_to(player_center))
        damage = max(1, int(getattr(player, "engineer_helper_damage", 1)))
        origins = list(getattr(player, "engineer_drone_positions", [])) or [pygame.Vector2(getattr(player, "engineer_drone_pos", player.rect.center))]
        drone_count = max(1, min(getattr(player, "engineer_gun_count", 1), len(origins)))
        burst_count = max(1, getattr(player, "engineer_gun_burst_count", 1))
        fired = 0
        target_ids = []
        visual_directions = []
        for drone_index, origin in enumerate(origins[:drone_count]):
            target = in_range[min(drone_index, len(in_range) - 1)]
            target_ids.append(id(target))
            visual_directions.append(pygame.Vector2(target.rect.center) - origin)
            for burst_index in range(burst_count):
                direction = pygame.Vector2(target.rect.center) - origin
                if direction.length_squared() == 0:
                    direction = pygame.Vector2(1, 0)
                if burst_count > 1:
                    direction = direction.rotate((burst_index - (burst_count - 1) / 2) * 4)
                projectiles.append(
                    self._make_projectile(
                        origin.x,
                        origin.y,
                        direction,
                        damage,
                        speed=getattr(player, "engineer_helper_projectile_speed", 720),
                        pierce=0,
                        critical=False,
                        knockback=10 * getattr(player, "knockback_power", 1.0),
                        source="engineer_drone",
                    )
                )
                fired += 1
        if fired <= 0:
            return None
        player.engineer_helper_timer = max(0.34, getattr(player, "engineer_helper_cooldown", 1.65))
        player.engineer_drone_target_id = target_ids[0] if target_ids else None
        player.engineer_drone_visual_directions = visual_directions
        player.engineer_drone_attack_flash = 0.18
        if effects:
            for origin in origins[:drone_count]:
                effects.ring(origin, radius=28, life=0.14, width=2)
            effects.ring(player.rect.center, radius=26, life=0.14, width=2)
        if audio:
            audio.play("shoot_engineer")
        return in_range[0]

    def _update_engineer_airstrike(self, dt, player, enemies, effects=None, audio=None):
        killed_enemies = []
        if not getattr(player, "engineer_airstrike_unlocked", False):
            player.engineer_airstrike_state = "inactive"
            return killed_enemies
        if getattr(player, "engineer_airstrike_cooldown_timer", 0.0) > 0:
            return killed_enemies

        state = getattr(player, "engineer_airstrike_state", "inactive")
        if state == "cooldown":
            player.engineer_airstrike_state = "ready"
            state = "ready"
        if state in ("inactive", "ready"):
            target = self._acquire_airstrike_target(player, enemies)
            if target is None:
                player.engineer_airstrike_state = "ready"
                return killed_enemies
            player.engineer_airstrike_target_pos.update(target)
            player.engineer_airstrike_state = "telegraph"
            player.engineer_airstrike_timer = 0.85
            if effects:
                effects.airstrike_launch(target, getattr(player, "engineer_airstrike_radius", 160))
            if audio:
                audio.play("shoot_engineer")
            return killed_enemies

        if state != "telegraph":
            return killed_enemies

        player.engineer_airstrike_timer = max(0.0, player.engineer_airstrike_timer - dt)
        if player.engineer_airstrike_timer > 0:
            return killed_enemies

        center = pygame.Vector2(player.engineer_airstrike_target_pos)
        radius = getattr(player, "engineer_airstrike_radius", 160)
        damage = getattr(player, "engineer_airstrike_damage", 110)
        if effects:
            effects.airstrike_impact(center, radius)
        if audio:
            audio.play("hit")
        for enemy in list(enemies):
            if not enemy.alive or getattr(enemy, "type", None) == EnemyType.BOSS:
                continue
            distance = center.distance_to(enemy.rect.center)
            if distance > radius * 1.45:
                continue
            if distance <= radius * 0.42:
                scaled_damage = damage
            elif distance <= radius:
                scaled_damage = max(1, int(damage * 0.55))
            else:
                scaled_damage = max(1, int(damage * 0.22))
            killed = enemy.take_damage(scaled_damage)
            if effects:
                effects.damage_number(shown_damage(enemy, scaled_damage), enemy.rect.midtop, critical=False)
            if killed:
                killed_enemies.append(enemy)
        player.engineer_airstrike_state = "cooldown"
        player.engineer_airstrike_cooldown_timer = getattr(player, "engineer_airstrike_cooldown", 28.0)
        return killed_enemies

    def _acquire_airstrike_target(self, player, enemies):
        candidates = [
            enemy for enemy in enemies
            if enemy.alive and getattr(enemy, "type", None) != EnemyType.BOSS
            and pygame.Vector2(enemy.rect.center).distance_squared_to(player.rect.center) <= 900 * 900
        ]
        if not candidates:
            return None

        def score(enemy):
            center = pygame.Vector2(enemy.rect.center)
            nearby = sum(
                1 for other in candidates
                if other is not enemy and center.distance_squared_to(other.rect.center) <= 180 * 180
            )
            distance = center.distance_to(player.rect.center)
            return (nearby, -distance)

        return pygame.Vector2(max(candidates, key=score).rect.center)

    def _update_engineer_blades(self, dt, player, enemies, effects=None, audio=None, spatial_grid=None):
        killed_enemies = []
        if getattr(player, "engineer_blade_count", 0) <= 0:
            return killed_enemies
        live_ids = {id(enemy) for enemy in enemies if enemy.alive}
        player.engineer_blade_hit_timers = {
            enemy_id: timer
            for enemy_id, timer in getattr(player, "engineer_blade_hit_timers", {}).items()
            if enemy_id in live_ids and timer > 0
        }
        positions = getattr(player, "engineer_blade_positions", [])
        if not positions:
            return killed_enemies
        radius = 24
        damage = max(1, int(getattr(player, "engineer_blade_damage", 1)))
        overdrive = getattr(player, "engineer_blade_overdrive_timer", 0.0) > 0
        if overdrive:
            damage += getattr(player, "engineer_blade_overdrive_damage_bonus", 0)
        if spatial_grid is not None:
            candidate_map = {}
            for blade_pos in positions:
                rect = pygame.Rect(round(blade_pos.x - 64), round(blade_pos.y - 64), 128, 128)
                for enemy in spatial_grid.nearby_rect(rect):
                    candidate_map[id(enemy)] = enemy
            candidates = list(candidate_map.values())
        else:
            candidates = list(enemies)
        for enemy in candidates:
            if not enemy.alive:
                continue
            enemy_id = id(enemy)
            if player.engineer_blade_hit_timers.get(enemy_id, 0) > 0:
                continue
            enemy_center = pygame.Vector2(enemy.rect.center)
            hit_pos = None
            for blade_pos in positions:
                if blade_pos.distance_squared_to(enemy_center) <= (radius + max(enemy.rect.width, enemy.rect.height) * 0.5) ** 2:
                    hit_pos = blade_pos
                    break
            if hit_pos is None:
                continue
            player.engineer_blade_hit_timers[enemy_id] = getattr(player, "engineer_blade_hit_cooldown", 0.6)
            player.engineer_blade_hit_flash = 0.16
            killed = enemy.take_damage(damage)
            if effects:
                effects.damage_number(shown_damage(enemy, damage), enemy.rect.midtop, critical=False)
                if hasattr(effects, "blade_hit"):
                    effects.blade_hit(hit_pos, strong=overdrive)
                else:
                    effects.ring(hit_pos, radius=34, life=0.16, width=2)
            if audio:
                audio.play("hit")
            if killed:
                killed_enemies.append(enemy)
        return killed_enemies

    def _update_engineer_bomber(self, dt, player, enemies, effects=None, audio=None):
        killed_enemies = []
        if getattr(player, "engineer_bomber_max_runs", 0) <= 0:
            player.engineer_bomber_state = "inactive"
            return killed_enemies

        state = getattr(player, "engineer_bomber_state", "inactive")
        if state == "inactive":
            player.engineer_bomber_state = "ready"
            player.engineer_bomber_pos.update(player.engineer_bomber_launch_pos())
            return killed_enemies

        if state == "cooldown":
            player.engineer_bomber_timer = max(0.0, player.engineer_bomber_timer - dt)
            if player.engineer_bomber_timer <= 0:
                player.engineer_bomber_state = "respawn"
                player.engineer_bomber_timer = 0.35
            return killed_enemies

        if state == "respawn":
            player.engineer_bomber_timer = max(0.0, player.engineer_bomber_timer - dt)
            if player.engineer_bomber_timer <= 0:
                player.engineer_bomber_state = "ready"
                player.engineer_bomber_runs_remaining = 0
                player.engineer_bomber_pos.update(player.engineer_bomber_launch_pos())
            return killed_enemies

        if state == "ready":
            player.engineer_bomber_state = "acquire"
            player.engineer_bomber_runs_remaining = max(1, getattr(player, "engineer_bomber_max_runs", 1))
            return killed_enemies

        if state == "acquire":
            target = self._acquire_bomber_target(player, enemies)
            if target is None:
                player.engineer_bomber_state = "ready"
                player.engineer_bomber_target_id = None
                return killed_enemies
            player.engineer_bomber_target_id = id(target)
            player.engineer_bomber_target_pos.update(target.rect.center)
            player.engineer_bomber_state = "flying"
            player.engineer_bomber_timer = 2.4
            if audio:
                audio.play("shoot_engineer")
            return killed_enemies

        if state != "flying":
            return killed_enemies

        target = next((enemy for enemy in enemies if enemy.alive and id(enemy) == player.engineer_bomber_target_id), None)
        if target is not None:
            player.engineer_bomber_target_pos.update(target.rect.center)
        direction = player.engineer_bomber_target_pos - player.engineer_bomber_pos
        distance = direction.length()
        player.engineer_bomber_timer = max(0.0, player.engineer_bomber_timer - dt)
        if distance > 0:
            step = min(distance, getattr(player, "engineer_bomber_speed", 430) * dt)
            player.engineer_bomber_pos += direction.normalize() * step
        if distance > 24 and player.engineer_bomber_timer > 0:
            return killed_enemies

        killed_enemies.extend(self._explode_engineer_bomber(player, enemies, effects, audio))
        player.engineer_bomber_runs_remaining = max(0, player.engineer_bomber_runs_remaining - 1)
        if player.engineer_bomber_runs_remaining > 0:
            player.engineer_bomber_state = "respawn"
            player.engineer_bomber_timer = 0.45
            player.engineer_bomber_target_id = None
        else:
            player.engineer_bomber_state = "cooldown"
            player.engineer_bomber_timer = getattr(player, "engineer_bomber_cooldown", 5.0)
            player.engineer_bomber_target_id = None
        return killed_enemies

    def _acquire_bomber_target(self, player, enemies):
        candidates = [
            enemy for enemy in enemies
            if enemy.alive and getattr(enemy, "type", None) != EnemyType.BOSS
            and pygame.Vector2(enemy.rect.center).distance_squared_to(player.rect.center) <= 760 * 760
        ]
        if not candidates:
            return None
        def score(enemy):
            center = pygame.Vector2(enemy.rect.center)
            nearby = 0
            for other in candidates:
                if other is enemy:
                    continue
                if center.distance_squared_to(other.rect.center) <= 150 * 150:
                    nearby += 1
            distance = center.distance_to(player.rect.center)
            return (nearby, -distance)
        return max(candidates, key=score)

    def _explode_engineer_bomber(self, player, enemies, effects=None, audio=None):
        killed_enemies = []
        radius = getattr(player, "engineer_bomber_radius", 96)
        damage = max(1, int(getattr(player, "engineer_bomber_damage", 1)))
        center = pygame.Vector2(player.engineer_bomber_pos)
        player.engineer_bomber_explosion_flash = 0.28
        if effects:
            effects.explosion(center, radius)
            effects.ring(center, color=(255, 120, 45), radius=radius, life=0.36, width=5)
            effects.message("BOMBER", center)
        if audio:
            audio.play("hit")
        for enemy in list(enemies):
            if not enemy.alive or getattr(enemy, "type", None) == EnemyType.BOSS:
                continue
            if center.distance_squared_to(enemy.rect.center) > radius * radius:
                continue
            killed = enemy.take_damage(damage)
            if effects:
                effects.damage_number(shown_damage(enemy, damage), enemy.rect.midtop, critical=False)
            if killed:
                killed_enemies.append(enemy)
        return killed_enemies

    def _spawn_ninja_shuriken(self, player, projectiles, enemy):
        damage = getattr(player, "ninja_shuriken_damage", 0)
        if damage <= 0:
            return
        origin = pygame.Vector2(player.rect.center)
        direction = pygame.Vector2(enemy.rect.center) - origin
        if direction.length_squared() == 0:
            direction = player.aim_direction
        projectiles.append(
            self._make_projectile(
                origin.x,
                origin.y,
                direction,
                damage + int(damage * getattr(player, "ninja_momentum", 0.0)),
                speed=max(500, getattr(player, "ninja_shuriken_speed", 760)),
                pierce=0,
                critical=False,
                source="ninja_shuriken",
            )
        )

    def _reward_enemy_kill(self, player, enemy, enemy_bullets, reward_multiplier, loot_system, feel=None, effects=None, audio=None):
        if getattr(enemy,'is_boss_guard',False):
            if audio:
                audio.play('enemy_death')
            if effects:
                effects.actor_death(enemy)
            self._apply_vampire_kill_reward(player,enemy,effects)
            return
        if getattr(enemy,'is_boss_eye',False):
            if audio:
                audio.play('boss_eye_break')
            if effects:
                effects.ring(enemy.rect.center,color=(100,245,165),radius=65,life=.3,width=4)
            return
        owner_id = id(enemy)
        for bullet in enemy_bullets:
            if getattr(bullet, "owner_id", None) == owner_id:
                bullet.kill()
        if audio:
            audio.play("enemy_death")
        if effects:
            effects.ring(enemy.rect.center, radius=62, life=0.30, width=4)
            if enemy.type == EnemyType.CHASER:
                effects.chaser_death(enemy)
            else:
                effects.actor_death(enemy)
        if enemy.type == EnemyType.BOSS:
            player.add_xp(BOSS_XP_REWARD)
            player.add_gold(BOSS_GOLD_REWARD)
        elif enemy.type == EnemyType.ELITE:
            if feel:
                feel.elite_kill()
            xp = ENEMY_XP_REWARD * reward_multiplier * 5
            gold = ENEMY_GOLD_REWARD * reward_multiplier * 6
            if loot_system:
                loot_system.spawn_enemy_rewards(enemy.rect.center, gold, xp, enemy.type)
            else:
                player.add_xp(xp)
                player.add_gold(gold)
        elif enemy.type == EnemyType.LOOT:
            if feel:
                feel.enemy_kill()
            bonus_gold = LOOT_HIT_GOLD_REWARD * LOOT_ESCAPE_KILL_BONUS_MULTIPLIER
            bonus_xp = LOOT_HIT_XP_REWARD * LOOT_ESCAPE_KILL_BONUS_MULTIPLIER
            if loot_system:
                loot_system.spawn_enemy_rewards(enemy.rect.center, bonus_gold, bonus_xp, enemy.type)
            else:
                player.add_xp(bonus_xp)
                player.add_gold(bonus_gold)
            if effects:
                effects.message(f"LOOT BONUS +{bonus_gold}g +{bonus_xp}xp", enemy.rect.midtop)
        else:
            if feel:
                feel.enemy_kill()
            xp = ENEMY_XP_REWARD * reward_multiplier
            gold = ENEMY_GOLD_REWARD * reward_multiplier
            if loot_system:
                loot_system.spawn_enemy_rewards(enemy.rect.center, gold, xp, enemy.type)
            else:
                player.add_xp(xp)
                player.add_gold(gold)
        self._apply_vampire_kill_reward(player, enemy, effects)

    def _apply_vampire_kill_reward(self, player, enemy, effects=None):
        heal = getattr(player, "vampire_kill_heal", 0)
        blood_gain = getattr(player, "vampire_blood_per_kill", 0)
        if getattr(enemy, "_vampire_rewarded", False):
            return
        enemy._vampire_rewarded = True
        wounded = getattr(enemy, "vampire_wound_stacks", 0) > 0
        if getattr(enemy, "type", None) == EnemyType.ELITE:
            heal += getattr(player, "vampire_elite_bonus_heal", 0)
            blood_gain += 2
        if wounded:
            self._spawn_blood_orb(player, enemy, effects=effects)
            if blood_gain <= 0:
                blood_gain = 1
        before = player.health
        if blood_gain:
            source = "wounded_kill" if wounded else "kill"
            player.add_blood(blood_gain, source=source)
        if heal:
            player.heal(heal + min(getattr(player, "vampire_blood", 0), 3))
        if effects and player.health > before:
            effects.message(f"BLOOD +{player.health - before}", player.rect.midtop)

    def _apply_vampire_hit_feed(self, player, enemy, effects=None):
        feed = 0
        if getattr(enemy, "type", None) == EnemyType.BOSS:
            feed = getattr(player, "vampire_blood_on_boss_hit", 0)
        elif getattr(player, "vampire_blood_on_hit", 0) > 0:
            counter = getattr(enemy, "_vampire_hit_counter", 0) + 1
            enemy._vampire_hit_counter = counter
            if counter % 3 == 0:
                feed = getattr(player, "vampire_blood_on_hit", 0)
        if feed <= 0:
            return
        source = "boss_hit" if getattr(enemy, "type", None) == EnemyType.BOSS else "hit"
        gained = player.add_blood(feed, source=source)
        if gained and effects:
            effects.message(f"BLOOD +{gained}", enemy.rect.midtop)
