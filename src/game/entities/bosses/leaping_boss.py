"""A heavy pursuer with committed, telegraphed leaps and aimed volleys."""

import math

import pygame

from game import config
from game.entities.bosses.basic_boss import BasicBoss
from game.entities.bullets.bullet import Bullet
from game.entities.enemies.enemy import Enemy
from game.visuals.animated_visual import AnimatedVisual


class LeapingBoss(BasicBoss):
    SPRITE_SIZE = 96
    DIRECTION_ROWS = {"down": 0, "right": 1, "left": 2, "up": 3}

    def __init__(self, level=1):
        super().__init__(level)
        self.speed = self.base_speed = 38
        self.state = "pursue"
        self.state_time = 0.0
        self.attack_index = 0
        self.jump_height = 0.0
        self.contact_disabled = False
        self.target = pygame.Vector2(self.x, self.y)
        self.jump_start = self.target.copy()
        self.pending_shots = []
        self.visual = AnimatedVisual(
            image_folder="enemies/golem", image_name="golem_animated.png",
            frame_cols=4, frame_rows=4,
            scale_x=self.SPRITE_SIZE, scale_y=self.SPRITE_SIZE,
            use_alpha=True,
            initial_state="idle", initial_facing="down",
            animations={
                f"{state}_{facing}": {
                    "row": row, "frames": frames, "speed": .3, "loop": True,
                }
                for facing, row in self.DIRECTION_ROWS.items()
                for state, frames in (("idle", [0]), ("walk", [0, 1, 2, 3]))
            },
        )

    def enter(self, state):
        self.state = state
        self.state_time = 0.0
        # Stop the walk cycle while charging, airborne or recovering. Keep the
        # same frame dimensions so rendering cannot change the collision bounds.
        self.visual.set_state("idle", reset=True)
        self._idle_time = 0.0
        self._pending_facing = None
        self._facing_time = 0.0

    def face_point(self, x, y):
        dx, dy = x - self.x, y - self.y
        if abs(dx) + abs(dy) < 1e-9:
            return
        if abs(dx) > abs(dy):
            facing = "right" if dx > 0 else "left"
        else:
            facing = "down" if dy > 0 else "up"
        self.visual.set_facing(facing)

    def update_animation(self, dt):
        if self.status_effects["ice"]["ice_timer"] <= 0:
            self.visual.update(dt)

    def apply_knockback(self, dir_x, dir_y, strength):
        if self.state != "jump":
            super().apply_knockback(dir_x, dir_y, strength * .15)

    def lock_jump_target(self, player, blockers):
        start = pygame.Vector2(self.x, self.y)
        delta = pygame.Vector2(player.x, player.y) - start
        if delta.length() > 180:
            delta.scale_to_length(180)
        # Trace the whole route so leaps never finish in, or tunnel through, walls.
        self.target = start.copy()
        steps = max(1, math.ceil(delta.length() / 4))
        for step in range(1, steps + 1):
            candidate = start + delta * (step / steps)
            self.x, self.y = candidate
            if self.collides_with_rects(blockers):
                break
            self.target = candidate
        self.x, self.y = start
        self.face_point(self.target.x, self.target.y)

    def volley(self, player, room):
        direction = pygame.Vector2(player.x - self.x, player.y - self.y)
        if not direction.length_squared():
            direction = pygame.Vector2(0, 1)
        direction = direction.normalize()
        for index in range(7):
            velocity = direction.rotate((index - 3) * 13) * (115 + (index % 2) * 15)
            self.pending_shots.append(Bullet(
                self.x, self.y, velocity.x, velocity.y,
                config.ENEMY_BULLET_COLOR, 4, self.damage, 1, 900,
                world_width=getattr(room, "viewport_width", config.SCREEN_WIDTH),
                world_height=getattr(room, "viewport_height", config.SCREEN_HEIGHT),
            ))

    def move(self, player, dt, blockers, entities, room=None):
        if self.is_dead():
            return
        if self.status_effects["ice"]["ice_timer"] > 0:
            self.jump_height = 0
            self.contact_disabled = False
            self.enter("recover")
            return
        self.state_time += dt
        if self.state == "pursue":
            Enemy.move(self, player, min(dt, .05), blockers, entities, room)
            if self.state_time >= 1.1:
                self.attack_index += 1
                if self.attack_index % 3 == 0:
                    self.face_point(player.x, player.y)
                    self.enter("spit_warning")
                else:
                    self.lock_jump_target(player, blockers)
                    self.enter("jump_warning")
        elif self.state == "jump_warning":
            if self.state_time >= .65:
                self.jump_start = pygame.Vector2(self.x, self.y)
                self.knockback_x = self.knockback_y = 0
                self.enter("jump")
                self.contact_disabled = True
        elif self.state == "jump":
            progress = min(1, self.state_time / .7)
            destination = self.jump_start.lerp(self.target, progress)
            delta = destination - pygame.Vector2(self.x, self.y)
            steps = max(1, math.ceil(delta.length() / 4))
            for _ in range(steps):
                self.move_by(delta.x / steps, delta.y / steps, blockers, entities)
            self.jump_height = math.sin(progress * math.pi) * 50
            if progress >= 1:
                self.jump_height = 0
                self.contact_disabled = False
                self.enter("recover")
        elif self.state == "spit_warning":
            if self.state_time >= .7:
                self.volley(player, room)
                self.enter("recover")
        elif self.state == "recover" and self.state_time >= .85:
            self.enter("pursue")

    def update(self, player, dt, blockers, entities, room=None):
        # Use the normal status system without the test boss's regeneration.
        self.pending_shots = []
        Enemy.update(self, player, dt, blockers, entities, room)
        return self.pending_shots

    def draw_ground_shadow(self, surface):
        pygame.draw.ellipse(surface, (38, 33, 43),
                            (round(self.x - 23), round(self.y + 18), 46, 12))
        if self.state in ("jump_warning", "jump"):
            pygame.draw.circle(surface, (210, 135, 72),
                               (round(self.target.x), round(self.target.y)), self.radius, 1)

    def draw(self, surface):
        Enemy.draw(self, surface, -round(self.jump_height))
        if self.state == "spit_warning":
            pygame.draw.circle(surface, (245, 143, 82),
                               (round(self.x), round(self.y + 12)), 5, 1)
