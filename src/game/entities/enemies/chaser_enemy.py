"""Enemigo basico que solo persigue al jugador."""

import math
import random

from game import config
from game.entities.enemies.enemy import Enemy


class ChaserEnemy(Enemy):
    def __init__(self, position, level=1):
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


        self.detection_distance = 300

        self.random_dir_x = 0
        self.random_dir_y = 0
        self.random_move_timer = 0
        self.random_move_interval = 1.5

    def choose_random_direction(self):
        self.random_dir_x = random.uniform(-1, 1)
        self.random_dir_y = random.uniform(-1, 1)

        length = math.hypot(self.random_dir_x, self.random_dir_y)

        if length > 0:
            self.random_dir_x /= length
            self.random_dir_y /= length


    def move(self, player, dt, blockers, entities, room=None):
        self._movement_dt = dt
        move_x, move_y = self.get_requested_movement(player, dt, blockers, room)
        old_x, old_y = self.x, self.y
        other_entities = [entity for entity in entities if entity is not self]
        self.move_safely(move_x, move_y, blockers, other_entities)
        self.update_visual_from_movement(self.x - old_x, self.y - old_y)

    def get_requested_movement(self, player, dt, blockers, room=None):
        """Evaluate steering once; callers decide how to apply collisions."""
        self.navigator.remaining_distance = math.inf
        diff_x = player.x - self.x
        diff_y = player.y - self.y
        distance = math.hypot(diff_x, diff_y)

        if distance <= 0:
            return 0, 0

        movement_speed = self.get_movement_speed()

        if distance <= self.detection_distance and not player.invulnerability_timer > 0:
            move_x, move_y = self.get_path_movement(player, dt, room, blockers)
        else:
            self.random_move_timer -= dt

            if self.random_move_timer <= 0:
                self.choose_random_direction()
                self.random_move_timer = self.random_move_interval

            lookahead = max(self.radius * 2, movement_speed * max(dt, 0.25))
            if not self.has_clear_path(self.x, self.y,
                                       self.x + self.random_dir_x * lookahead,
                                       self.y + self.random_dir_y * lookahead, blockers):
                angle = math.atan2(self.random_dir_y, self.random_dir_x)
                for turn in (math.pi / 2, -math.pi / 2, math.pi):
                    dx, dy = math.cos(angle + turn), math.sin(angle + turn)
                    if self.has_clear_path(self.x, self.y, self.x + dx * lookahead,
                                           self.y + dy * lookahead, blockers):
                        self.random_dir_x, self.random_dir_y = dx, dy
                        break
                else:
                    return 0, 0
            move_x = self.random_dir_x * movement_speed * dt
            move_y = self.random_dir_y * movement_speed * dt

        return move_x, move_y
