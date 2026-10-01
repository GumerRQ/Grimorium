"""Data-driven room props and lightweight, persistent material fragments."""
import math
import random
from functools import lru_cache

import pygame

from game.utils.paths import asset_path
from game.rooms.destructible_data import definitions



@lru_cache(maxsize=None)
def images(kind):
    return build_images(kind, definitions())


def build_images(kind, catalog):
    spec = catalog[kind]
    sheet = pygame.image.load(asset_path(spec['asset'])).convert_alpha()
    background_colors = {tuple(color) for color in spec.get('background_colors', [])}
    # Accept both transparent PNGs and art exported on the editing background.
    # Clear alpha before cropping so collision bounds and debris exclude it too.
    for y in range(sheet.get_height()):
        for x in range(sheet.get_width()):
            color = sheet.get_at((x, y))
            if (color.r, color.g, color.b) in background_colors:
                sheet.set_at((x, y), (color.r, color.g, color.b, 0))
    # One horizontal sheet per object: intact, damaged, then individual fragments.
    width, height = spec['frame_size']
    if sheet.get_height() != height or sheet.get_width() < width*2 or sheet.get_width() % width:
        raise ValueError(f'{kind}: sheet must contain a horizontal row of {width}x{height} frames')
    frames = [sheet.subsurface((x, 0, width, height)).copy()
              for x in range(0, sheet.get_width(), width)]
    fragments = []
    for frame in frames[2:]:
        bounds = frame.get_bounding_rect()
        if bounds.width and bounds.height:
            fragments.append(frame.subsurface(bounds).copy())
    return frames[0], frames[1], tuple(fragments)


def sweep_rect(x, y, dx, dy, rect, radius):
    """First contact of a moving projectile with an expanded blocker."""
    enter, leave, normal = 0.0, 1.0, (0, 0)
    for start, delta, low, high, axis in (
        (x, dx, rect.left-radius, rect.right+radius, 0),
        (y, dy, rect.top-radius, rect.bottom+radius, 1),
    ):
        if abs(delta) < 1e-12:
            if start < low or start > high:
                return None
            continue
        a, b = (low-start)/delta, (high-start)/delta
        near, far = min(a, b), max(a, b)
        if near > enter:
            enter = near
            sign = -1 if delta > 0 else 1
            normal = (sign, 0) if axis == 0 else (0, sign)
        leave = min(leave, far)
        if enter > leave:
            return None
    return (enter, normal) if leave >= 0 and enter <= 1 else None


class Destructible:
    def __init__(self, cell, on_destroy=None):
        self.on_destroy = on_destroy
        catalog = definitions()
        self.kind = random.choices(list(catalog), weights=[s['weight'] for s in catalog.values()], k=1)[0]
        self.spec = catalog[self.kind]
        self.intact, self.damaged, self.fragments = images(self.kind)
        self.position = self.intact.get_rect(center=cell.center).topleft
        self.rect = self.intact.get_bounding_rect().move(self.position)
        self.hits = 0
        self.body_cooldown = 0.0
        self.shake = 0.0

    def is_dead(self):
        return self.hits >= self.spec['hits_to_break']

    def receive_impact(self, impact):
        body = impact.kind == 'contact'
        if self.is_dead() or (body and self.body_cooldown > 0) or impact.damage <= 0:
            return False
        self.hits += 1
        self.shake = 0.12
        if body:
            self.body_cooldown = self.spec['body_hit_interval']
        if self.is_dead() and self.on_destroy is not None:
            self.on_destroy(self)
        return True

    def update(self, dt):
        self.body_cooldown = max(0, self.body_cooldown-dt)
        self.shake = max(0, self.shake-dt)

    def draw(self, surface):
        x, y = self.position
        offset = round(math.sin(self.shake*100)*2) if self.shake else 0
        surface.blit(self.damaged if self.hits >= self.spec['damaged_after_hits'] else self.intact, (x+offset, y))


class Debris:
    def __init__(self, image, center):
        self.image = pygame.transform.rotate(image, random.choice((0, 90, 180, 270)))
        self.x, self.y = center
        angle = random.uniform(0, math.tau)
        speed = random.uniform(25, 65)
        self.vx, self.vy = math.cos(angle)*speed, math.sin(angle)*speed
        self.height, self.vz = 1.0, random.uniform(30, 65)
        self.age = 0.0

    def update(self, dt, room):
        self.age += dt
        if self.age > 1.5:
            return
        # Small substeps keep fragments inside the walkable room floor.
        steps = max(1, math.ceil(dt / .02))
        step = dt / steps
        for _ in range(steps):
            x, y = self.x+self.vx*step, self.y+self.vy*step
            if any(r.collidepoint(x, y) for r in room.get_blocking_rects(True, True, True)) or not any(f['rect'].collidepoint(x, y) for f in room.floors):
                self.vx *= -.35
                self.vy *= -.35
            else:
                self.x, self.y = x, y
            self.vx *= math.exp(-4*step)
            self.vy *= math.exp(-4*step)
            self.vz -= 180*step
            self.height = max(0, self.height+self.vz*step)
            if self.height == 0:
                self.vz = -self.vz*.25 if self.vz < -15 else 0

    def draw(self, surface):
        surface.blit(self.image, self.image.get_rect(center=(round(self.x), round(self.y-self.height))))
