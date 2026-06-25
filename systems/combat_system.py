from settings import (
    ENEMY_DAMAGE,
    ENEMY_CONTACT_COOLDOWN,
    ENEMY_XP_REWARD,
    ENEMY_GOLD_REWARD,
    JUMPER_DAMAGE,
    BOSS_XP_REWARD,
    BOSS_GOLD_REWARD,
    BOSS_DAMAGE,
)
from entities.enemy import EnemyType

LOOT_HIT_GOLD_REWARD = 100
LOOT_HIT_XP_REWARD = 22
LOOT_ESCAPE_KILL_BONUS_MULTIPLIER = 10


class CombatSystem:
    def __init__(self):
        self.player_contact_timer = 0.0

    def reset(self):
        self.player_contact_timer = 0.0

    def update(self, dt, player, projectiles, enemies, enemy_bullets, effects=None, audio=None, reward_multiplier=1):
        if self.player_contact_timer > 0:
            self.player_contact_timer = max(0, self.player_contact_timer - dt)

        kills = 0
        boss_killed = False

        for projectile in projectiles:
            if not projectile.alive:
                continue
            for enemy in enemies:
                if not enemy.alive or not projectile.can_hit(enemy):
                    continue
                if projectile.rect.colliderect(enemy.rect):
                    if enemy.type == EnemyType.BOSS and enemy.phase == 1:
                        enemy.shield -= projectile.damage
                        enemy.hit_flash = 0.08

                        if effects:
                            effects.damage_number(projectile.damage, enemy.rect.midtop, critical=projectile.critical)
                            effects.ring(enemy.rect.center, radius=38, life=0.18, width=2)
                        
                        if audio:
                            audio.play("hit")

                        projectile.register_hit(enemy)

                        if enemy.shield <=0:
                            enemy.shield = 0
                            enemy.phase = 2

                            if effects:
                                effects.ring(enemy.rect.center, radius=150, life=0.65, width=5)
                                effects.message("SHIELD BROKEN", enemy.rect.midtop)
                            
                            if audio:
                                audio.play("boss_phase")

                        break

                    killed = enemy.take_damage(projectile.damage)
                    if enemy.type == EnemyType.LOOT:
                        player.add_gold(LOOT_HIT_GOLD_REWARD)
                        player.add_xp(LOOT_HIT_XP_REWARD)
                        if effects:
                            effects.message(f"+{LOOT_HIT_GOLD_REWARD}g +{LOOT_HIT_XP_REWARD}xp", enemy.rect.midtop)
                    if effects:
                        effects.damage_number(projectile.damage, enemy.rect.midtop, critical=projectile.critical)
                        effects.ring(enemy.rect.center, radius=26, life=0.16, width=2)
                    if audio:
                        audio.play("hit")
                    projectile.register_hit(enemy)

                    if killed:
                        owner_id = id(enemy)
                        for bullet in enemy_bullets:
                            if getattr(bullet, "owner_id", None) == owner_id:
                                bullet.kill()
                        if audio:
                            audio.play("death")
                        if effects:
                            effects.ring(enemy.rect.center, radius=62, life=0.30, width=4)
                        kills += 1
                        if enemy.type == EnemyType.BOSS:
                            boss_killed = True
                            player.add_xp(BOSS_XP_REWARD)
                            player.add_gold(BOSS_GOLD_REWARD)
                        elif enemy.type == EnemyType.LOOT:
                            bonus_gold = LOOT_HIT_GOLD_REWARD * LOOT_ESCAPE_KILL_BONUS_MULTIPLIER
                            bonus_xp = LOOT_HIT_XP_REWARD * LOOT_ESCAPE_KILL_BONUS_MULTIPLIER
                            player.add_xp(bonus_xp)
                            player.add_gold(bonus_gold)
                            if effects:
                                effects.message(f"LOOT BONUS +{bonus_gold}g +{bonus_xp}xp", enemy.rect.midtop)
                        else:
                            xp = ENEMY_XP_REWARD * reward_multiplier
                            gold = ENEMY_GOLD_REWARD * reward_multiplier
                            if enemy.type == EnemyType.ELITE:
                                xp *= 5
                                gold *= 6
                            player.add_xp(xp)
                            player.add_gold(gold)
                    break

        for bullet in enemy_bullets:
            if bullet.alive and bullet.rect.colliderect(player.rect):
                if player.take_damage(bullet.damage):
                    bullet.kill()
                    if effects:
                        effects.ring(player.rect.center, radius=45, life=0.22, width=3)
                    if audio:
                        audio.play("hit")

        if self.player_contact_timer <= 0:
            for enemy in enemies:
                if enemy.alive and player.rect.colliderect(enemy.rect):
                    if enemy.type == EnemyType.BOSS:
                        damage = BOSS_DAMAGE
                    elif getattr(enemy, "leap_timer", 0) > 0:
                        damage = JUMPER_DAMAGE
                    else:
                        damage = ENEMY_DAMAGE
                    damage = int(damage * getattr(enemy, "damage_multiplier", 1.0))
                    if player.take_damage(damage):
                        self.player_contact_timer = ENEMY_CONTACT_COOLDOWN
                        if effects:
                            effects.ring(player.rect.center, radius=45, life=0.22, width=3)
                        if audio:
                            audio.play("hit")
                    break

        return kills, boss_killed
