import pygame
from settings import (
    MAP_SIZE,
    PLAYER_SPEED,
    PLAYER_MAX_HEALTH,
    PLAYER_INVULNERABLE_TIME,
    DASH_SPEED,
    DASH_DURATION,
    DASH_COOLDOWN,
    BLUE,
)


class Player:
    def __init__(self):
        self.rect = pygame.Rect(MAP_SIZE // 2, MAP_SIZE // 2, 38, 38)
        self.color = BLUE

        self.base_speed = PLAYER_SPEED
        self.speed = PLAYER_SPEED
        self.velocity = pygame.Vector2(0, 0)
        self.move_direction = pygame.Vector2(0, 0)
        self.aim_direction = pygame.Vector2(1, 0)

        self.max_health = PLAYER_MAX_HEALTH
        self.health = self.max_health
        self.invulnerable_timer = 0.0

        self.level = 1
        self.xp = 0
        self.xp_to_next = 100
        self.gold = 0

        self.damage_bonus = 0
        self.fire_rate_multiplier = 1.0
        self.projectile_count = 1
        self.spread_degrees = 0
        self.projectile_speed_bonus = 0
        self.pierce = 0
        self.crit_chance = 0.0
        self.crit_multiplier = 1.75
        self.regen_on_room_clear = 10

        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.dash_direction = pygame.Vector2(1, 0)

        self.pending_level_ups = 0
        self.last_upgrade_text = ""
        self.perk_counts = {}
        self.perk_counts = {}

    def reset(self):
        self.rect.center = (MAP_SIZE // 2, MAP_SIZE // 2)
        self.velocity.update(0, 0)
        self.move_direction.update(0, 0)
        self.aim_direction.update(1, 0)

        self.speed = self.base_speed
        self.max_health = PLAYER_MAX_HEALTH
        self.health = self.max_health
        self.invulnerable_timer = 0.0

        self.level = 1
        self.xp = 0
        self.xp_to_next = 100
        self.gold = 0

        self.damage_bonus = 0
        self.fire_rate_multiplier = 1.0
        self.projectile_count = 1
        self.spread_degrees = 0
        self.projectile_speed_bonus = 0
        self.pierce = 0
        self.crit_chance = 0.0
        self.crit_multiplier = 1.75
        self.regen_on_room_clear = 10

        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.dash_direction.update(1, 0)

        self.pending_level_ups = 0
        self.last_upgrade_text = ""

    def build_power_score(self):
        damage_score = self.damage_bonus / 7
        fire_score = max(0, self.fire_rate_multiplier - 1.0) * 4
        projectile_score = max(0, self.projectile_count - 1) * 1.4
        pierce_score = self.pierce * 0.9
        crit_score = self.crit_chance * 8
        speed_score = max(0, self.speed - self.base_speed) / 35
        hp_score = max(0, self.max_health - PLAYER_MAX_HEALTH) / 35
        return max(0.0, damage_score + fire_score + projectile_score + pierce_score + crit_score + speed_score + hp_score)

    def move_to_hub_spawn(self):
        self.rect.center = (MAP_SIZE // 2, MAP_SIZE // 2 + 120)

    def move_to_room_spawn(self):
        self.rect.center = (MAP_SIZE // 2, MAP_SIZE // 2)

    def handle_movement_input(self):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)

        if keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_s]:
            direction.y += 1
        if keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_d]:
            direction.x += 1

        if direction.length_squared() > 0:
            direction = direction.normalize()

        self.move_direction = direction

        if self.dash_timer > 0:
            self.velocity = self.dash_direction * DASH_SPEED
        else:
            self.velocity = direction * self.speed

    def try_dash(self):
        if self.dash_cooldown_timer > 0 or self.dash_timer > 0:
            return False

        if self.move_direction.length_squared() > 0:
            self.dash_direction = self.move_direction.copy()
        else:
            self.dash_direction = self.aim_direction.copy()

        self.dash_timer = DASH_DURATION
        self.dash_cooldown_timer = DASH_COOLDOWN
        self.invulnerable_timer = max(self.invulnerable_timer, DASH_DURATION + 0.50)
        return True

    def update_aim(self, target_world_pos):
        direction = pygame.Vector2(
            target_world_pos.x - self.rect.centerx,
            target_world_pos.y - self.rect.centery,
        )
        if direction.length_squared() > 0:
            self.aim_direction = direction.normalize()

    def update(self, dt, solid_rects=None):
        if solid_rects is None:
            solid_rects = []

        if self.invulnerable_timer > 0:
            self.invulnerable_timer = max(0, self.invulnerable_timer - dt)
        if self.dash_timer > 0:
            self.dash_timer = max(0, self.dash_timer - dt)
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer = max(0, self.dash_cooldown_timer - dt)

        self.rect.x += round(self.velocity.x * dt)

        for solid in solid_rects:
            if self.rect.colliderect(solid):
                if self.velocity.x > 0:
                    self.rect.right = solid.left
                elif self.velocity.x < 0:
                    self.rect.left = solid.right

        self.rect.y += round(self.velocity.y * dt)

        for solid in solid_rects:
            if self.rect.colliderect(solid):
                if self.velocity.y > 0:
                    self.rect.bottom = solid.top
                elif self.velocity.y < 0:
                    self.rect.top = solid.bottom

        self.rect.clamp_ip(pygame.Rect(0, 0, MAP_SIZE, MAP_SIZE))

    def take_damage(self, amount):
        if self.invulnerable_timer > 0:
            return False
        self.health = max(0, self.health - amount)
        self.invulnerable_timer = PLAYER_INVULNERABLE_TIME
        return True

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def add_xp(self, amount):
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.28)
            self.pending_level_ups += 1
            leveled = True
        return leveled

    def consume_pending_level_up(self):
        if self.pending_level_ups <= 0:
            return False
        self.pending_level_ups -= 1
        return True

    def add_gold(self, amount):
        self.gold += amount

    def spend_gold(self, amount):
        if self.gold < amount:
            return False
        self.gold -= amount
        return True

    def is_dead(self):
        return self.health <= 0

    def draw(self, surface, camera):
        sr = camera.apply_rect(self.rect)
        cx, cy = sr.centerx, sr.centery
        x, y, w, h = sr.x, sr.y, sr.width, sr.height

        dashing = self.dash_timer > 0
        invuln  = self.invulnerable_timer > 0 and int(self.invulnerable_timer * 20) % 2 == 0

        if dashing:
            body_col  = (100, 220, 255)
            head_col  = (140, 235, 255)
            visor_col = (0,  180, 230)
            glow_col  = (80, 200, 255)
        elif invuln:
            body_col  = (120, 170, 255)
            head_col  = (150, 190, 255)
            visor_col = (60,  120, 220)
            glow_col  = (100, 150, 255)
        else:
            body_col  = (42,  110, 200)
            head_col  = (60,  150, 230)
            visor_col = (20,   60, 140)
            glow_col  = (80,  160, 255)

        # --- dash trail ---
        if dashing:
            trail_surf = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
            pygame.draw.rect(trail_surf, (*glow_col, 40), (4, 4, w + 12, h + 12), border_radius=8)
            surface.blit(trail_surf, (x - 10, y - 10))

        # --- legs ---
        leg_w, leg_h = w // 3 - 1, h // 3
        leg_y = y + h - 2
        pygame.draw.rect(surface, (30, 80, 160),
                         (x + 3, leg_y, leg_w, leg_h), border_radius=3)
        pygame.draw.rect(surface, (30, 80, 160),
                         (x + w - leg_w - 3, leg_y, leg_w, leg_h), border_radius=3)

        # --- body ---
        pygame.draw.rect(surface, body_col, sr, border_radius=6)

        # armour highlight on body top
        highlight = pygame.Rect(x + 3, y + 3, w - 6, h // 3)
        pygame.draw.rect(surface, (*head_col, 80),
                         highlight, border_radius=4)

        # chest detail line
        pygame.draw.line(surface, visor_col,
                         (cx - 4, cy - 2), (cx + 4, cy - 2), 2)

        # --- gun arm pointing toward aim ---
        aim = self.aim_direction
        arm_len  = 14
        gun_len  = 18
        arm_start = pygame.Vector2(cx, cy - 2)
        arm_end   = arm_start + aim * arm_len
        gun_end   = arm_end   + aim * gun_len

        pygame.draw.line(surface, body_col,
                         (round(arm_start.x), round(arm_start.y)),
                         (round(arm_end.x),   round(arm_end.y)), 5)

        # gun barrel
        perp = pygame.Vector2(-aim.y, aim.x)
        g1 = arm_end + perp * 2
        g2 = arm_end - perp * 2
        g3 = gun_end - perp * 2
        g4 = gun_end + perp * 2
        gun_pts = [(round(p.x), round(p.y)) for p in (g1, g2, g3, g4)]
        pygame.draw.polygon(surface, (25, 25, 40), gun_pts)
        pygame.draw.line(surface, (80, 80, 100),
                         (round(arm_end.x), round(arm_end.y)),
                         (round(gun_end.x), round(gun_end.y)), 1)

        # muzzle dot
        pygame.draw.circle(surface, (255, 220, 100),
                           (round(gun_end.x), round(gun_end.y)), 2)

        # --- head (sits above body) ---
        head_w = w - 4
        head_h = h // 2 - 2
        head_x = x + 2
        head_y = y - head_h + 4
        head_rect = pygame.Rect(head_x, head_y, head_w, head_h)
        pygame.draw.rect(surface, head_col, head_rect, border_radius=5)

        # visor bar
        visor_rect = pygame.Rect(head_x + 4, head_y + head_h // 3, head_w - 8, head_h // 3)
        pygame.draw.rect(surface, visor_col, visor_rect, border_radius=2)

        # visor glow dots (eyes)
        eye_y = visor_rect.centery
        pygame.draw.circle(surface, (120, 220, 255), (head_x + 8,  eye_y), 3)
        pygame.draw.circle(surface, (120, 220, 255), (head_x + head_w - 8, eye_y), 3)

        # head top shine
        pygame.draw.rect(surface, (*head_col, 120),
                         pygame.Rect(head_x + 3, head_y + 2, head_w - 6, 3),
                         border_radius=2)

        # --- invuln blink ring ---
        if invuln:
            pygame.draw.circle(surface, (*glow_col, 90),
                               (cx, cy), w // 2 + 6, 2)
