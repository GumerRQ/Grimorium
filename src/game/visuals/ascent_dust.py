"""Merging dust puffs around the arriving room, independent of combat RNG."""
import random

import pygame


class AscentDust:
    def __init__(self, room_layer, pivot, duration):
        self.field = pygame.Surface(room_layer.get_size())
        self.particles = []
        self.end_time = duration
        self.kernel = pygame.Surface((32, 32))
        for y in range(32):
            for x in range(32):
                radius = ((x - 15.5) ** 2 + (y - 15.5) ** 2) / 15.5 ** 2
                value = round(210 * max(0, 1 - radius) ** 3)
                self.kernel.set_at((x, y), (value,) * 3)
        mask = pygame.mask.from_surface(room_layer)
        outline = mask.outline(3)
        if not outline:
            return
        rng = random.Random(731)
        width, height = mask.get_size()
        def solid(x, y):
            return mask.get_at((x, y)) if 0 <= x < width and 0 <= y < height else 0
        for i in range(240):
            x, y = rng.choice(outline)
            normal = pygame.Vector2(solid(x - 3, y) - solid(x + 3, y),
                                    solid(x, y - 3) - solid(x, y + 3))
            if not normal.length_squared():
                normal = pygame.Vector2(x - pivot[0], y - pivot[1])
            if not normal.length_squared():
                continue
            progress = rng.uniform(.82, .92) if i > 150 else rng.uniform(.4, .82)
            scale = 1 + 1.1 * (1 - progress * progress * (3 - 2 * progress))
            origin = pygame.Vector2(pivot) + (pygame.Vector2(x, y) - pivot) * scale
            life = rng.uniform(.4, .65)
            birth = progress * duration
            drift = normal.normalize().rotate(rng.uniform(-25, 25)) * rng.uniform(10, 27)
            self.particles.append((birth, life, origin, drift, rng.randint(4, 7)))
            self.end_time = max(self.end_time, birth + life)

    def draw(self, surface, elapsed):
        self.field.fill((0, 0, 0))
        for birth, life, origin, drift, size in self.particles:
            age = (elapsed - birth) / life
            if not 0 < age < 1:
                continue
            pos = origin + drift * (1 - (1 - age) ** 2) + pygame.Vector2(0, -12 * age)
            strength = round(230 * min(1, age / .08) * max(0, min(1, (1 - age) / .65)))
            extent = round(size * (3 + 2 * age))
            puff = pygame.transform.smoothscale(self.kernel, (extent, extent))
            puff.fill((strength,) * 3, special_flags=pygame.BLEND_RGB_MULT)
            self.field.blit(puff, puff.get_rect(center=(round(pos.x), round(pos.y))),
                            special_flags=pygame.BLEND_RGB_ADD)
        for threshold, color in ((40, (209, 209, 197, 70)), (65, (222, 222, 209, 175))):
            mask = pygame.mask.from_threshold(self.field, (255, 255, 255),
                                              (256 - threshold,) * 3 + (255,))
            surface.blit(mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0)), (0, 0))
