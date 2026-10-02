"""Deterministic cutout animation made from the author's native Krita layers.

All transforms are runtime composition. Source drawings stay untouched. The
same renderer drives the game, the preview and the exported video.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass

import pygame

from game.utils.paths import asset_path


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smooth(value):
    value = clamp(value)
    return value * value * (3 - 2 * value)


def lerp(a, b, value):
    return a + (b - a) * value


@dataclass
class Cutout:
    image: pygame.Surface
    rect: pygame.Rect


class IntroSequence:
    """Load once; draw at any time without advancing or mutating playback."""

    def __init__(self, size=(320, 180)):
        self.size = tuple(size)
        if len(size) != 2 or min(size) <= 0:
            raise ValueError("Intro size must contain two positive dimensions")
        self.root = asset_path("video", "intro")
        self.plan = json.loads((self.root / "timeline.json").read_text(encoding="utf-8"))
        self.beats = self.plan["beats"]
        ends = [float(beat["end"]) for beat in self.beats]
        if any(not math.isfinite(t) for t in ends) or any(b <= a for a, b in zip([0.0] + ends, ends)):
            raise ValueError("Intro beat end times must increase")
        if [beat["id"] for beat in self.beats] != ["reading", "shadow", "snatch", "reaction", "tower", "chase", "arrival", "title"]:
            raise ValueError("Intro timeline has unexpected beats")
        self.duration = ends[-1]
        self.ends = ends
        self.layers = {}
        manifest = json.loads((self.root / "layers" / "manifest.json").read_text(encoding="utf-8"))
        self.canvas = (manifest["width"], manifest["height"])
        self.ratio = min(size[0] / self.canvas[0], size[1] / self.canvas[1])
        self.offset = ((size[0] - self.canvas[0] * self.ratio) / 2,
                       (size[1] - self.canvas[1] * self.ratio) / 2)
        # Numeric tracing/reference layers are deliberately excluded.
        for group in manifest["groups"]:
            for item in group["layers"]:
                if item["reference"] or not item["visible"]:
                    continue
                image = pygame.image.load(str(self.root / "layers" / item["file"]))
                if item["opacity"] < 1:
                    image.set_alpha(round(item["opacity"] * 255))
                self.layers[group["scene"], item["name"]] = Cutout(
                    image, pygame.Rect(item["x"], item["y"], item["width"], item["height"]))
        self.reader = self._combine(1, ["Baston", "Mage", "Book"])
        self.reader_empty = self._combine(1, ["Baston", "Mage"])
        self.back_mage = self._combine(5, ["Mago", "Baston"])
        crow = pygame.image.load(str(self.root / "crow-silhouette.png"))
        bounds = crow.get_bounding_rect(min_alpha=8)
        # Runtime texture region, not a modification of the saved art.
        crow = crow.subsurface(bounds).copy()
        self.crow = Cutout(crow, pygame.Rect(0, 0, *crow.get_size()))
        self._cache = {}
        self._backgrounds = {}
        self.font = pygame.font.Font(None, max(18, round(size[1] * .112)))

    def _combine(self, scene, names):
        layers = [self.layers[scene, name] for name in names]
        rect = layers[0].rect.copy()
        for layer in layers[1:]:
            rect.union_ip(layer.rect)
        image = pygame.Surface(rect.size, pygame.SRCALPHA)
        for layer in layers:
            image.blit(layer.image, (layer.rect.x - rect.x, layer.rect.y - rect.y))
        return Cutout(image, rect)

    def beat_at(self, seconds):
        seconds = clamp(float(seconds), 0, self.duration)
        start = 0.0
        for beat in self.beats:
            if seconds < beat["end"]:
                return beat, (seconds - start) / (beat["end"] - start)
            start = beat["end"]
        return self.beats[-1], 1.0

    def _mapped_time(self, seconds):
        """Map configurable beat lengths to the authored poses' time domain."""
        beat, progress = self.beat_at(seconds)
        index = self.beats.index(beat)
        authored = [0.0, 4.4, 5.4, 5.72, 8.6, 11.6, 17.5, 18.8, 20.0]
        return lerp(authored[index], authored[index + 1], progress)

    def _stamp(self, target, cutout, center=None, scale=1, angle=0, opacity=255, stretch=(1, 1)):
        if opacity <= 0 or scale <= 0:
            return
        if center is None:
            center = cutout.rect.center
        width = max(1, round(cutout.image.get_width() * self.ratio * scale * stretch[0]))
        height = max(1, round(cutout.image.get_height() * self.ratio * scale * stretch[1]))
        angle = round(angle * 2) / 2
        key = (id(cutout.image), width, height, angle)
        image = self._cache.get(key)
        if image is None:
            image = pygame.transform.smoothscale(cutout.image, (width, height))
            if angle:
                image = pygame.transform.rotate(image, angle)
            if len(self._cache) >= 180:
                self._cache.clear()
            self._cache[key] = image
        if opacity < 255:
            image = image.copy()
            image.set_alpha(round(opacity))
        x = round(self.offset[0] + center[0] * self.ratio)
        y = round(self.offset[1] + center[1] * self.ratio)
        target.blit(image, image.get_rect(center=(x, y)))

    def _layer(self, surface, scene, name, **kwargs):
        self._stamp(surface, self.layers[scene, name], **kwargs)

    def _background(self, surface, wide=False):
        key = "wide" if wide else "path"
        if key not in self._backgrounds:
            bg = pygame.Surface(self.size)
            bg.fill((98, 169, 195) if wide else (143, 175, 48))
            if wide:
                self._layer(bg, 5, "Cielo Montanias")
            else:
                self._layer(bg, 1, "Forest/Plains")
                self._layer(bg, 1, "Path")
            self._backgrounds[key] = bg
        surface.blit(self._backgrounds[key], (0, 0))

    def _fade(self, surface, opacity):
        if opacity <= 0:
            return
        overlay = pygame.Surface(self.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, round(clamp(opacity, 0, 255))))
        surface.blit(overlay, (0, 0))

    def _bird(self, surface, center, width, phase=0, opacity=255, book=False):
        factor = width / self.crow.rect.width
        # Small whole-body squash is sufficient during the fleeting pass.
        flap = 1 + .045 * math.sin(phase * 24)
        if book:
            layer = self.layers[5, "Libro"]
            self._stamp(surface, layer, center=(center[0] - width * .23, center[1] + width * .29),
                        scale=width / 590, angle=math.sin(phase * 18) * 4, opacity=opacity)
        self._stamp(surface, self.crow, center=center, scale=factor,
                    stretch=(1, flap), opacity=opacity)

    def _close(self, surface, t):
        self._background(surface)
        walking = min(t, 4.4)
        progress = walking / 4.4
        dx, dy = -453 * progress, 297 * progress
        bob = -abs(math.sin(walking * 6.5)) * 16 if t < 4.4 else 0
        sway = math.sin(walking * 6.5) * .65 if t < 4.4 else 0
        center = (self.reader.rect.centerx + dx, self.reader.rect.centery + dy + bob)
        if t < 5.5:
            self._stamp(surface, self.reader, center, angle=sway)
        else:
            reaction = max(0, t - 5.72)
            tilt = 0
            if .65 < reaction < 1.28:
                tilt = 5 * math.sin((reaction - .65) / .63 * math.pi)
            jump = -65 * max(0, math.sin((reaction - 1.28) / .28 * math.pi)) if 1.28 < reaction < 1.56 else 0
            leave = smooth((reaction - 2.2) / .68)
            empty_center = (self.reader_empty.rect.centerx + dx - leave * 2350,
                            self.reader_empty.rect.centery + dy + jump - leave * 280)
            self._stamp(surface, self.reader_empty, empty_center, angle=tilt + leave * 12)
            if 1.26 < reaction < 2.18:
                sign_scale = .75 * min(1, (reaction - 1.26) * 12)
                self._layer(surface, 4, "Sorpresa", center=(1100, 430), scale=sign_scale)
        if 4.4 <= t < 5.4:
            p = smooth((t - 4.4) / 1.0)
            self._bird(surface, (lerp(3800, 1830, p), lerp(240, 610, p)),
                       2400, phase=0, opacity=round(125 * p))
        if 5.4 <= t < 5.72:
            p = (t - 5.4) / .32
            position = (lerp(3600, -1100, p), 580 - 100 * p)
            for delay, alpha in ((160, 25), (75, 45)):
                self._bird(surface, (position[0] + delay, position[1] + 10), 1450, opacity=alpha)
            self._bird(surface, position, 1450, phase=t)
            if t >= 5.5:
                take = (t - 5.5) / .22
                book = self.layers[1, "Book"]
                self._stamp(surface, book,
                            center=(book.rect.centerx - 453 - take * 2400,
                                    book.rect.centery + 297 - take * 450),
                            angle=-take * 22)
            if 5.48 <= t < 5.58:
                self._layer(surface, 3, "Boom", center=(1190, 950), scale=.29,
                            opacity=200 * math.sin((t - 5.48) / .10 * math.pi))

    def _wide(self, surface, t):
        self._background(surface, wide=True)
        if t < 11.6:
            p = smooth((t - 8.6) / 1.75)
            if t < 10.35:
                self._bird(surface, (lerp(1540, 680, p), lerp(420, 350, p)),
                           lerp(590, 210, p), phase=t - 8.6, book=True)
            # Passing behind the native tower hides the thief at the window.
            self._layer(surface, 5, "Torre")
            self._stamp(surface, self.back_mage,
                        center=(self.back_mage.rect.centerx,
                                self.back_mage.rect.centery - 8 * math.sin((t - 8.6) * 2)),
                        angle=1.5 * math.sin((t - 8.6) * 1.4))
        else:
            self._layer(surface, 7, "Torre")
            # Position is the feet, so scaling really sends him into depth.
            points = [(11.6, 1838, 1548, 1.0), (12.6, 1420, 1570, .74),
                      (13.45, 1040, 1470, .58), (14.6, 820, 1235, .40),
                      (16.0, 725, 1120, .30), (17.5, 678, 1037, .205)]
            if t <= 17.5:
                for first, last in zip(points, points[1:]):
                    if first[0] <= t <= last[0]:
                        f = (t - first[0]) / (last[0] - first[0])
                        x, feet, scale = [lerp(first[i], last[i], f) for i in (1, 2, 3)]
                        break
                hop = abs(math.sin((t - 11.6) * 15)) * 37 * scale
                self._stamp(surface, self.back_mage,
                            center=(x, feet - self.back_mage.rect.height * scale / 2 - hop),
                            scale=scale, angle=math.sin((t - 11.6) * 15) * 3)
            else:
                into_door = smooth((t - 17.85) / .62)
                scale = lerp(.205, .12, into_door)
                self._stamp(surface, self.back_mage,
                            center=(678, 1037 - self.back_mage.rect.height * scale / 2 - 22 * into_door),
                            scale=scale, opacity=255 * (1 - into_door))
            self._layer(surface, 7, "Montania")
        if t > 18.5:
            self._fade(surface, smooth((t - 18.5) / .45) * 255)

    def draw(self, surface, seconds):
        if surface.get_size() != self.size:
            raise ValueError("Intro destination size differs from configured size")
        if not math.isfinite(seconds):
            raise ValueError("Intro time must be finite")
        t = self._mapped_time(seconds)
        if t < 8.6:
            self._close(surface, t)
        else:
            self._wide(surface, t)
        if t < .4:
            self._fade(surface, 255 * (1 - smooth(t / .4)))
        if t >= 18.95:
            surface.fill((13, 15, 19))
            title = self.font.render(self.plan["title"], True, (241, 216, 151))
            title.set_alpha(round(255 * smooth((t - 18.95) / .45)))
            surface.blit(title, title.get_rect(center=(self.size[0] / 2, self.size[1] / 2)))
