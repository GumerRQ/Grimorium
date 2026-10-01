from pathlib import Path
p=Path('src/game/screens/hud_editor_screen.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace('        self.undo_stack = []','        self.undo_stack = []\n        self.redo_stack = []\n        self.grid_step = 1\n        self.clean_preview = False\n        self.edit_field = None\n        self.field_value = ""\n        self.field_replace = True\n        self.pick_index = 0')
s=s.replace('pygame.Rect(166, 5, 391, 112)','pygame.Rect(166, 5, 391, 137)')
s=s.replace('[("distribute", self.distribute), ("all_stats", self.select_stats)],','[("distribute", self.distribute), ("all_stats", self.select_stats), ("redo", self.redo)],')
s=s.replace('            for key, callback in entries:\n                width = 148 if row == 2 else 72','            for index, (key, callback) in enumerate(entries):\n                width = 148 if row == 2 and index < 2 else 72')
s=s.replace('        self.status = ""\n\n    def undo', '        self.status = ""\n        self.redo_stack.clear()\n\n    def undo')
s=s.replace('''        if self.undo_stack:
            self.layout.items = self.undo_stack.pop()''','''        if self.undo_stack:
            self.redo_stack.append(deepcopy(self.layout.items))
            self.layout.items = self.undo_stack.pop()''')
s=s.replace('    def reset(self):','''    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(deepcopy(self.layout.items))
            self.layout.items = self.redo_stack.pop()
        self.drag = None
        self.selected = [key for key in self.selected if key in self.layout.items]

    def fields(self):
        return [(pygame.Rect(172+i*79, 121, 75, 15), i) for i in range(4)]

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

    def reset(self):''')
s=s.replace('''    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:''','''    def handle_event(self, event):
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
        if event.type == pygame.KEYDOWN:''')
s=s.replace('''            elif ctrl and event.key == pygame.K_z:
                self.undo()''','''            elif ctrl and event.key == pygame.K_z:
                self.redo() if event.mod & pygame.KMOD_SHIFT else self.undo()
            elif ctrl and event.key == pygame.K_y:
                self.redo()
            elif event.key == pygame.K_h:
                self.clean_preview = not self.clean_preview
                self.drag = None''')
s=s.replace('''            for rect, key, callback in self.buttons:
                if rect.collidepoint(pos):''','''            if self.clean_preview:
                return
            for rect, index in self.fields():
                if rect.collidepoint(pos) and len(self.selected) == 1:
                    self.edit_field = index
                    self.field_value = str(self.layout.items[self.selected[0]]["rect"][index])
                    self.field_replace = True
                    return
            if pygame.Rect(493,121,55,15).collidepoint(pos):
                self.grid_step = {1:4, 4:8, 8:1}[self.grid_step]
                return
            for rect, key, callback in self.buttons:
                if rect.collidepoint(pos):''')
s=s.replace('            key = hits[0]','''            if pygame.key.get_mods() & pygame.KMOD_ALT:
                self.pick_index = (self.pick_index + 1) % len(hits)
            else:
                self.pick_index = 0
            key = hits[self.pick_index]''')
s=s.replace('''            if kind == "move":
                self.move_group(originals, dx, dy)''','''            if kind == "move":
                if self.grid_step > 1:
                    anchor = next(iter(originals.values()))
                    dx = round((anchor[0]+dx)/self.grid_step)*self.grid_step-anchor[0]
                    dy = round((anchor[1]+dy)/self.grid_step)*self.grid_step-anchor[1]
                self.move_group(originals, dx, dy)''')
a=s.index('                if self.layout.is_image(key):',s.index('elif event.type == pygame.MOUSEMOTION'))
b=s.index('        elif event.type == pygame.MOUSEBUTTONUP',a)
s=s[:a]+'''                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    old = pygame.Rect(originals[key])
                    scale = min(rect.w / old.w, (640-old.x)/old.w, (360-old.y)/old.h)
                    rect.size = (max(4,round(old.w*scale)), max(4,round(old.h*scale)))
                self.resize_element(key, rect, originals)
'''+s[b:]
s=s.replace('''        mouse = self.screen_to_virtual(pygame.mouse.get_pos())
        for key''','''        if self.clean_preview:
            label = self.font.render(self.t("preview_hint"), True, (245,235,199))
            pygame.draw.rect(surface, (20,27,34), (240,344,170,12))
            surface.blit(label, (245,347))
            return
        if self.grid_step > 1:
            for x in range(0,640,self.grid_step):
                for y in range(0,360,self.grid_step):
                    surface.set_at((x,y),(76,95,93))
        mouse = self.screen_to_virtual(pygame.mouse.get_pos())
        for key''')
s=s.replace('''        for i, key in enumerate(("help_mouse", "help_keys")):''','''        for rect,index in self.fields():
            pygame.draw.rect(surface,(60,82,77) if self.edit_field==index else (35,45,53),rect)
            value = self.field_value + "_" if self.edit_field==index else (
                str(self.layout.items[self.selected[0]]["rect"][index]) if len(self.selected)==1 else "-")
            label = self.font.render(("X", "Y", "W", "H")[index]+": "+value,True,(230,234,220))
            surface.blit(label,(rect.x+4,rect.y+5))
        pygame.draw.rect(surface,(44,61,64),(493,121,55,15))
        surface.blit(self.font.render(self.t("grid")+f" {self.grid_step}",True,(230,234,220)),(497,126))
        for i, key in enumerate(("help_mouse", "help_keys")):''')
p.write_text(s,encoding='utf-8')
# Room editor entry stays within the main menu's available vertical space.
p=Path('src/game/screens/menu_screen.py');s=p.read_text(encoding='utf-8')
s=s.replace('    BUTTON_GAP = 42','    BUTTON_GAP = 35')
s=s.replace('(self.game.localization.text("ui.menu.quit"), self.quit_game', '(self.game.localization.text("ui.menu.room_editor"), self.open_room_editor, self.game.localization.text("ui.menu.room_editor_desc")),\n                (self.game.localization.text("ui.menu.quit"), self.quit_game')
s=s.replace('    def quit_game(self):','''    def open_room_editor(self):
        from game.screens.room_editor_screen import RoomEditorScreen
        self.game.screen_manager.set_screen(RoomEditorScreen(self.game))

    def quit_game(self):''')
p.write_text(s,encoding='utf-8')
