from game.systems.impacts import Impact, apply_impact
from game.systems.collision_shapes import circle_overlaps_entity
import math
import random
import pygame

from game.systems.toxic_smoke import SMOKE_PIXEL_SIZE, smoke_sprite


class ToxicOverload:
    def __init__(self, player, combo_data):
        self.player = player

        self.radius = combo_data["radius"]
        self.drain_per_second = combo_data["drain_per_second"]
        #self.drain_per_second = max(0.12, combo_data["drain_per_second"])
        self.speed_multiplier = combo_data["speed_multiplier"]
        self.tick_time = combo_data["tick_time"]
        self.tick_damage = combo_data["tick_damage"]
        self.charge_decay_factor = combo_data["charge_decay_factor"]

        self.charge = 1.0
        self.max_charge = 1.0
        self.tick_timer = 0
        self.fed_enemies = set()
        self.finished = False
        self.smoke_time = 0

    def update(self, dt, enemies):
        if self.finished:
            return

        self.smoke_time += dt
        self.feed_new_enemies(enemies)

        self.charge = max(0, self.charge - self.drain_per_second * dt)

        self.tick_timer -= dt
        if self.tick_timer <= 0:
            self.damage_enemies(enemies)
            self.tick_timer = self.tick_time

        if self.charge <= 0:
            self.finished = True

    def feed_new_enemies(self, enemies):
        for enemy in enemies:
            if enemy.is_dead() or enemy in self.fed_enemies:
                continue


            if circle_overlaps_entity(self.player.x, self.player.y, self.radius, enemy):
                max_charge = (
                    self.charge_decay_factor
                    ** len(self.fed_enemies)
                )

                self.max_charge = max_charge
                self.charge = self.max_charge
                self.fed_enemies.add(enemy)

    def damage_enemies(self, enemies):
        for enemy in enemies:
            if enemy.is_dead():
                continue


            if circle_overlaps_entity(self.player.x, self.player.y, self.radius, enemy):
                apply_impact(enemy, Impact(self.tick_damage, kind='effect', source=self))

    def draw(self, surface):
        if self.finished:
            return

        center = (int(self.player.x), int(self.player.y))

        # The same broad clouds as the trail, slowly moving around the player.
        smoke_size = max(12, round(self.radius * 2.6))
        for variant, direction in ((2, 1), (5, -1)):
            cloud = smoke_sprite(smoke_size, variant)
            angle = direction * (self.smoke_time * 7 + variant * 31)
            cloud = pygame.transform.rotate(cloud, angle)
            cloud_size = (cloud.get_width(), max(1, round(cloud.get_height() * 0.8)))
            cloud = pygame.transform.scale(cloud, (
                max(1, cloud_size[0] // SMOKE_PIXEL_SIZE),
                max(1, cloud_size[1] // SMOKE_PIXEL_SIZE),
            ))
            cloud = pygame.transform.scale(cloud, cloud_size)
            cloud.set_alpha(180)
            drift = pygame.Vector2(
                math.sin(self.smoke_time * 0.8 + variant) * self.radius * 0.06,
                math.cos(self.smoke_time * 0.6 + variant) * self.radius * 0.04,
            )
            surface.blit(cloud, cloud.get_rect(center=(
                round(center[0] + drift.x), round(center[1] + drift.y)
            )))

        field_width = max(1, round(self.radius * 2))
        field_height = max(1, round(self.radius * 1.6))
        field_surface = pygame.Surface(
            (field_width, field_height),
            pygame.SRCALPHA,
        )
        self.draw_electric_sparks(field_surface)

        surface.blit(
            field_surface,
            (center[0] - self.radius, center[1] - field_height // 2),
        )

        bar_width = 34
        bar_height = 4
        bar_x = center[0] - bar_width // 2
        bar_y = center[1] - self.player.radius - 12

        pygame.draw.rect(
            surface,
            (35, 35, 35),
            (bar_x, bar_y, bar_width, bar_height),
        )

        pygame.draw.rect(
            surface,
            (190, 120, 220),
            (
                bar_x,
                bar_y,
                int(bar_width * (self.charge / self.max_charge)),
                bar_height,
            ),
        )

        pygame.draw.rect(
            surface,
            (255, 235, 135),
            (bar_x, bar_y, bar_width, bar_height),
            1,
        )

    def draw_electric_sparks(self, field_surface):
        # Hold each discharge briefly, then replace its jagged branches.
        frame = int(self.smoke_time / 0.09)
        rng = random.Random(frame)
        pulse = 0.72 + 0.28 * (1 - (self.smoke_time / 0.09) % 1)
        center = pygame.Vector2(field_surface.get_size()) / 2
        radius_x = field_surface.get_width() / 2
        radius_y = field_surface.get_height() / 2
        bolts = []
        tips = []

        def jagged_points(start, end, steps, amplitude):
            direction = end - start
            if direction.length_squared() < 0.001:
                return [start, end]
            normal = pygame.Vector2(-direction.y, direction.x).normalize()
            points = [start]
            for index in range(1, steps):
                fraction = index / steps
                offset = (-1 if index % 2 else 1) * rng.uniform(0.35, 1) * amplitude
                points.append(start.lerp(end, fraction) + normal * offset)
            points.append(end)
            return points

        bolt_count = rng.randint(3, 5)
        rotation = rng.uniform(0, math.tau)
        for index in range(bolt_count):
            angle = rotation + index * math.tau / bolt_count + rng.uniform(-0.25, 0.25)
            radial = pygame.Vector2(math.cos(angle) * radius_x, math.sin(angle) * radius_y)
            start = center + radial * rng.uniform(0.08, 0.18)
            end = center + radial * rng.uniform(0.72, 0.86)
            points = jagged_points(start, end, rng.randint(4, 6), self.radius * 0.055)
            bolts.append((points, False))
            tips.append(end)

            branch_points = range(2, len(points) - 2)
            for branch_index in rng.sample(branch_points, min(2, len(branch_points))):
                branch_start = points[branch_index]
                branch_angle = angle + rng.choice((-1, 1)) * rng.uniform(0.5, 1.1)
                branch_length = self.radius * rng.uniform(0.16, 0.28)
                branch_end = branch_start + pygame.Vector2(
                    math.cos(branch_angle), math.sin(branch_angle) * 0.8
                ) * branch_length
                branch = jagged_points(branch_start, branch_end, 2, self.radius * 0.025)
                bolts.append((branch, True))

        # Separate glow from the cores so crossing branches stay bright.
        glow = pygame.Surface(field_surface.get_size(), pygame.SRCALPHA)
        for points, branch in bolts:
            pygame.draw.lines(glow, (255, 175, 35, int(32 * pulse)), False, points, 5 if branch else 9)
        for points, branch in bolts:
            pygame.draw.lines(glow, (255, 205, 55, int(75 * pulse)), False, points, 3 if branch else 5)
        field_surface.blit(glow, (0, 0))
        for points, branch in bolts:
            if not branch:
                pygame.draw.lines(field_surface, (255, 218, 70, int(220 * pulse)), False, points, 3)
        for points, branch in bolts:
            pygame.draw.lines(field_surface, (255, 252, 220, int((215 if branch else 255) * pulse)), False, points, 1)
        for tip in tips:
            pygame.draw.line(field_surface, (255, 249, 200, int(220 * pulse)), tip - (2, 0), tip + (2, 0))
            pygame.draw.line(field_surface, (255, 249, 200, int(220 * pulse)), tip - (0, 2), tip + (0, 2))
