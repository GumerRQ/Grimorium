from pathlib import Path
p=Path('src/game/screens/hud_editor_screen.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace('        self.drag = None\n        self.status = ""','        self.drag = None\n        self.mode = "all"\n        self.status = ""',1)
s=s.replace('pygame.Rect(166, 5, 391, 91)','pygame.Rect(166, 5, 391, 112)')
s=s.replace('''            [("distribute", self.distribute), ("all_stats", self.select_stats)],''','''            [("distribute", self.distribute), ("all_stats", self.select_stats)],
            [("mode", self.cycle_mode), ("add_png", self.add_png), ("reload", self.reload_art),
             ("group", self.group_selection), ("visibility", self.toggle_visibility)],''')
s=s.replace('    def remember(self):','''    def eligible_keys(self):
        return [key for key in self.layout.items
                if self.mode == "all" or self.layout.is_image(key) == (self.mode == "images")]

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
        self.layout.items[panel]["members"] = members
        self.status = self.t("grouped")

    def toggle_visibility(self):
        self.remember()
        for key in self.selected:
            if self.layout.is_image(key):
                item = self.layout.items[key]
                item["visible"] = not item.get("visible", True)

    def remember(self):''')
s=s.replace('''        self.drag = None

    def reset''','''        self.drag = None
        self.selected = [key for key in self.selected if key in self.layout.items]

    def reset''')
s=s.replace('        self.layout.items = deepcopy(DEFAULTS)','        self.layout.items = deepcopy(DEFAULTS)\n        self.selected = []')
s=s.replace('        self.selected = ["damage",','        self.mode = "all"\n        self.selected = ["damage",')
s=s.replace('if key not in ("health_bar", "tower_view"):', 'if key not in ("health_bar", "tower_view") and not self.layout.is_image(key):')
# Move a panel and its children together when aligning/distributing too.
s=s.replace('            self.put_rect(key, rect)\n\n    def distribute', '''            self.move_element(key, rect)

    def distribute''')
s=s.replace('            self.put_rect(key, rect)\n\n    def move_group', '''            self.move_element(key, rect)

    def move_element(self, key, rect):
        previous = self.layout.rect(key)
        originals = {k: self.layout.items[k]["rect"][:] for k in self.layout.movement_keys([key])}
        self.move_group(originals, rect.x - previous.x, rect.y - previous.y)

    def move_group''')
s=s.replace('''            elif ctrl and event.key == pygame.K_z:
                self.undo()''','''            elif ctrl and event.key == pygame.K_z:
                self.undo()
            elif ctrl and event.key == pygame.K_o:
                self.add_png()
            elif ctrl and event.key == pygame.K_g:
                self.group_selection()
            elif event.key == pygame.K_g:
                self.cycle_mode()
            elif event.key == pygame.K_r:
                self.reload_art()
            elif event.key == pygame.K_DELETE:
                self.toggle_visibility()''')
s=s.replace('''                keys = list(self.layout.items)
                index = keys.index(self.selected[-1]) if self.selected else -1
                self.selected = [keys[(index + (-1 if event.mod & pygame.KMOD_SHIFT else 1)) % len(keys)]]''','''                keys = self.eligible_keys()
                index = keys.index(self.selected[-1]) if self.selected and self.selected[-1] in keys else -1
                if keys:
                    self.selected = [keys[(index + (-1 if event.mod & pygame.KMOD_SHIFT else 1)) % len(keys)]]''')
s=s.replace('self.move_group({k: self.layout.items[k]["rect"][:] for k in self.selected}, dx, dy)','self.move_group(self.originals(), dx, dy)')
s=s.replace('self.drag = ("resize", pos, {key: list(rect)})','self.drag = ("resize", pos, self.originals())')
s=s.replace('hits = [k for k in reversed(self.layout.items) if self.layout.rect(k).collidepoint(pos)]','''keys = self.eligible_keys()
            # Text zones take priority in All mode; use Images mode to grab whole panels.
            keys.sort(key=lambda k: not self.layout.is_image(k))
            hits = [k for k in reversed(keys) if self.layout.rect(k).collidepoint(pos)]''')
s=s.replace('self.drag = ("move", pos, {k: self.layout.items[k]["rect"][:] for k in self.selected})','self.drag = ("move", pos, self.originals())')
s=s.replace('''                self.put_rect(key, rect)
        elif event.type == pygame.MOUSEBUTTONUP''','''                if self.layout.is_image(key):
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
        elif event.type == pygame.MOUSEBUTTONUP''')
s=s.replace('''        self.combat.draw_room_info(surface)
        self.combat.draw_floor_track(surface)''','''        self.combat.draw_floor_track(surface)
        self.combat.draw_room_info(surface)''')
s=s.replace('        for key in self.layout.items:\n            rect =', '        for key in self.eligible_keys():\n            rect =')
s=s.replace('''            label = self.font.render(self.t(key), True, (236, 237, 221))''','''            label = self.font.render(self.t("mode_" + self.mode) if key == "mode" else self.t(key),
                                     True, (236, 237, 221))''')
s=s.replace("self.t('names.' + key)","self.name(key)")
s=s.replace('''        surface.blit(self.font.render(info, True, (228, 232, 220)), (173, 76))''','''        surface.blit(self.font.render(info, True, (228, 232, 220)), (173, 93))''')
s=s.replace('(173, 86)', '(173, 104)')
p.write_text(s,encoding='utf-8')
import json
updates={
'es':{'mode_all':'Todo [G]','mode_images':'Graficos [G]','mode_text':'Contenido [G]', 'add_png':'Anadir PNG', 'reload':'Recargar [R]', 'group':'Vincular', 'visibility':'Ver / ocultar',
'imported':'PNG anadido. Guarda para conservarlo en el HUD.', 'import_error':'No se pudo importar. Elige un PNG valido.', 'reloaded':'PNG recargados.', 'reload_error':'No se pudo recargar: revisa los archivos PNG.',
'group_hint':'Selecciona un grafico y sus textos (Shift+clic).', 'grouped':'Contenido vinculado al panel.',
'help_mouse':'G: modo de seleccion | Arrastra el panel con su contenido | Shift+clic: varios | Esquina: tamano',
'help_keys':'Ctrl+O: PNG | R: recargar | Ctrl+G: vincular | Ctrl+S: guardar | Ctrl+Z: deshacer | F8: listo | Esc: cancelar'},
'en':{'mode_all':'All [G]','mode_images':'Graphics [G]','mode_text':'Content [G]', 'add_png':'Add PNG', 'reload':'Reload [R]', 'group':'Link content', 'visibility':'Show / hide',
'imported':'PNG added. Save to keep it in the HUD.', 'import_error':'Could not import. Choose a valid PNG.', 'reloaded':'PNG files reloaded.', 'reload_error':'Could not reload: check the PNG files.',
'group_hint':'Select one graphic and its text zones (Shift+click).', 'grouped':'Content linked to panel.',
'help_mouse':'G: selection mode | Drag panel with its content | Shift+click: multi-select | Corner: resize',
'help_keys':'Ctrl+O: PNG | R: reload | Ctrl+G: link | Ctrl+S: save | Ctrl+Z: undo | F8: done | Esc: cancel'}}
for lang,entries in updates.items():
 p=Path('data/lang')/(lang+'.json');data=json.loads(p.read_text(encoding='utf-8'));data['ui']['hud_editor'].update(entries)
 data['ui']['hud_editor']['names'].update(stats_panel='Panel izquierdo' if lang=='es' else 'Left panel',tower_panel='Marco de torre' if lang=='es' else 'Tower frame')
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
import ast
for p in Path('src').rglob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
print('Editor graphics mode, PNG import, reload, linking and syntax OK.')
