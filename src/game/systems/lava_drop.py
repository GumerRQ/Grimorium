from game.systems.collision_shapes import circle_overlaps_entity
import math

import pygame

from game.systems.effect_handlers import apply_fire_data
from game.visuals.poison_storm import draw_lava_rain_drop


class LavaDrop:
    def __init__(
        self,
        x,
        start_y,
        target_y,
        radius,
        fall_duration,
        fire_data,
    ):
        self.x = x
        self.start_y = start_y
        self.target_y = target_y
        self.radius = radius
        self.fall_duration = fall_duration
        self.fire_data = fire_data

        self.timer = 0
        self.y = start_y
        self.finished = False

    def update(self, dt, enemies):
        self.timer += dt
        progress = min(1, self.timer / self.fall_duration)
        self.y = self.start_y + (self.target_y - self.start_y) * progress

        if progress < 1:
            return

        for enemy in enemies:
            if enemy.is_dead():
                continue

            if circle_overlaps_entity(self.x, self.y, self.radius, enemy):
                apply_fire_data(enemy, self.fire_data)

        self.finished = True

    def draw(self, surface):
        if self.finished:
            return

        draw_lava_rain_drop(surface, self.x, self.y, self.radius, self.timer,
                            progress=min(1, self.timer / self.fall_duration))
