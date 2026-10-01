"""Small side-view tower; its hidden extension is revealed by the first boss."""
import pygame

from game import config


class TowerTrack:
    FLOOR_HEIGHT = 22

    def __init__(self):
        self.first_loop = sum(step in ("normal", "boss") for step in config.RUN_PATTERN)
        self.roof_removed = False
        self.roof_time = 0.0
        self.growth_time = 1.0
        self.floor_count = self.first_loop
        self.previous_count = self.first_loop
        self.floor_position = 0.0
        self.start_position = 0.0
        self.target_position = 0.0
        self.travel_time = 0.0
        self.roof_floor = self.first_loop

    def reveal(self):
        if not self.roof_removed:
            self.roof_removed = True
            self.roof_time = 0.0

    def enter_floor(self, count):
        self.start_position = self.floor_position
        self.target_position = max(0, count - 1)
        self.travel_time = 0.0
        target = ((max(1, count) - 1) // self.first_loop + 1) * self.first_loop
        self.expand_to(target)

    def expand_to(self, target):
        if target > self.floor_count:
            self.reveal()
            self.previous_count = self.floor_count
            self.floor_count = target
            self.growth_time = 0.0

    def defeat_boss(self, completed_loop, max_loops):
        if completed_loop < max_loops:
            self.expand_to((completed_loop + 1) * self.first_loop)

    def update(self, dt):
        dt = max(0.0, dt)
        self.travel_time += dt
        travel = min(1.0, self.travel_time / max(.1, config.TOWER_ASCENT_SECONDS))
        travel = travel * travel * (3 - 2 * travel)
        self.floor_position = self.start_position + (self.target_position - self.start_position) * travel
        if self.roof_removed:
            self.roof_time = min(1.4, self.roof_time + dt)
        self.growth_time = min(1.0, self.growth_time + dt)

    def draw(self, surface, history, font, current_floor, localization, layout=None):
        if layout is not None:
            if not layout.is_visible("tower_view"):
                return
            # Keep tower animation coordinates independent of the editable viewport.
            if not hasattr(self, "_hud_surface"):
                self._hud_surface = pygame.Surface((640, 360), pygame.SRCALPHA)
            scratch = self._hud_surface
            scratch.fill((0, 0, 0, 0))
            self.draw(scratch, history, font, current_floor, localization)
            target = layout.rect("tower_view")
            view = scratch.subsurface((568, 88, 55, 167))
            surface.blit(pygame.transform.scale(view, target.size), target)
            return
        panel = pygame.Rect(568, 64, 55, 267)
        pygame.draw.rect(surface, (20, 27, 34), panel)
        current = max(0, current_floor)
        count = self.floor_count
        growth = self.growth_time ** 2 * (3 - 2 * self.growth_time)
        height = self.FLOOR_HEIGHT
        viewport = pygame.Rect(568, 88, 55, 167)
        camera = 0.0
        if self.roof_removed:
            # Before the reveal the building is stationary. Afterwards blend
            # into a centered follow camera, without snapping at the boss.
            follow = min(1.0, self.roof_time / 1.4)
            follow = follow * follow * (3 - 2 * follow)
            centered = (self.floor_position + .5) * height - (247 - viewport.centery)
            camera = max(0.0, centered) * follow
        bottom, center = round(247 + camera), 595
        old_clip = surface.get_clip()
        surface.set_clip(viewport.clip(old_clip))
        self.draw_landscape(surface, viewport, camera)
        # Ground and the entrance anchor the building while it grows upward.
        pygame.draw.ellipse(surface, (11, 18, 23), (571, bottom - 2, 49, 9))
        for index in range(count):
            built = index < len(history.floors)
            floor = history.floors[index] if built else None
            width = 34
            if floor and index >= self.first_loop:
                occupied = [(r, c) for r, row in enumerate(floor["layout"])
                            for c, tile in enumerate(row) if tile not in " Vv"]
                if occupied:
                    span = max(c for _, c in occupied) - min(c for _, c in occupied) + 1
                    width = round(24 + span / 13 * 17)
            fresh = index >= self.previous_count and count > self.first_loop
            lift = round(13 * (1 - growth)) if fresh else 0
            y = round(bottom - (index + 1) * height) - lift
            if y > viewport.bottom or y + height < viewport.top:
                continue
            room = pygame.Surface((width, max(5, round(height) + 1)), pygame.SRCALPHA)
            boss = floor["type"] == "boss" if floor else (index + 1) % self.first_loop == 0
            color = (99, 92, 76) if boss else (72, 87, 97)
            if index > current:
                color = (48, 57, 67)
            room.fill(color)
            pygame.draw.rect(room, (28, 38, 46), room.get_rect(), 1)
            for brick_y in range(5, room.get_height(), 5):
                pygame.draw.line(room, (48, 59, 66), (1, brick_y), (width - 2, brick_y))
                for brick_x in range(4 + (brick_y // 5 % 2) * 5, width - 1, 10):
                    pygame.draw.line(room, (48, 59, 66), (brick_x, brick_y - 4), (brick_x, brick_y))
            light = max(0, 1 - abs(index - self.floor_position))
            window_color = tuple(round(a + (b - a) * light)
                                 for a, b in zip((20, 31, 42), (255, 217, 128)))
            for wx in (width // 3, width * 2 // 3):
                pygame.draw.rect(room, window_color, (wx - 1, 3, 3, max(2, min(6, round(height) - 6))))
            if fresh:
                room.set_alpha(round(255 * growth))
            surface.blit(room, (center - width // 2, y))
        marker_y = round(bottom - (self.floor_position + .5) * height)
        pygame.draw.polygon(surface, (255, 227, 158),
                            [(570, marker_y - 3), (574, marker_y), (570, marker_y + 3)])
        roof = pygame.Surface((48, 27), pygame.SRCALPHA)
        pygame.draw.polygon(roof, (139, 72, 67), [(0, 24), (24, 1), (47, 24)])
        pygame.draw.polygon(roof, (69, 44, 53), [(24, 1), (47, 24), (24, 24)])
        pygame.draw.line(roof, (205, 145, 102), (1, 24), (24, 1), 1)
        pygame.draw.rect(roof, (42, 44, 51), (0, 24, 48, 3))
        roof_y = bottom - self.roof_floor * height - 26
        if not self.roof_removed:
            surface.blit(roof, (center - 24, round(roof_y)))
        elif self.roof_time < 1.4:
            t = self.roof_time / 1.4
            flying = pygame.transform.rotate(roof, -65 * t)
            flying.set_alpha(round(255 * (1 - t)))
            surface.blit(flying, flying.get_rect(center=(center + round(22 * t),
                         round(roof_y + 13 - 125 * t - 25 * t * t))))
        surface.set_clip(old_clip)
        def label(text, y, color=(227, 232, 230)):
            image = font.render(text, True, color)
            surface.blit(image, image.get_rect(center=(595, y)))
        label(localization.text("ui.tower.title"), 77)
        label(localization.text("ui.tower.floor"), 272)
        label(str(current + 1) if self.roof_removed else f"{current + 1}/{self.first_loop}", 286)
        label(localization.text("ui.tower.loop") if self.roof_removed else localization.text("ui.tower.top"), 308)
        label(str(current // self.first_loop + 1) if self.roof_removed else str(self.first_loop), 322)

    def draw_labels(self, surface, font, current_floor, localization, layout):
        current = max(0, current_floor)
        texts = {
            "tower_title": localization.text("ui.tower.title"),
            "floor_label": localization.text("ui.tower.floor"),
            "floor_value": str(current + 1) if self.roof_removed else f"{current + 1}/{self.first_loop}",
            "loop_label": localization.text("ui.tower.loop" if self.roof_removed else "ui.tower.top"),
            "loop_value": str(current // self.first_loop + 1) if self.roof_removed else str(self.first_loop),
        }
        for key, text in texts.items():
            layout.draw_text(surface, font, text, key, (227, 232, 230))

    def draw_landscape(self, surface, viewport, camera):
        # The scenery scrolls downward as our viewpoint climbs. Distant clouds
        # and hills move slower; tower floors always retain their pixel size.
        for y in range(viewport.top, viewport.bottom):
            mix = (y - viewport.top) / viewport.height
            color = (round(82 + 42 * mix), round(149 + 40 * mix), round(189 + 23 * mix))
            pygame.draw.line(surface, color, (viewport.left, y), (viewport.right - 1, y))
        for index in range(-1, 4):
            y = round(viewport.top + (camera * .35) % 78 + index * 78)
            x = viewport.left + (7 if index % 2 else 31)
            pygame.draw.ellipse(surface, (201, 223, 225), (x - 9, y, 22, 5))
            pygame.draw.ellipse(surface, (225, 236, 232), (x - 4, y - 3, 12, 7))
        hill_y = round(235 + camera * .45)
        pygame.draw.ellipse(surface, (77, 126, 100), (548, hill_y, 100, 50))
        ground_y = round(247 + camera)
        if ground_y < viewport.bottom:
            pygame.draw.rect(surface, (61, 111, 58), (viewport.left, ground_y, viewport.width,
                                                    viewport.bottom - ground_y))
            pygame.draw.line(surface, (137, 171, 77), (viewport.left, ground_y),
                             (viewport.right - 1, ground_y), 2)
            for x in range(viewport.left + 2, viewport.right - 1, 7):
                pygame.draw.line(surface, (152, 183, 83), (x, ground_y), (x - 1, ground_y - 2))
