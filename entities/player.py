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
        self.invulnerable_timer = max(self.invulnerable_timer, DASH_DURATION + 0.10)
        return True

    def update_aim(self, target_world_pos):
        direction = pygame.Vector2(
            target_world_pos.x - self.rect.centerx,
            target_world_pos.y - self.rect.centery,
        )
        if direction.length_squared() > 0:
            self.aim_direction = direction.normalize()

    def update(self, dt):
        if self.invulnerable_timer > 0:
            self.invulnerable_timer = max(0, self.invulnerable_timer - dt)
        if self.dash_timer > 0:
            self.dash_timer = max(0, self.dash_timer - dt)
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer = max(0, self.dash_cooldown_timer - dt)

        self.rect.x += round(self.velocity.x * dt)
        self.rect.y += round(self.velocity.y * dt)
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
        screen_rect = camera.apply_rect(self.rect)

        if self.dash_timer > 0:
            color = (120, 230, 255)
        elif self.invulnerable_timer > 0 and int(self.invulnerable_timer * 20) % 2 == 0:
            color = (125, 180, 255)
        else:
            color = self.color

        pygame.draw.rect(surface, color, screen_rect, border_radius=6)

        center = pygame.Vector2(screen_rect.center)
        end = center + self.aim_direction * 38
        pygame.draw.line(surface, (15, 15, 15), center, end, 3)
