"""Enemigo que intenta disparar al jugador."""

import math

from game import config
from game.entities.bullets.bullet import create_normal_shot
from game.entities.enemies.enemy import Enemy
from game.visuals.animated_visual import AnimatedVisual


class ShooterEnemy(Enemy):
    def __init__(self, position, level=1, with_visual=True):
        health = int(config.ENEMY_MAX_HEALTH * (1.12 ** (level-1)))
        #damage = int(config.ENEMY_DAMAGE * (1.08 ** (level - 1)))
        #speed = config.ENEMY_SPEED * (1.02 * (level - 1))

        super().__init__(
            position=position,
            speed=config.ENEMY_SPEED,
            max_health=health,
            radius=config.ENEMY_RADIUS,
            color=config.ENEMY_COLOR,
            damage=config.ENEMY_DAMAGE,
            score_value=10,
        )

        self.shoot_cooldown = config.SHOOTER_ENEMY_FIRE_COOLDOWN
        self.bullet_speed = config.SHOOTER_ENEMY_BULLET_SPEED
        self.shoot_timer = 0.0
        self.preferred_distance = 100
        self.shoot_distance = config.SHOOTER_ENEMY_SHOOT_DISTANCE
        self.bullet_element = None

        if with_visual:
            self.visual = AnimatedVisual(
                image_folder="enemies/rat",
                image_name="rat_animated.png",
                frame_cols=4,
                frame_rows=4,
                scale_x = 32,
                scale_y = 32,
                use_alpha=True,
                initial_state="idle",
                initial_facing="down",
                animations={
                    "idle_right": {"row": 0, "frames": [0], "speed": 0.25, "loop": True},
                    "walk_right": {"row": 0, "frames": [0, 1, 2, 3], "speed": 0.25, "loop": True},
    
                    "idle_left": {"row": 1, "frames": [0], "speed": 0.25, "loop": True},
                    "walk_left": {"row": 1, "frames": [0, 1, 2, 3], "speed": 0.25, "loop": True},
    
                    "idle_down": {"row": 2, "frames": [0], "speed": 0.25, "loop": True},
                    "walk_down": {"row": 2, "frames": [0, 1, 2, 3], "speed": 0.25, "loop": True},
    
                    "idle_up": {"row": 3, "frames": [0], "speed": 0.25, "loop": True},
                    "walk_up": {"row": 3, "frames": [0, 1, 2, 3], "speed": 0.25, "loop": True},
                },
            )


    def move(self, player, dt, blockers, entities, room=None):
        self._movement_dt = dt
        diff_x = player.x - self.x
        diff_y = player.y - self.y
        distance = math.hypot(diff_x, diff_y)

        if distance <= 0:
            self.visual.set_state("idle")
            return

        visible = self.has_clear_path(self.x, self.y, player.x, player.y, blockers)
        if distance > self.preferred_distance or not visible:
            move_x, move_y = self.get_path_movement(player, dt, room, blockers)
        elif distance < self.preferred_distance - 50:
            # Retreat only into free space; when backed into a wall, try an
            # oblique escape that still increases the distance from the player.
            angle = math.atan2(-diff_y, -diff_x)
            move_x = move_y = 0
            step = max(0, self.get_movement_speed() * dt)
            lookahead = max(self.radius * 2, step)
            for turn in (0, math.pi / 4, -math.pi / 4, math.pi / 2, -math.pi / 2):
                dx, dy = math.cos(angle + turn), math.sin(angle + turn)
                if self.has_clear_path(self.x, self.y, self.x + dx * lookahead,
                                       self.y + dy * lookahead, blockers):
                    move_x, move_y = dx * step, dy * step
                    break
        else:
            self.visual.set_state("idle")
            return

        old_x = self.x
        old_y = self.y

        self.move_safely(move_x, move_y, blockers, entities)

        real_move_x = self.x - old_x
        real_move_y = self.y - old_y

        self.update_visual_from_movement(real_move_x, real_move_y)

    def shoot(self, player):
        diff_x = player.x - self.x
        diff_y = player.y - self.y
        distance = math.hypot(diff_x, diff_y)

        if distance >= self.preferred_distance or self.shoot_timer > 0:
            return []

        if distance <= 0:
            return []

        vel_x = (diff_x / distance) * self.bullet_speed
        vel_y = (diff_y / distance) * self.bullet_speed


        effect_data = {}
        if self.bullet_element is not None:
            effect_data = self.element_stats[self.bullet_element].copy()
        shot, rate = create_normal_shot(self.x, self.y, vel_x, vel_y, self.shoot_distance, self.bullet_element, effect_data)
        self.shoot_timer = self.shoot_cooldown * rate
        for bullet in shot:
            bullet.color = config.ENEMY_BULLET_COLOR

        return shot

    def update(self, player, dt, blockers, entities,  room=None):
        super().update(player, dt, blockers, entities, room)
        self.shoot_timer = max(0, self.shoot_timer - dt)
        return self.shoot(player)
