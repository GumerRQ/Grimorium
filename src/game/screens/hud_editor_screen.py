"""In-game combat HUD layout editor. The underlying combat never updates here."""
from copy import deepcopy
import pygame
from game.screens.base_screen import BaseScreen
from game.ui.fonts import create_font
from game.ui.hud_layout import DEFAULTS


class HudEditorScreen(BaseScreen):
    VIRTUAL_WIDTH = 640
    VIRTUAL_HEIGHT = 360

    def __init__(self, game, combat):
        super().__init__(game)
        self.combat = combat
        self.layout = combat.hud_layout
        self.saved = deepcopy(self.layout.items)
        self.undo_stack = []
        self.redo_stack = []
        self.grid_step = 1
        self.clean_preview = False
        self.edit_field = None
        self.field_value = ""
        self.field_replace = True
        self.pick_index = 0
        self.selected = ["coins"]
        self.drag = None
        self.mode = "all"
        self.status = ""
        self.font = create_font(pixel_scale=1)
        self.backdrop = pygame.Surface(self.get_virtual_size())
        combat.draw_scene(self.backdrop)
        self.panel = pygame.Rect(166, 5, 391, 137)
        self.panel.topleft = getattr(combat, "hud_editor_panel_position", self.panel.topleft)
        self.panel.clamp_ip(pygame.Rect(0, 0, 640, 360))
        self.panel_drag = None
        self.buttons = []
        rows = [
            [("save", self.save), ("done", self.finish), ("cancel", self.cancel),
             ("undo", self.undo), ("reset", self.reset)],
            [("left", lambda: self.set_alignment("left")),
             ("center", lambda: self.set_alignment("center")),
             ("right", lambda: self.set_alignment("right")),
             ("align_x", lambda: self.align("x")), ("align_y", lambda: self.align("y"))],
            [("distribute", self.distribute), ("all_stats", self.select_stats),
             ("redo", self.redo), ("delete", self.delete_selection)],
            [("mode", self.cycle_mode), ("add_png", self.add_png), ("reload", self.reload_art),
             ("group", self.group_selection), ("visibility", self.toggle_visibility)],
        ]
        for row, entries in enumerate(rows):
            x = self.panel.x + 6
            for index, (key, callback) in enumerate(entries):
                width = 110 if row == 2 and index < 2 else 72
                self.buttons.append((pygame.Rect(x, self.panel.y + 16 + row * 17, width, 14), key, callback))
                x += width + 4

    def t(self, key):
        return self.game.localization.text("ui.hud_editor." + key)

    def eligible_keys(self):
        return [key for key in self.layout.items
                if not self.layout.items[key].get("deleted", False)
                and (self.mode == "all" or self.layout.is_image(key) == (self.mode == "images"))]

    def delete_selection(self):
        if not self.selected:
            return
        self.remember()
        for key in self.selected:
            self.layout.items[key]["deleted"] = True
        self.selected = []
        self.drag = None
        self.status = self.t("deleted")

    def cycle_mode(self):
        modes = ("all", "images", "text")
        self.mode = modes[(modes.index(self.mode) + 1) % len(modes)]
        self.selected = []
        self.drag = None

    def name(self, key):
        item = self.layout.items[key]
        return item.get("name") or self.game.localization.text("ui.hud_editor.names." + key, key)

    def originals(self):
        return {key: self.layout.items[key]["rect"][:] for key in self.layout.movement_keys(self.selected)}

    def add_png(self):
        root = None
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            filename = filedialog.askopenfilename(parent=root, title=self.t("add_png"),
                                                  filetypes=[("PNG", "*.png")])
            if filename:
                self.remember()
                key = self.layout.import_png(filename)
                self.selected = [key]
                self.mode = "images"
                self.status = self.t("imported")
        except Exception:
            self.status = self.t("import_error")
        finally:
            if root is not None:
                root.destroy()

    def reload_art(self):
        try:
            from game.ui.health_hearts import reload_hearts
            reload_hearts()
            self.layout.reload_images()
            self.status = self.t("reloaded")
        except (OSError, ValueError, pygame.error):
            self.status = self.t("reload_error")

    def group_selection(self):
        panels = [key for key in self.selected if self.layout.is_image(key)]
        if len(panels) != 1:
            self.status = self.t("group_hint")
            return
        self.remember()
        panel = panels[0]
        members = [key for key in self.selected if not self.layout.is_image(key)]
        # Each number belongs to at most one panel, avoiding double movement.
        for key, item in self.layout.items.items():
            if self.layout.is_image(key):
                item["members"] = [member for member in item.get("members", []) if member not in members]
                if item.get("fit_to") in members:
                    item.pop("fit_to", None)
        self.layout.items[panel]["members"] = members
        if "health_bar" in members:
            self.layout.items[panel]["fit_to"] = "health_bar"
        else:
            self.layout.items[panel].pop("fit_to", None)
        self.status = self.t("grouped")

    def toggle_visibility(self):
        self.remember()
        for key in self.selected:
            item = self.layout.items[key]
            item["visible"] = not item.get("visible", True)

    def remember(self):
        self.undo_stack.append(deepcopy(self.layout.items))
        self.undo_stack = self.undo_stack[-60:]
        self.status = ""
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(deepcopy(self.layout.items))
            self.layout.items = self.undo_stack.pop()
        self.drag = None
        self.selected = [key for key in self.selected if key in self.layout.items and not self.layout.items[key].get("deleted", False)]

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(deepcopy(self.layout.items))
            self.layout.items = self.redo_stack.pop()
        self.drag = None
        self.selected = [key for key in self.selected if key in self.layout.items and not self.layout.items[key].get("deleted", False)]

    def fields(self):
        return [(pygame.Rect(self.panel.x+6+i*79, self.panel.y+116, 75, 15), i) for i in range(4)]

    def grid_rect(self):
        return pygame.Rect(self.panel.x+327, self.panel.y+116, 55, 15)

    def move_panel(self, pos):
        old = self.panel.topleft
        self.panel.topleft = (pos[0]-self.panel_drag[0], pos[1]-self.panel_drag[1])
        self.panel.clamp_ip(pygame.Rect(0, 0, 640, 360))
        dx, dy = self.panel.x-old[0], self.panel.y-old[1]
        for rect, _, _ in self.buttons:
            rect.move_ip(dx, dy)
        self.combat.hud_editor_panel_position = self.panel.topleft

    def apply_field(self):
        if self.edit_field is None or len(self.selected) != 1:
            self.edit_field = None
            return
        try:
            value = int(self.field_value)
        except ValueError:
            self.status = self.t("invalid_number")
            return
        key = self.selected[0]
        rect = self.layout.rect(key)
        values = list(rect)
        values[self.edit_field] = value
        x,y,w,h = values
        if x < 0 or y < 0 or w < 4 or h < 4 or x+w > 640 or y+h > 360:
            self.status = self.t("invalid_number")
            return
        self.remember()
        target = pygame.Rect(values)
        if self.edit_field < 2:
            self.move_element(key, target)
        else:
            self.resize_element(key, target, self.originals())
        self.edit_field = None

    def resize_element(self, key, rect, originals):
        if self.layout.is_image(key):
            old = pygame.Rect(originals[key])
            for member, previous in originals.items():
                if member == key:
                    continue
                child = pygame.Rect(previous)
                child.x = rect.x + round((child.x - old.x) * rect.w / old.w)
                child.y = rect.y + round((child.y - old.y) * rect.h / old.h)
                child.w = max(4, round(child.w * rect.w / old.w))
                child.h = max(4, round(child.h * rect.h / old.h))
                self.put_rect(member, child)
        self.put_rect(key, rect)

    def reset(self):
        self.remember()
        self.layout.items = deepcopy(DEFAULTS)
        self.selected = []

    def select_stats(self):
        self.mode = "all"
        self.selected = [key for key in ("damage", "speed", "fire_rate", "shoot_distance", "body_damage")
                         if not self.layout.items[key].get("deleted", False)]

    def save(self):
        if self.layout.save():
            self.saved = deepcopy(self.layout.items)
            self.status = self.t("saved")
            return True
        self.status = self.t("save_error")
        return False

    def finish(self):
        if self.save():
            self.game.screen_manager.set_screen(self.combat)

    def cancel(self):
        self.layout.items = deepcopy(self.saved)
        self.game.screen_manager.set_screen(self.combat)

    def set_alignment(self, alignment):
        self.remember()
        for key in self.selected:
            if key not in ("health_bar", "tower_view") and not self.layout.is_image(key):
                self.layout.items[key]["align"] = alignment

    def put_rect(self, key, rect):
        rect.width = max(4, min(640, rect.width))
        rect.height = max(4, min(360, rect.height))
        rect.clamp_ip(pygame.Rect(0, 0, 640, 360))
        self.layout.items[key]["rect"] = list(rect)

    def align(self, axis):
        if len(self.selected) < 2:
            return
        self.remember()
        anchor = self.layout.rect(self.selected[0])
        for key in self.selected[1:]:
            rect = self.layout.rect(key)
            if axis == "x":
                rect.centerx = anchor.centerx
            else:
                rect.centery = anchor.centery
            self.move_element(key, rect)

    def distribute(self):
        if len(self.selected) < 3:
            return
        self.remember()
        keys = sorted(self.selected, key=lambda key: self.layout.rect(key).centery)
        first, last = self.layout.rect(keys[0]).centery, self.layout.rect(keys[-1]).centery
        for i, key in enumerate(keys):
            rect = self.layout.rect(key)
            rect.centery = round(first + (last - first) * i / (len(keys) - 1))
            self.move_element(key, rect)

    def move_element(self, key, rect):
        previous = self.layout.rect(key)
        originals = {k: self.layout.items[k]["rect"][:] for k in self.layout.movement_keys([key])}
        self.move_group(originals, rect.x - previous.x, rect.y - previous.y)

    def move_group(self, originals, dx, dy):
        boxes = [pygame.Rect(rect) for rect in originals.values()]
        dx = max(-min(r.left for r in boxes), min(dx, 640 - max(r.right for r in boxes)))
        dy = max(-min(r.top for r in boxes), min(dy, 360 - max(r.bottom for r in boxes)))
        for key, rect in originals.items():
            self.put_rect(key, pygame.Rect(rect).move(dx, dy))

    def handle_event(self, event):
        if self.panel_drag is not None:
            if event.type == pygame.MOUSEMOTION:
                self.move_panel(self.screen_to_virtual(event.pos))
                return
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.panel_drag = None
                return
        if self.edit_field is not None:
            if event.type == pygame.TEXTINPUT:
                if event.text.isdigit():
                    self.field_value = ("" if self.field_replace else self.field_value) + event.text
                    self.field_value = self.field_value[:4]
                    self.field_replace = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.apply_field()
                elif event.key == pygame.K_ESCAPE:
                    self.edit_field = None
                elif event.key == pygame.K_BACKSPACE:
                    self.field_value = "" if self.field_replace else self.field_value[:-1]
                    self.field_replace = False
                elif event.key == pygame.K_a and event.mod & pygame.KMOD_CTRL:
                    self.field_replace = True
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.apply_field()
                if self.edit_field is not None:
                    return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_F8, pygame.K_ESCAPE) and getattr(event, "repeat", False):
                return
            ctrl = bool(event.mod & pygame.KMOD_CTRL)
            if event.key == pygame.K_ESCAPE:
                self.cancel()
            elif event.key == pygame.K_F8:
                self.finish()
            elif ctrl and event.key == pygame.K_s:
                self.save()
            elif ctrl and event.key == pygame.K_z:
                self.redo() if event.mod & pygame.KMOD_SHIFT else self.undo()
            elif ctrl and event.key == pygame.K_y:
                self.redo()
            elif event.key == pygame.K_h:
                self.clean_preview = not self.clean_preview
                self.drag = None
            elif ctrl and event.key == pygame.K_o:
                self.add_png()
            elif ctrl and event.key == pygame.K_g:
                self.group_selection()
            elif event.key == pygame.K_g:
                self.cycle_mode()
            elif event.key == pygame.K_r:
                self.reload_art()
            elif event.key == pygame.K_DELETE:
                self.delete_selection()
            elif event.key == pygame.K_TAB:
                keys = self.eligible_keys()
                index = keys.index(self.selected[-1]) if self.selected and self.selected[-1] in keys else -1
                if keys:
                    self.selected = [keys[(index + (-1 if event.mod & pygame.KMOD_SHIFT else 1)) % len(keys)]]
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN) and self.selected:
                self.remember()
                step = 10 if event.mod & pygame.KMOD_SHIFT else 1
                dx = step * ((event.key == pygame.K_RIGHT) - (event.key == pygame.K_LEFT))
                dy = step * ((event.key == pygame.K_DOWN) - (event.key == pygame.K_UP))
                self.move_group(self.originals(), dx, dy)
            elif event.key == pygame.K_F12:
                self.game.toggle_fullscreen()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = tuple(round(v) for v in self.screen_to_virtual(event.pos))
            if self.clean_preview:
                return
            if pygame.Rect(self.panel.x, self.panel.y, self.panel.width, 16).collidepoint(pos):
                self.panel_drag = (pos[0]-self.panel.x, pos[1]-self.panel.y)
                self.drag = None
                return
            for rect, index in self.fields():
                if rect.collidepoint(pos) and len(self.selected) == 1:
                    self.edit_field = index
                    self.field_value = str(self.layout.items[self.selected[0]]["rect"][index])
                    self.field_replace = True
                    return
            if self.grid_rect().collidepoint(pos):
                self.grid_step = {1:4, 4:8, 8:1}[self.grid_step]
                return
            for rect, key, callback in self.buttons:
                if rect.collidepoint(pos):
                    self.drag = None
                    callback()
                    return
            if self.panel.collidepoint(pos):
                return
            # Resize the single selected zone from its bottom-right handle.
            if len(self.selected) == 1:
                key = self.selected[0]
                rect = self.layout.rect(key)
                if pygame.Rect(rect.right - 4, rect.bottom - 4, 6, 6).collidepoint(pos):
                    self.remember()
                    self.drag = ("resize", pos, self.originals())
                    return
            keys = self.eligible_keys()
            # Text zones take priority in All mode; use Images mode to grab whole panels.
            keys.sort(key=lambda k: not self.layout.is_image(k))
            hits = [k for k in reversed(keys) if self.layout.rect(k).collidepoint(pos)]
            if not hits:
                self.selected = []
                return
            if pygame.key.get_mods() & pygame.KMOD_ALT:
                self.pick_index = (self.pick_index + 1) % len(hits)
            else:
                self.pick_index = 0
            key = hits[self.pick_index]
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                if key in self.selected:
                    self.selected.remove(key)
                else:
                    self.selected.append(key)
                return
            if key not in self.selected:
                self.selected = [key]
            self.remember()
            self.drag = ("move", pos, self.originals())
        elif event.type == pygame.MOUSEMOTION and self.drag:
            kind, start, originals = self.drag
            pos = tuple(round(v) for v in self.screen_to_virtual(event.pos))
            dx, dy = pos[0] - start[0], pos[1] - start[1]
            if kind == "move":
                if self.grid_step > 1:
                    anchor = next(iter(originals.values()))
                    dx = round((anchor[0]+dx)/self.grid_step)*self.grid_step-anchor[0]
                    dy = round((anchor[1]+dy)/self.grid_step)*self.grid_step-anchor[1]
                self.move_group(originals, dx, dy)
            else:
                key = next(iter(originals))
                rect = pygame.Rect(originals[key])
                rect.width = max(4, min(640 - rect.x, rect.width + dx))
                rect.height = max(4, min(360 - rect.y, rect.height + dy))
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    old = pygame.Rect(originals[key])
                    scale = min(rect.w / old.w, (640-old.x)/old.w, (360-old.y)/old.h)
                    rect.size = (max(4,round(old.w*scale)), max(4,round(old.h*scale)))
                self.resize_element(key, rect, originals)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.drag = None

    def draw(self, surface):
        surface.blit(self.backdrop, (0, 0))
        self.combat.draw_floor_track(surface)
        self.combat.draw_room_info(surface)
        self.combat.draw_hud(surface)
        if self.clean_preview:
            label = self.font.render(self.t("preview_hint"), True, (245,235,199))
            pygame.draw.rect(surface, (20,27,34), (240,344,170,12))
            surface.blit(label, (245,347))
            return
        if self.grid_step > 1:
            for x in range(0,640,self.grid_step):
                for y in range(0,360,self.grid_step):
                    surface.set_at((x,y),(76,95,93))
        mouse = self.screen_to_virtual(pygame.mouse.get_pos())
        for key in self.eligible_keys():
            rect = self.layout.rect(key)
            selected = key in self.selected
            color = (255, 211, 112) if selected else (84, 155, 166)
            pygame.draw.rect(surface, color, rect, 1)
            if selected:
                pygame.draw.line(surface, (97, 147, 139), (rect.centerx, 0), (rect.centerx, 359))
                pygame.draw.line(surface, (97, 147, 139), (0, rect.centery), (639, rect.centery))
                if len(self.selected) == 1:
                    pygame.draw.rect(surface, color, (rect.right - 3, rect.bottom - 3, 5, 5))
        pygame.draw.rect(surface, (20, 27, 34), self.panel)
        pygame.draw.rect(surface, (114, 150, 142), self.panel, 1)
        title = self.t("title") + (" *" if self.layout.items != self.saved else "")
        surface.blit(self.font.render(title, True, (239, 220, 167)), (self.panel.x+7, self.panel.y+6))
        # A small grip marks the draggable header without covering its title.
        for offset in (0, 3, 6):
            pygame.draw.line(surface, (114, 150, 142),
                             (self.panel.right-17, self.panel.y+5+offset),
                             (self.panel.right-7, self.panel.y+5+offset))
        for rect, key, callback in self.buttons:
            pygame.draw.rect(surface, (61, 79, 76) if rect.collidepoint(mouse) else (38, 50, 56), rect)
            label = self.font.render(self.t("mode_" + self.mode) if key == "mode" else self.t(key),
                                     True, (236, 237, 221))
            surface.blit(label, label.get_rect(center=rect.center))
        if self.selected:
            key = self.selected[-1]
            r = self.layout.rect(key)
            info = f"{self.name(key)}  X:{r.x} Y:{r.y}  {r.w}x{r.h}  " + self.t(self.layout.items[key]['align'])
        else:
            info = self.t("select")
        surface.blit(self.font.render(info, True, (228, 232, 220)), (self.panel.x+7, self.panel.y+88))
        if self.status:
            surface.blit(self.font.render(self.status, True, (239, 220, 167)), (self.panel.x+7, self.panel.y+99))
        for rect,index in self.fields():
            pygame.draw.rect(surface,(60,82,77) if self.edit_field==index else (35,45,53),rect)
            value = self.field_value + "_" if self.edit_field==index else (
                str(self.layout.items[self.selected[0]]["rect"][index]) if len(self.selected)==1 else "-")
            label = self.font.render(("X", "Y", "W", "H")[index]+": "+value,True,(230,234,220))
            surface.blit(label,(rect.x+4,rect.y+5))
        grid = self.grid_rect()
        pygame.draw.rect(surface,(44,61,64),grid)
        surface.blit(self.font.render(self.t("grid")+f" {self.grid_step}",True,(230,234,220)),(grid.x+4,grid.y+5))
        for i, key in enumerate(("help_mouse", "help_keys")):
            line = self.font.render(self.t(key), True, (243, 239, 222))
            rect = line.get_rect(center=(320, 343 + i * 9))
            pygame.draw.rect(surface, (20, 27, 34), rect.inflate(6, 4))
            surface.blit(line, rect)
