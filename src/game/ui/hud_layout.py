"""Editable combat HUD zones, in the game's 640 x 360 logical pixels."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import shutil

import pygame
from game.utils.paths import data_path, asset_path


def zone(x, y, w, h, align="center"):
    return {"rect": [x, y, w, h], "align": align}


DEFAULTS = {
    "stats_panel": {**zone(5, 57, 73, 167), "kind": "image",
                    "asset": "images/hud/panels/stats_panel.png", "visible": True,
                    "members": ["time", "coins", "damage", "speed", "fire_rate", "shoot_distance", "body_damage"]},
    "tower_panel": {**zone(564, 60, 63, 275), "kind": "image",
                    "asset": "images/hud/panels/tower_panel.png", "visible": True,
                    "members": ["tower_view", "tower_title", "floor_label", "floor_value", "loop_label", "loop_value"]},
    "health_bar": zone(25, 15, 120, 16, "left"),
    "health_text": zone(25, 15, 120, 16),
    "time": zone(5, 47, 96, 16),
    "coins": zone(24, 89, 68, 16),
    "damage": zone(40, 113, 40, 16),
    "speed": zone(40, 135, 40, 16),
    "fire_rate": zone(40, 155, 40, 16),
    "shoot_distance": zone(40, 175, 40, 16),
    "body_damage": zone(40, 197, 40, 16),
    "tower_view": zone(568, 88, 55, 167),
    "tower_title": zone(568, 69, 55, 16),
    "floor_label": zone(568, 264, 55, 16),
    "floor_value": zone(568, 278, 55, 16),
    "loop_label": zone(568, 300, 55, 16),
    "loop_value": zone(568, 314, 55, 16),
}


class HudLayout:
    def __init__(self):
        self.path = (Path(os.environ.get("APPDATA", Path.home())) / "Grimorium" / "hud_layout.json"
                     if getattr(sys, "frozen", False) else data_path("hud_layout.json"))
        self.items = deepcopy(DEFAULTS)
        self.image_cache = {}
        self.scaled_cache = {}
        self.health_capacity = 0
        self.load()

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("version") not in (1, 2, 3):
                return
            for key, value in data.get("items", {}).items():
                if not isinstance(key, str) or not isinstance(value, dict):
                    continue
                is_image = value.get("kind") == "image"
                if key not in self.items and not is_image:
                    continue
                if key in self.items and self.is_image(key) != is_image:
                    continue
                if is_image:
                    try:
                        self.image_path(value["asset"])
                    except (KeyError, TypeError, ValueError):
                        continue
                rect = value.get("rect")
                if not isinstance(rect, list) or len(rect) != 4 or not all(type(n) is int for n in rect):
                    continue
                x, y, w, h = rect
                if w < 4 or h < 4 or x < 0 or y < 0 or x + w > 640 or y + h > 360:
                    continue
                align = value.get("align", "center")
                if align not in ("left", "center", "right"):
                    continue
                self.items[key] = zone(x, y, w, h, align)
                self.items[key]["deleted"] = value.get("deleted", False) is True
                self.items[key]["visible"] = value.get("visible", True) is not False
                if is_image:
                    self.items[key].update(kind="image", asset=value["asset"],
                                           visible=value.get("visible", True) is not False,
                                           members=[m for m in value.get("members", [])
                                                    if isinstance(m, str) and m in DEFAULTS
                                                    and DEFAULTS[m].get("kind") != "image"],
                                           name=str(value.get("name", ""))[:60])
                    fit_to = value.get("fit_to")
                    # One-time compatibility with layouts saved before explicit links.
                    if data.get("version") < 3 and fit_to is None:
                        if "health_bar" in value.get("members", []) or Path(value["asset"]).stem == "health_panel":
                            fit_to = "health_bar"
                    if fit_to == "health_bar":
                        self.items[key]["fit_to"] = fit_to
                        if fit_to not in self.items[key]["members"]:
                            self.items[key]["members"].append(fit_to)
        except (OSError, ValueError, AttributeError, TypeError):
            pass

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps({"version": 3, "items": self.items}, indent=2) + "\n", encoding="utf-8")
            temporary.replace(self.path)
            return True
        except OSError:
            return False

    def is_image(self, key):
        return self.items[key].get("kind") == "image"

    def is_visible(self, key):
        item = self.items.get(key, {})
        return not item.get("deleted", False) and item.get("visible", True)

    def is_health_panel(self, key):
        item = self.items[key]
        return self.is_image(key) and item.get("fit_to") == "health_bar"

    def health_width_adjustment(self):
        from game.ui.health_hearts import heart_row_width
        rect = self.rect("health_bar")
        # Signed difference: keep the edited margins, but fit even a short row.
        # Use capacity so losing health does not hide the empty heart containers.
        return heart_row_width(self.health_capacity, rect.height) - rect.width

    @staticmethod
    def extend_health_panel(image, size):
        # Scale uniformly with height, keep end caps, repeat the middle strip.
        width, height = size
        source_w, source_h = image.get_size()
        scaled_w = max(1, round(source_w * height / source_h))
        image = pygame.transform.scale(image, (scaled_w, height))
        cap = max(1, min(round(12 * height / source_h), width // 2, scaled_w // 3))
        result = pygame.Surface(size, pygame.SRCALPHA)
        result.blit(image, (0, 0), (0, 0, cap, height))
        result.blit(image, (width-cap, 0), (scaled_w-cap, 0, cap, height))
        # One complete repeat of the straight top/bottom rail, away from caps.
        strip_w = max(1, min(round(32 * height / source_h), scaled_w-2*cap))
        source_x = max(cap, (scaled_w-strip_w)//2)
        for x in range(cap, width-cap, strip_w):
            result.blit(image, (x, 0), (source_x, 0, min(strip_w, width-cap-x), height))
        return result

    def image_path(self, relative):
        root = asset_path().resolve()
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or path.suffix.lower() != ".png":
            raise ValueError("HUD images must be PNG files inside assets")
        return path

    def get_image(self, key):
        source = self.items[key]["asset"]
        if source not in self.image_cache:
            self.image_cache[source] = pygame.image.load(str(self.image_path(source))).convert_alpha()
        return self.image_cache[source]

    def reload_images(self):
        # Load all first so a broken edit leaves the previous images available.
        images = {}
        for key in self.items:
            if self.is_image(key):
                source = self.items[key]["asset"]
                images[source] = pygame.image.load(str(self.image_path(source))).convert_alpha()
        self.image_cache = images
        self.scaled_cache.clear()

    def draw_images(self, surface):
        for key, item in self.items.items():
            if not self.is_image(key) or not self.is_visible(key):
                continue
            rect = self.rect(key)
            health_panel = self.is_health_panel(key)
            if health_panel and self.is_visible("health_bar"):
                rect.width = max(4, rect.width + self.health_width_adjustment())
            try:
                image = self.get_image(key)
                cache_key = (item["asset"], rect.size, health_panel)
                if cache_key not in self.scaled_cache:
                    # Avoid accumulating every intermediate size while dragging.
                    self.scaled_cache = {k: v for k, v in self.scaled_cache.items() if k[0] != item["asset"]}
                    self.scaled_cache[cache_key] = (self.extend_health_panel(image, rect.size)
                                                    if health_panel else pygame.transform.scale(image, rect.size))
                surface.blit(self.scaled_cache[cache_key], rect)
            except (OSError, ValueError, pygame.error):
                # Missing custom art must not prevent starting a run.
                pygame.draw.rect(surface, (161, 74, 95), rect, 1)

    def movement_keys(self, selection):
        keys = list(selection)
        for key in selection:
            if self.is_image(key):
                keys.extend(m for m in self.items[key].get("members", []) if m in self.items)
        return [key for key in dict.fromkeys(keys) if not self.items[key].get("deleted", False)]

    def import_png(self, filename):
        source = Path(filename).resolve()
        image = pygame.image.load(str(source)).convert_alpha()
        root = asset_path().resolve()
        if source.is_relative_to(root):
            destination = source
        else:
            folder = asset_path("images", "hud", "panels")
            folder.mkdir(parents=True, exist_ok=True)
            destination = folder / source.name
            index = 2
            while destination.exists():
                destination = folder / f"{source.stem}_{index}.png"
                index += 1
            shutil.copy2(source, destination)
        key = "image_" + destination.stem
        index = 2
        base = key
        while key in self.items:
            key = f"{base}_{index}"
            index += 1
        w, h = image.get_size()
        scale = min(1, 640 / w, 360 / h)
        w, h = max(4, round(w * scale)), max(4, round(h * scale))
        self.items[key] = {**zone((640 - w) // 2, (360 - h) // 2, w, h),
                           "kind": "image", "asset": destination.relative_to(root).as_posix(),
                           "name": destination.stem, "visible": True, "members": []}
        self.image_cache[self.items[key]["asset"]] = image
        return key

    def rect(self, key):
        return pygame.Rect(self.items[key]["rect"])

    def draw_text(self, surface, font, text, key, color):
        if not self.is_visible(key):
            return
        image = font.render(text, True, color)
        zone_rect = self.rect(key)
        target = image.get_rect(centery=zone_rect.centery)
        align = self.items[key]["align"]
        if align == "left":
            target.left = zone_rect.left
        elif align == "right":
            target.right = zone_rect.right
        else:
            target.centerx = zone_rect.centerx
        surface.blit(image, target)
