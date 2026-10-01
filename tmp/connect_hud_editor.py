from pathlib import Path

def edit(file,old,new):
 p=Path(file);s=p.read_text(encoding='utf-8-sig');assert old in s,(file,old);p.write_text(s.replace(old,new),encoding='utf-8')
p='src/game/screens/combat_screen.py'
edit(p,'        # Combat background','        from game.ui.hud_layout import HudLayout\n        if not hasattr(game, "hud_layout"):\n            game.hud_layout = HudLayout()\n        self.hud_layout = game.hud_layout\n\n        # Combat background')
edit(p,'    def handle_event(self, event):','''    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F8:
            if not getattr(event, "repeat", False):
                from game.screens.hud_editor_screen import HudEditorScreen
                self.game.screen_manager.set_screen(HudEditorScreen(self.game, self))
            return''')
edit(p,'    def draw(self, surface):','    def draw_scene(self, surface):')
edit(p,'''        self.draw_room_info(surface)
        self.draw_floor_track(surface)

        self.draw_extra(surface)
        self.draw_hud(surface)''','''        self.draw_extra(surface)

    def draw(self, surface):
        self.draw_scene(surface)
        self.draw_room_info(surface)
        self.draw_floor_track(surface)
        self.draw_hud(surface)''')
edit(p,'''        text = self.font.render(self.game.localization.text("ui.combat.time").format(seconds=self.room_time), True, config.HUD_COLOR)
        surface.blit(text, text.get_rect(center=(53, 55)))''','''        self.hud_layout.draw_text(surface, self.font,
                                  self.game.localization.text("ui.combat.time").format(seconds=self.room_time),
                                  "time", config.HUD_COLOR)''')
edit(p,'self.game.get_tower_floor_index(), self.game.localization)','self.game.get_tower_floor_index(), self.game.localization, self.hud_layout)')
edit(p,'self.player.draw_player_stats(surface, self.font, self.stat_positions)','self.player.draw_player_stats(surface, self.font, self.stat_positions, self.hud_layout)')
edit(p,'self.player.draw_player_health(surface, self.font)','self.player.draw_player_health(surface, self.font, self.hud_layout)')
p='src/game/entities/player.py'
edit(p,'def draw_player_health(self, surface, font):','def draw_player_health(self, surface, font, layout=None):')
edit(p,'        y = 15\n','        y = 15\n        if layout is not None:\n            x, y, bar_width, bar_height = layout.rect("health_bar")\n')
edit(p,'        text_rect = text.get_rect(center=background_rect.center)\n        surface.blit(text, text_rect)','''        if layout is not None:
            layout.draw_text(surface, font, f"{int(self.health)} / {self.max_health}",
                             "health_text", (255, 255, 255))
        else:
            text_rect = text.get_rect(center=background_rect.center)
            surface.blit(text, text_rect)''')
edit(p,'def draw_player_stats(self, surface, font, stat_positions):','def draw_player_stats(self, surface, font, stat_positions, layout=None):')
edit(p,'        for stat_name, text_value in stat_lines.items():','''        for stat_name, text_value in stat_lines.items():
            if layout is not None:
                if stat_name in layout.items:
                    layout.draw_text(surface, font, text_value, stat_name, config.HUD_COLOR)
                continue''')
p='src/game/visuals/tower_track.py'
edit(p,'def draw(self, surface, history, font, current_floor, localization):','''def draw(self, surface, history, font, current_floor, localization, layout=None):
        if layout is not None:
            # Keep tower animation coordinates independent of the editable viewport.
            scratch = pygame.Surface((640, 360), pygame.SRCALPHA)
            self.draw(scratch, history, font, current_floor, localization)
            pygame.draw.rect(surface, (20, 27, 34), (568, 64, 55, 267))
            target = layout.rect("tower_view")
            view = scratch.subsurface((568, 88, 55, 167))
            surface.blit(pygame.transform.scale(view, target.size), target)
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
            return''')
