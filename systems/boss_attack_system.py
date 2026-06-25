import pygame
import math
from settings import BOSS_DAMAGE, ENEMY_BULLET_DAMAGE
from entities.enemy import Enemy, EnemyType
from entities.enemy_bullet import EnemyBullet
from systems.world_utils import rotate_vector

class BossAttackSystem:
    def handle_action(self, action, enemies, enemy_bullets, effects=None, audio=None, player=None):
        """
        تعديل جوهري: إضافة player لمعرفة المسافة واتخاذ قرار ديناميكي.
        """
        boss_pos = pygame.Vector2(action["x"], action["y"])
        player_pos = pygame.Vector2(player.rect.center) if player is not None else boss_pos + base * 400
        distance = boss_pos.distance_to(player_pos)
        
        base = action["direction"]
        phase = action.get("phase", 1)
        threat = max(1.0, action.get("difficulty", 1.0))
        damage_multiplier = action.get("damage_multiplier", 1.0)

        # قرار ديناميكي:
        if distance < 250:
            # اللاعب قريب: هجوم النطحة/الاندفاع
            self._boss_dash_attack(action, player_pos, phase, threat, enemies, effects)
        elif distance > 500:
            # اللاعب بعيد: هجوم الجاذبية
            self._boss_gravity_well(action, phase, threat, damage_multiplier, enemy_bullets, effects)
        else:
            # المسافة متوسطة: الهجمات الكلاسيكية (مع دمج الكومبو)
            if action["type"] == "boss_cone":
                self._boss_burst_cone(action, base, phase, threat, damage_multiplier, enemy_bullets)
            elif action["type"] == "boss_ring":
                self._boss_ring(action, phase, threat, damage_multiplier, enemy_bullets, effects, audio)
            else:
                self._boss_summon_leap(action, base, phase, threat, enemies, effects)

    def _boss_burst_cone(self, action, base, phase, threat, damage_multiplier, enemy_bullets, count=3):
        # هجوم كومبو: دفعات متتالية تزداد سرعتها
        for i in range(count):
            offset = (i - 1) * 15
            speed = 400 + (i * 100)
            enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(base, offset), 
                                 int(15 * damage_multiplier), speed=speed))

    def _boss_gravity_well(self, action, phase, threat, damage_multiplier, enemy_bullets, effects):
        # سحب وتدوير كور حول البوس
        for angle in range(0, 360, 45):
            vec = rotate_vector(pygame.Vector2(1, 0), angle)
            enemy_bullets.append(EnemyBullet(action["x"], action["y"], vec, 
                                 int(20 * damage_multiplier), speed=50))
        if effects:
            effects.ring((action["x"], action["y"]), radius=200, life=0.6, width=10)

    def _boss_dash_attack(self, action, player_pos, phase, threat, enemies, effects):
        # نطح اللاعب
        for enemy in enemies:
            if enemy.type == EnemyType.BOSS:
                direction = (player_pos - pygame.Vector2(action["x"], action["y"])).normalize()
                enemy.leap_velocity = direction * (1200 * phase)
                enemy.leap_timer = 0.5
                break
        if effects:
            effects.ring((action["x"], action["y"]), radius=80, life=0.3, width=20)

    def _boss_ring(self, action, phase, threat, damage_multiplier, enemy_bullets, effects, audio):
        step = 20
        for angle in range(0, 360, step):
            enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(pygame.Vector2(1, 0), angle), 
                                 int(14 * damage_multiplier), speed=300 + phase*50))
        if audio: audio.play("boss")

    def _boss_summon_leap(self, action, base, phase, threat, enemies, effects):
        boss_pos = pygame.Vector2(action["x"], action["y"])
        pos = boss_pos + base * 100
        enemies.append(Enemy(pos.x, pos.y, EnemyType.CHASER, difficulty=threat))
