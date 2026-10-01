from game.systems.collision_shapes import circle_overlaps_entity
import math
import random

import pygame

from game.systems.effect_handlers import apply_poison_data
from game.systems.toxic_smoke import smoke_sprite


TRAIL_WIDTH_MULTIPLIER = 1.2
BUBBLE_SPAWN_INTERVAL = 0.16
BUBBLE_MIN_RADIUS = 2
BUBBLE_MAX_RADIUS = 4
BUBBLE_RISE_SPEED = 9
BUBBLE_LIFETIME = 0.65


class ToxicTrail:
    """Rastro dañino que se deja durante Sobrecarga Tóxica."""

    def __init__(self, combo_data, effect_data):
        self.duration = combo_data["trail_duration"]
        self.radius = combo_data["trail_radius"]
        self.segment_spacing = combo_data["trail_segment_spacing"]
        self.tick_time = combo_data["trail_tick_time"]
        self.stacks_per_tick = combo_data["trail_stacks_per_tick"]
        self.poison_data = effect_data["poison"]
        self.ice_poison_data = effect_data["combos"]["ice_poison"]

        self.segments = []
        self.bubbles = []
        self.last_position = None
        self.path_id = 0
        self.tick_timer = 0
        self.bubble_timer = 0
        self.smoke_time = 0

    @property
    def finished(self):
        return not self.segments and not self.bubbles

    def update(self, dt, enemies, player=None):
        self.smoke_time += dt
        if player is not None:
            self.leave_segments(player.x, player.y)
        else:
            self.last_position = None

        for segment in self.segments:
            segment["age"] += dt

        self.segments = [
            segment
            for segment in self.segments
            if segment["age"] < self.duration
        ]

        self.update_bubbles(dt)

        if self.segments:
            self.tick_timer -= dt
            if self.tick_timer <= 0:
                self.damage_enemies(enemies)
                self.tick_timer = self.tick_time

    def update_bubbles(self, dt):
        for bubble in self.bubbles:
            bubble["age"] += dt

        self.bubbles = [
            bubble
            for bubble in self.bubbles
            if bubble["age"] < bubble["lifetime"]
        ]

        if not self.segments:
            return

        self.bubble_timer += dt
        while self.bubble_timer >= BUBBLE_SPAWN_INTERVAL:
            self.bubble_timer -= BUBBLE_SPAWN_INTERVAL
            index = random.randrange(len(self.segments))
            segment = self.segments[index]
            previous = self.segments[max(0, index - 1)]
            if previous["path_id"] != segment["path_id"]:
                previous = segment
            dx = segment["x"] - previous["x"]
            dy = segment["y"] - previous["y"]
            distance = math.hypot(dx, dy)
            normal_x, normal_y = (-dy / distance, dx / distance) if distance else (0, 1)
            along = random.random()
            across = random.uniform(-0.75, 0.75) * self.radius * TRAIL_WIDTH_MULTIPLIER
            self.bubbles.append(
                {
                    "x": previous["x"] + dx * along + normal_x * across,
                    "y": previous["y"] + dy * along + normal_y * across,
                    "age": 0,
                    "lifetime": BUBBLE_LIFETIME,
                    "radius": random.randint(BUBBLE_MIN_RADIUS, BUBBLE_MAX_RADIUS),
                    "drift_x": random.uniform(-3, 3),
                }
            )

    def leave_segments(self, x, y):
        if self.last_position is None:
            self.path_id += 1
            self.last_position = (x, y)
            self.add_segment(x, y)
            return

        last_x, last_y = self.last_position
        distance = math.hypot(x - last_x, y - last_y)

        while distance >= self.segment_spacing:
            direction_x = (x - last_x) / distance
            direction_y = (y - last_y) / distance
            last_x += direction_x * self.segment_spacing
            last_y += direction_y * self.segment_spacing
            self.add_segment(last_x, last_y)
            distance = math.hypot(x - last_x, y - last_y)

        self.last_position = (last_x, last_y)

    def add_segment(self, x, y):
        self.segments.append(
            {"x": x, "y": y, "age": 0, "path_id": self.path_id}
        )

    def damage_enemies(self, enemies):
        for enemy in enemies:
            if enemy.is_dead():
                continue

            for segment in self.segments:
                if circle_overlaps_entity(segment["x"], segment["y"], self.radius, enemy):
                    for _ in range(self.stacks_per_tick):
                        apply_poison_data(
                            enemy,
                            self.poison_data,
                            self.ice_poison_data,
                        )
                    break

    def smoke_sprite(self, variant):
        size = max(12, int(self.radius * TRAIL_WIDTH_MULTIPLIER * 3.5))
        return smoke_sprite(size, variant)

    def draw_smoke(self, surface):
        spacing = max(1, self.radius * 0.35)
        for index, segment in enumerate(self.segments):
            previous = self.segments[max(0, index - 1)]
            if previous["path_id"] != segment["path_id"]:
                previous = segment
            dx = segment["x"] - previous["x"]
            dy = segment["y"] - previous["y"]
            steps = max(1, math.ceil(math.hypot(dx, dy) / spacing))
            for step in range(1, steps + 1):
                fraction = step / steps
                x = previous["x"] + dx * fraction
                y = previous["y"] + dy * fraction
                age = previous["age"] + (segment["age"] - previous["age"]) * fraction
                fade = min(1, max(0, (self.duration - age) / 0.8))
                # World-anchored variation stays stable as old samples expire.
                phase = x * 0.035 + y * 0.027
                variant = int(phase) % 8
                sprite = self.smoke_sprite(variant)
                if fade < 1:
                    sprite = sprite.copy()
                    sprite.fill((255, 255, 255, int(255 * fade)), special_flags=pygame.BLEND_RGBA_MULT)
                drift_x = math.sin(phase + self.smoke_time * 0.9) * self.radius * 0.16
                drift_y = math.sin(phase * 1.3 - self.smoke_time * 0.7) * self.radius * 0.20
                position = (round(x + drift_x - sprite.get_width() / 2),
                            round(y + drift_y - sprite.get_height() / 2))
                # Merge density instead of stacking opacity into separate discs.
                surface.blit(sprite, position, special_flags=pygame.BLEND_RGBA_MAX)

    def draw(self, surface):
        trail_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        self.draw_smoke(trail_surface)
        surface.blit(trail_surface, (0, 0))
        trail_surface.fill((0, 0, 0, 0))
        for bubble in self.bubbles:
            life_ratio = 1 - bubble["age"] / bubble["lifetime"]
            radius = max(1, int(bubble["radius"] * (0.65 + life_ratio * 0.35)))
            bubble_x = int(bubble["x"] + bubble["drift_x"] * bubble["age"])
            bubble_y = int(bubble["y"] - BUBBLE_RISE_SPEED * bubble["age"])
            alpha = int(150 * life_ratio)

            pygame.draw.circle(
                trail_surface,
                (190, 100, 225, alpha),
                (bubble_x, bubble_y),
                radius,
            )
            pygame.draw.circle(
                trail_surface,
                (225, 145, 245, int(alpha * 0.7)),
                (bubble_x - 1, bubble_y - 1),
                max(1, radius // 2),
            )

        surface.blit(trail_surface, (0, 0))
