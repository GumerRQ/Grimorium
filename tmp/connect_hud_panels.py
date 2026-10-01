from pathlib import Path
p=Path('src/game/ui/hud_layout.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace('import sys','import sys\nimport shutil')
s=s.replace('from game.utils.paths import data_path','from game.utils.paths import data_path, asset_path')
s=s.replace('DEFAULTS = {','''DEFAULTS = {
    "stats_panel": {**zone(5, 57, 73, 167), "kind": "image",
                    "asset": "images/hud/panels/stats_panel.png", "visible": True,
                    "members": ["time", "coins", "damage", "speed", "fire_rate", "shoot_distance", "body_damage"]},
    "tower_panel": {**zone(564, 60, 63, 275), "kind": "image",
                    "asset": "images/hud/panels/tower_panel.png", "visible": True,
                    "members": ["tower_view", "tower_title", "floor_label", "floor_value", "loop_label", "loop_value"]},''')
s=s.replace('        self.items = deepcopy(DEFAULTS)','        self.items = deepcopy(DEFAULTS)\n        self.image_cache = {}\n        self.scaled_cache = {}',1)
s=s.replace('if data.get("version") != 1:', 'if data.get("version") not in (1, 2):')
s=s.replace('''                if key not in self.items or not isinstance(value, dict):
                    continue''','''                if not isinstance(key, str) or not isinstance(value, dict):
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
                        continue''')
s=s.replace('                self.items[key] = zone(x, y, w, h, align)','''                self.items[key] = zone(x, y, w, h, align)
                if is_image:
                    self.items[key].update(kind="image", asset=value["asset"],
                                           visible=value.get("visible", True) is not False,
                                           members=[m for m in value.get("members", [])
                                                    if isinstance(m, str) and m in DEFAULTS
                                                    and DEFAULTS[m].get("kind") != "image"],
                                           name=str(value.get("name", ""))[:60])''')
s=s.replace('{"version": 1, "items": self.items}', '{"version": 2, "items": self.items}')
position=s.index('    def rect(self, key):')
s=s[:position]+'''    def is_image(self, key):
        return self.items[key].get("kind") == "image"

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
            if not self.is_image(key) or not item.get("visible", True):
                continue
            rect = self.rect(key)
            try:
                image = self.get_image(key)
                cache_key = (item["asset"], rect.size)
                if cache_key not in self.scaled_cache:
                    # Avoid accumulating every intermediate size while dragging.
                    self.scaled_cache = {k: v for k, v in self.scaled_cache.items() if k[0] != item["asset"]}
                    self.scaled_cache[cache_key] = pygame.transform.scale(image, rect.size)
                surface.blit(self.scaled_cache[cache_key], rect)
            except (OSError, ValueError, pygame.error):
                # Missing custom art must not prevent starting a run.
                pygame.draw.rect(surface, (161, 74, 95), rect, 1)

    def movement_keys(self, selection):
        keys = list(selection)
        for key in selection:
            if self.is_image(key):
                keys.extend(m for m in self.items[key].get("members", []) if m in self.items)
        return list(dict.fromkeys(keys))

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

'''+s[position:]
p.write_text(s,encoding='utf-8')
# Remove the baked HUD entirely from the room snapshot; compose movable images live.
p=Path('src/game/screens/combat_screen.py');s=p.read_text(encoding='utf-8')
a=s.index('        self.background = pygame.image.load(',s.index('    def setup_background'))
b=s.index('    def setup_player_for_combat',a)
s=s[:a]+s[b:]
s=s.replace('        surface.blit(self.background, (self.offset_x, self.offset_y))\n','')
s=s.replace('''        self.draw_room_info(surface)
        self.draw_floor_track(surface)''','''        self.draw_floor_track(surface)
        self.draw_room_info(surface)''')
s=s.replace('''                              self.game.get_tower_floor_index(), self.game.localization, self.hud_layout)
''','''                              self.game.get_tower_floor_index(), self.game.localization, self.hud_layout)
        self.hud_layout.draw_images(surface)
        self.tower_track.draw_labels(surface, self.font, self.game.get_tower_floor_index(),
                                    self.game.localization, self.hud_layout)
''')
p.write_text(s,encoding='utf-8')
p=Path('src/game/screens/ascent_screen.py');s=p.read_text(encoding='utf-8')
s=s.replace('        surface.blit(screen.background, (screen.offset_x, screen.offset_y))\n','').replace('''        screen.draw_room_info(surface)
        screen.draw_floor_track(surface)''','''        screen.draw_floor_track(surface)
        screen.draw_room_info(surface)''');p.write_text(s,encoding='utf-8')
p=Path('src/game/visuals/tower_track.py');s=p.read_text(encoding='utf-8')
s=s.replace('            pygame.draw.rect(surface, (20, 27, 34), (568, 64, 55, 267))\n','')
a=s.index('            current = max(0, current_floor)',s.index('def draw('));b=s.index('            return',a)
labels=s[a:b]
s=s[:a]+s[b:]
a=s.index('    def draw_landscape')
# Reuse existing label content outside the view render so frames sit over the landscape but below text.
method='    def draw_labels(self, surface, font, current_floor, localization, layout):\n'+''.join(line[4:]+'\n' for line in labels.splitlines())+'\n'
s=s[:a]+method+s[a:];p.write_text(s,encoding='utf-8')
print('Independent HUD artwork and grouped layout support connected.')
