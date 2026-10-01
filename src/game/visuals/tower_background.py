"""Paisaje persistente bajo la torre, independiente de la cámara y las salas.

El terreno se compone una sola vez con PNG editables. Solo se recorta y escala
durante el ascenso; las nubes son dos capas independientes. No usa el generador
aleatorio del combate ni modifica el tamaño de entidades o colisiones.
"""

from collections import OrderedDict
import math
import random

import pygame

from game import config
from game.utils.paths import asset_path


def _smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


class TowerBackground:
    SIZE = (640, 360)
    SKY_COLOR = (103, 190, 226)
    SPRITE_BACKGROUND_COLOR = (76, 105, 113)
    ASSET_NAMES = (
        "ground_moss", "tree_oak", "tree_pine", "tree_birch",
        "rock_large", "rock_small", "cloud_wide", "cloud_round",
    )

    def __init__(self, total_floors, seed=None):
        self.total_floors = max(1, int(total_floors))
        self.seed = config.TOWER_LANDSCAPE_SEED if seed is None else seed
        self.floor = 0.0
        self.target_floor = 0
        self._start_floor = 0.0
        self._elapsed = config.TOWER_ASCENT_SECONDS
        self.cloud_time = 0.0
        self._sprites = {
            name: pygame.image.load(
                asset_path("images", "backgrounds", "tower", name + ".png")
            ).convert_alpha()
            for name in self.ASSET_NAMES
        }
        for name, sprite in self._sprites.items():
            if name != "ground_moss":
                # Character Maker Pro exports may use a solid background.
                # Bake the color key into alpha before scaling or cloud fades.
                sprite.set_colorkey(self.SPRITE_BACKGROUND_COLOR)
                self._sprites[name] = sprite.convert_alpha()
        self._sprite_cache = OrderedDict()
        self._terrain_frame = pygame.Surface(self.SIZE).convert()
        self._fog = pygame.Surface(self.SIZE).convert()
        self._fog.fill(self.SKY_COLOR)
        self._frame_key = None
        self._build_terrain(random.Random(self.seed))
        self._build_clouds(random.Random(self.seed + 1))

    @property
    def progress(self):
        return min(1.0, self.floor / max(1, self.total_floors - 1))

    @property
    def ground_scale(self):
        return max(
            config.TOWER_MIN_GROUND_SCALE,
            1.0 / (1.0 + config.TOWER_ZOOM_PER_FLOOR * self.floor),
        )

    def set_floor(self, floor, *, immediate=False):
        """Piso absoluto, empezando en cero; las tiendas no cuentan como pisos."""
        floor = max(0, min(self.total_floors - 1, int(floor)))
        if immediate:
            self.floor = float(floor)
            self.target_floor = floor
            self._start_floor = self.floor
            self._elapsed = config.TOWER_ASCENT_SECONDS
        elif floor != self.target_floor:
            # Si llega otro cambio antes de terminar, partir de la altura visible.
            self._start_floor = self.floor
            self.target_floor = floor
            self._elapsed = 0.0

    def update(self, dt):
        dt = max(0.0, dt)
        self.cloud_time += dt
        duration = max(0.001, config.TOWER_ASCENT_SECONDS)
        self._elapsed = min(duration, self._elapsed + dt)
        amount = _smoothstep(self._elapsed / duration)
        self.floor = self._start_floor + (self.target_floor - self._start_floor) * amount

    def _sprite(self, name, width, flip=False):
        width = max(1, round(width))
        key = (name, width, flip)
        cached = self._sprite_cache.get(key)
        if cached is not None:
            self._sprite_cache.move_to_end(key)
            return cached
        original = self._sprites[name]
        height = max(1, round(original.get_height() * width / original.get_width()))
        sprite = pygame.transform.scale(original, (width, height))
        if flip:
            sprite = pygame.transform.flip(sprite, True, False)
        self._sprite_cache[key] = sprite
        if len(self._sprite_cache) > 128:
            self._sprite_cache.popitem(last=False)
        return sprite

    def _build_terrain(self, rng):
        # Margen suficiente incluso en la altura máxima: no asoman bordes vacíos.
        minimum_scale = max(0.05, config.TOWER_MIN_GROUND_SCALE)
        tile = self._sprites["ground_moss"].convert()
        tw, th = tile.get_size()
        width = math.ceil((self.SIZE[0] / minimum_scale + 128) / tw) * tw
        height = math.ceil((self.SIZE[1] / minimum_scale + 128) / th) * th
        self.terrain = pygame.Surface((width, height)).convert()
        tiles = {(x, y): pygame.transform.flip(tile, bool(x), bool(y))
                 for x in range(2) for y in range(2)}
        for row, y in enumerate(range(0, height, th)):
            for col, x in enumerate(range(0, width, tw)):
                self.terrain.blit(tiles[(col % 2, row % 2)], (x, y))

        cx, cy = width // 2, height // 2
        self.world_center = (cx, cy)
        # Sendero discreto: una referencia estable para reconocer el alejamiento.
        self._paths = []
        for direction in (-1, 1):
            points = []
            for offset in range(0, height, 12):
                y = cy + offset * direction
                if y < -30 or y > height + 30:
                    break
                x = cx + 62 + math.sin(offset / 140.0) * 75 + offset * .12
                points.append((round(x), round(y)))
            if len(points) > 1:
                pygame.draw.lines(self.terrain, (152, 112, 63), False, points, 21)
                pygame.draw.lines(self.terrain, (209, 169, 100), False, points, 15)
                self._paths.extend(points)

        tree_names = ("tree_oak", "tree_pine", "tree_birch")
        for y in range(12, height, 57):
            for x in range(12, width, 57):
                if rng.random() > .78:
                    continue
                px, py = x + rng.randint(-22, 22), y + rng.randint(-22, 22)
                if abs(px - cx) < 130 and abs(py - cy) < 85:
                    continue
                if any((px - ax) ** 2 + (py - ay) ** 2 < 27 ** 2
                       for ax, ay in self._paths):
                    continue
                if rng.random() < .82:
                    name = rng.choice(tree_names)
                    sprite_width = rng.randint(35, 57)
                else:
                    name = rng.choice(("rock_large", "rock_small"))
                    sprite_width = rng.randint(12, 25)
                sprite = self._sprite(name, sprite_width, rng.random() < .5)
                self.terrain.blit(sprite, sprite.get_rect(center=(px, py)))

    def _build_clouds(self, rng):
        self.clouds = []
        # Las capas se desplazan a distinta velocidad. Sus bordes se reciclan
        # fuera de pantalla; las posiciones no se sortean de nuevo en cada piso.
        for layer in range(2):
            for row in range(3):
                for col in range(4):
                    self.clouds.append({
                        "name": rng.choice(("cloud_wide", "cloud_round")),
                        "x": col * 240 + rng.uniform(-70, 70),
                        "y": row * 230 + rng.uniform(-50, 50),
                        "width": rng.uniform(110, 180),
                        "layer": layer,
                        "flip": rng.random() < .5,
                        "opacity": rng.uniform(.75, 1.0),
                    })

    def _draw_terrain(self, surface):
        sw = round(self.SIZE[0] / self.ground_scale)
        sh = round(self.SIZE[1] / self.ground_scale)
        haze = round(237 * _smoothstep((self.progress - .08) / .92))
        key = (sw, sh, haze)
        if key != self._frame_key:
            source = pygame.Rect(0, 0, sw, sh)
            source.center = self.world_center
            pygame.transform.scale(self.terrain.subsurface(source), self.SIZE, self._terrain_frame)
            if haze:
                self._fog.set_alpha(haze)
                self._terrain_frame.blit(self._fog, (0, 0))
            self._frame_key = key
        surface.blit(self._terrain_frame, (0, 0))

    def draw(self, surface):
        self._draw_terrain(surface)
        for cloud in self.clouds:
            layer = cloud["layer"]
            amount = _smoothstep((self.progress - (.12 + layer * .14)) / .68)
            alpha = round((150 + layer * 45) * amount * cloud["opacity"])
            if not alpha:
                continue
            scale = 1.0 - .2 * self.progress
            sprite = self._sprite(cloud["name"], cloud["width"] * scale, cloud["flip"])
            sprite.set_alpha(alpha)
            travel = self.cloud_time * config.TOWER_CLOUD_SPEED * (1 + layer * .7)
            x = (cloud["x"] + travel) % 960 - 160
            y = (cloud["y"] + travel * .12) % 690 - 165
            surface.blit(sprite, sprite.get_rect(center=(round(x), round(y))))
