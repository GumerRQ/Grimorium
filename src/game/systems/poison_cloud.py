from game.systems.collision_shapes import circle_overlaps_entity
import math
import random
import pygame

from game.systems.lava_drop import LavaDrop
from game.visuals.poison_storm import cloud_sprite


class PoisonCloud:
    def __init__(
        self,
        x,
        y,
        combo_data,
        poison_data,
        rain_origin_y=None,
    ):
        self.x = x
        self.y = y
        self.rain_origin_y = y if rain_origin_y is None else rain_origin_y
        self.spawn_y = self.rain_origin_y
        self.rise_duration = combo_data["cloud_rise_duration"]
        self.rise_timer = 0

        self.radius = combo_data["cloud_radius"]
        self.duration = combo_data["cloud_duration"]
        self.tick_time = combo_data["tick_time"]
        self.tick_timer = 0

        self.stacks_per_tick = combo_data["stacks_per_tick"]
        self.poison_data = poison_data

        self.ignited_duration_multiplier = combo_data[
            "ignited_duration_multiplier"
        ]
        self.lava_drop_interval = combo_data["lava_drop_interval"]
        self.lava_drop_fall_duration = combo_data[
            "lava_drop_fall_duration"
        ]
        self.lava_drop_radius = combo_data["lava_drop_radius"]

        self.is_ignited = False
        self.fire_data = None
        self.lava_drop_timer = 0

        self.expired = False

    def update(self, dt, enemies):
        self.rise_timer = min(
            self.rise_duration,
            self.rise_timer + dt,
        )

        duration_multiplier = 1
        if self.is_ignited:
            duration_multiplier = self.ignited_duration_multiplier

        self.duration -= dt * duration_multiplier
        self.tick_timer -= dt

        lava_drops = []

        if self.is_ignited:
            self.lava_drop_timer -= dt
            while self.lava_drop_timer <= 0:
                lava_drops.append(self.create_lava_drop())
                self.lava_drop_timer += self.lava_drop_interval

        if self.duration <= 0:
            self.expired = True
            return lava_drops

        if self.tick_timer <= 0:
            self.apply_poison(enemies)
            self.tick_timer = self.tick_time

        return lava_drops

    def contains_entity(self, entity):
        distance = math.hypot(
            entity.x - self.x,
            entity.y - self.get_display_y(),
        )
        return distance <= self.radius + getattr(entity, "radius", 0)

    def get_rise_progress(self):
        if self.rise_duration <= 0:
            return 1

        return self.rise_timer / self.rise_duration

    def get_display_y(self):
        progress = self.get_rise_progress()
        return self.spawn_y + (self.y - self.spawn_y) * progress

    def ignite(self, fire_data):
        if (
            self.is_ignited
            or self.lava_drop_interval <= 0
            or fire_data is None
        ):
            return

        self.is_ignited = True
        self.fire_data = fire_data.copy()
        self.lava_drop_timer = 0

    def create_lava_drop(self):
        angle = random.uniform(0, math.tau)
        distance = math.sqrt(random.uniform(0, 1)) * self.radius
        target_x = self.x + math.cos(angle) * distance
        target_y = self.rain_origin_y + random.uniform(0, self.radius * 0.25)

        return LavaDrop(
            x=target_x,
            start_y=self.get_display_y() + self.radius * 0.25,
            target_y=target_y,
            radius=self.lava_drop_radius,
            fall_duration=self.lava_drop_fall_duration,
            fire_data=self.fire_data,
        )

    def apply_poison(self, enemies):
        for enemy in enemies:
            if enemy.is_dead():
                continue


            if circle_overlaps_entity(self.x, self.y, self.radius, enemy):
                poison = enemy.status_effects["poison"]

                poison["max_stacks"] = self.poison_data["max_stacks"]
                poison["damage_taken_per_stack"] = self.poison_data["damage_taken_per_stack"]

                poison["stacks"] = min(
                    poison["stacks"] + self.stacks_per_tick,
                    poison["max_stacks"],
                )

                if getattr(enemy, "is_boss", False):
                    poison["timer"] = self.poison_data["boss_duration"]

    def draw(self, surface):
        rise_progress = self.get_rise_progress()
        scale = 0.35 + 0.65 * rise_progress
        display_y = self.get_display_y()

        cloud_width = max(1, int(self.radius * 2.5 * scale))
        cloud_height = max(1, int(self.radius * 1.2 * scale))
        shadow_width = max(1, int(self.radius * 2.2 * scale))
        shadow_height = max(2, int(self.radius * 0.28 * scale))

        shadow_surface = pygame.Surface(
            (shadow_width, shadow_height),
            pygame.SRCALPHA,
        )
        pygame.draw.ellipse(
            shadow_surface,
            (45, 25, 55, 60),
            (0, 0, shadow_width, shadow_height),
        )
        surface.blit(
            shadow_surface,
            (
                int(self.x - shadow_width / 2),
                int(self.rain_origin_y - shadow_height / 2),
            ),
        )

        frame = int(-self.duration * 8 + self.x * 0.03) % 24
        cloud_surface = cloud_sprite(cloud_width, cloud_height, self.is_ignited, frame)

        surface.blit(
            cloud_surface,
            (
                int(self.x - cloud_width / 2),
                int(display_y - cloud_height / 2),
            ),
        )
