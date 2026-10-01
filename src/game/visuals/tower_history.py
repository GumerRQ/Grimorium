"""Ordered floor silhouettes for the live stack and the end-of-run tower."""
from datetime import datetime
import json
import logging
import uuid

import pygame

from game.utils.paths import project_root
from game.visuals.tower_track import TowerTrack


class TowerHistory:
    def __init__(self):
        self.floors = []
        self.layers = []
        self.path = None
        self.track = TowerTrack()

    def record(self, screen):
        self.run_seed = screen.game.run_state.run_seed
        self.debug_used = screen.game.run_state.debug_used
        self.floors.append({"floor": len(self.floors) + 1,
                            "type": screen.room.room_type,
                            "layout": list(screen.room.layout), "completed": False})
        self.layers.append(screen.capture_room_layer(include_structure=False))
        self.track.enter_floor(len(self.floors))
        self.save()

    def complete(self, screen):
        self.debug_used = screen.game.run_state.debug_used
        if self.floors:
            self.floors[-1]["completed"] = True
            self.layers[-1] = screen.capture_room_layer(include_structure=False)
            self.save()

    def save(self, result="in_progress"):
        if not self.floors:
            return
        if self.path is None:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.path = project_root() / "saves" / "towers" / f"{stamp}-{uuid.uuid4().hex[:6]}.json"
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps({"version": 1, "result": result,
                                             "seed": getattr(self, 'run_seed', None),
                                             "debug_used": getattr(self, 'debug_used', False),
                                             "roof_removed": self.track.roof_removed,
                                             "floors": self.floors}, indent=2), encoding="utf-8")
            temporary.replace(self.path)
        except OSError:
            logging.exception("Could not save tower history to %s", self.path)

    def draw_below(self, surface, height, pivot, count):
        for index, layer in enumerate(self.layers[:count]):
            depth = max(0.0, height - index)
            scale = 1 / (1 + .28 * depth)
            brightness = max(.07, .3 ** depth)
            width, h = layer.get_size()
            image = pygame.transform.scale(layer, (max(1, round(width * scale)),
                                                   max(1, round(h * scale))))
            shade = round(255 * brightness)
            image.fill((shade, shade, shade), special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(image, (round(pivot[0] * (1 - scale)), round(pivot[1] * (1 - scale))))

    def underlay(self, screen):
        layer = pygame.Surface(screen.get_virtual_size(), pygame.SRCALPHA)
        self.draw_below(layer, len(self.layers) - 1, screen.room.perimeter_rect.center,
                        len(self.layers) - 1)
        return layer

    def draw_side(self, surface, center_x, bottom, available_height):
        """Shallow side perspective preserves each floor's actual footprint."""
        spacing = min(23, available_height / max(1, len(self.floors)))
        for index, floor in enumerate(self.floors):
            base = bottom - index * spacing
            boss = floor["type"] == "boss"
            top = (123, 113, 92) if boss else (91, 110, 117)
            front = (75, 65, 51) if boss else (43, 57, 66)
            for r, row in enumerate(floor["layout"]):
                for c, tile in enumerate(row):
                    if tile in " Vv":
                        continue
                    x = center_x + (c - r - 2) * 8
                    y = base + (c + r - 11) * 2
                    points = [(x, y), (x + 8, y + 2), (x, y + 4), (x - 8, y + 2)]
                    pygame.draw.polygon(surface, front, [points[3], points[2], points[1],
                                         (x + 8, y + 2 + spacing), (x, y + 4 + spacing),
                                         (x - 8, y + 2 + spacing)])
                    pygame.draw.polygon(surface, top, points)
