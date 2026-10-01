"""Keyboard and mouse menu. Layout and styling stay separate from actions."""
import pygame

from game import config
from game.screens.base_screen import BaseScreen
from game.ui.button import Button
from game.ui.actions import activate_button, is_confirmation
from game.ui.fonts import create_font


class MenuScreen(BaseScreen):
    VIRTUAL_WIDTH = 640
    VIRTUAL_HEIGHT = 360
    BACKGROUND = (22, 25, 32)
    PANEL = (31, 37, 45)
    ACCENT = (183, 208, 170)
    TEXT = (233, 235, 231)
    MUTED = (161, 174, 180)
    BUTTON_RECT = (40, 104, 272, 34)
    BUTTON_GAP = 35

    def __init__(self, game, return_screen=None):
        super().__init__(game)
        self.return_screen = return_screen
        self.title_font = create_font(28)
        self.font = create_font(14)
        self.small_font = create_font(10)
        self.language_saved = True
        self.page = 'main'
        self.selected = 0
        self.buttons = []
        self.descriptions = []
        self.open_page('options' if return_screen is not None else 'main')

    def open_page(self, page, selected=0):
        self.page = page
        if page == 'main':
            entries = [
                (self.game.localization.text("ui.menu.play"), self.game.start_new_run, self.game.localization.text("ui.menu.play_desc")),
                (self.game.localization.text("ui.menu.options"), lambda: self.open_page('options'), self.game.localization.text("ui.menu.options_desc")),
                (self.game.localization.text("ui.menu.controls"), lambda: self.open_page('controls'), self.game.localization.text("ui.menu.controls_desc")),
                (self.game.localization.text("ui.menu.practice"), lambda: self.open_page('practice'), self.game.localization.text("ui.menu.practice_desc")),
                (self.game.localization.text("ui.menu.room_editor"), self.open_room_editor, self.game.localization.text("ui.menu.room_editor_desc")),
                (self.game.localization.text("ui.menu.quit"), self.quit_game, self.game.localization.text("ui.menu.quit_desc")),
            ]
        elif page == 'options':
            entries = [
                (self.game.localization.text('ui.menu.language'), self.toggle_language,
                 self.game.localization.text('ui.menu.language_desc')),
                (self.game.localization.text("ui.menu.display") + (self.game.localization.text("ui.menu.fullscreen") if self.game.is_fullscreen else self.game.localization.text("ui.menu.window")),
                 self.toggle_fullscreen, self.game.localization.text("ui.menu.display_desc")),
                (self.game.localization.text("ui.menu.fps") + (self.game.localization.text("ui.menu.yes") if getattr(self.game, 'show_fps', True) else self.game.localization.text("ui.menu.no")),
                 self.toggle_fps, self.game.localization.text("ui.menu.fps_desc")),
                (self.game.localization.text("ui.menu.back"), self.back_from_options, self.game.localization.text('ui.pause.back_desc' if self.return_screen is not None else 'ui.menu.back_desc')),
            ]
        elif page == 'practice':
            entries = [
                (self.game.localization.text("ui.menu.golem"), lambda: self.game.start_boss_test('leaping'),
                 self.game.localization.text("ui.menu.golem_desc")),
                (self.game.localization.text("ui.menu.basic"), lambda: self.game.start_boss_test('basic'),
                 self.game.localization.text("ui.menu.basic_desc")),
                (self.game.localization.text("ui.menu.back"), lambda: self.open_page('main', 3), self.game.localization.text("ui.menu.back_desc")),
            ]
        else:
            entries = [(self.game.localization.text("ui.menu.back"), lambda: self.open_page('main', 2), '')]
        x, y, width, height = self.BUTTON_RECT
        self.buttons = [Button((x, y + i * self.BUTTON_GAP, width, height), label, action,
                               font_size=14) for i, (label, action, _) in enumerate(entries)]
        self.descriptions = [description for _, _, description in entries]
        self.selected = min(selected, len(self.buttons) - 1)

    def back_from_options(self):
        if self.return_screen is not None:
            self.game.screen_manager.set_screen(self.return_screen)
        else:
            self.open_page('main', 1)

    def open_room_editor(self):
        from game.screens.room_editor_screen import RoomEditorScreen
        self.game.screen_manager.set_screen(RoomEditorScreen(self.game))

    def quit_game(self):
        self.game.running = False

    def toggle_fullscreen(self):
        self.game.toggle_fullscreen()
        if self.page == 'options':
            self.open_page('options', self.selected)

    def toggle_language(self):
        language = "en" if self.game.localization.language == "es" else "es"
        self.language_saved = self.game.localization.set_language(language)
        self.open_page("options", self.selected)

    def toggle_fps(self):
        self.game.show_fps = not getattr(self.game, 'show_fps', True)
        self.open_page('options', self.selected)

    def virtual_pos(self, pos):
        # Derive from the current display, also before the first menu frame or
        # immediately after F12; never depend on stale screen render metrics.
        width, height = self.game.screen.get_size()
        scale = max(1, min(width // self.VIRTUAL_WIDTH, height // self.VIRTUAL_HEIGHT))
        return ((pos[0] - (width - self.VIRTUAL_WIDTH * scale) // 2) / scale,
                (pos[1] - (height - self.VIRTUAL_HEIGHT * scale) // 2) / scale)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F12:
                self.toggle_fullscreen()
            elif event.key == pygame.K_ESCAPE:
                if self.return_screen is not None:
                    self.back_from_options()
                else:
                    self.open_page('main', 0 if self.page == 'main' else 1)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.buttons)
            elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_TAB):
                step = -1 if event.key == pygame.K_TAB and event.mod & pygame.KMOD_SHIFT else 1
                self.selected = (self.selected + step) % len(self.buttons)
            elif is_confirmation(event):
                activate_button(self, self.selected)
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            pos = self.virtual_pos(event.pos)
            for index, button in enumerate(self.buttons):
                if button.rect.collidepoint(pos):
                    self.selected = index
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        activate_button(self, index)
                    break

    def text(self, surface, text, pos, font=None, color=None):
        surface.blit((font or self.font).render(text, True, color or self.TEXT), pos)

    def draw(self, surface):
        surface.fill(self.BACKGROUND)
        self.text(surface, 'GRIMORIUM', (40, 26), self.title_font)
        headings = {'main': self.game.localization.text("ui.menu.heading_main"), 'options': self.game.localization.text("ui.menu.heading_options"),
                    'controls': self.game.localization.text("ui.menu.heading_controls"), 'practice': self.game.localization.text("ui.menu.heading_practice")}
        self.text(surface, headings[self.page], (42, 69), self.small_font, self.ACCENT)
        pygame.draw.line(surface, (57, 68, 73), (40, 88), (600, 88))
        pygame.draw.rect(surface, self.PANEL, (336, 104, 264, 202), border_radius=8)
        for index, button in enumerate(self.buttons):
            button.draw(surface, focused=index == self.selected)
        if self.page == 'controls':
            self.text(surface, self.game.localization.text("ui.menu.how"), (354, 123), color=self.ACCENT)
            for index, (key, action) in enumerate([
                ('W A S D', self.game.localization.text("ui.menu.move")), (self.game.localization.text("ui.menu.arrows"), self.game.localization.text("ui.menu.shoot")),
                ('1 / 2 / 3', self.game.localization.text("ui.menu.weapon")), ('Enter / E', self.game.localization.text("ui.menu.shop")),
                ('Escape', self.game.localization.text("ui.menu.pause")), ('F12', self.game.localization.text("ui.menu.full_control")),
            ]):
                self.text(surface, key, (354, 155 + index * 22), self.small_font, self.ACCENT)
                self.text(surface, action, (445, 155 + index * 22), self.small_font)
        else:
            self.text(surface, self.game.localization.text("ui.menu.next"), (354, 123), self.small_font, self.ACCENT)
            for index, line in enumerate(self.descriptions[self.selected].splitlines()):
                self.text(surface, line, (354, 155 + index * 20), self.small_font)
            if self.page == 'options':
                self.text(surface, self.game.localization.text("ui.menu.session" if self.language_saved else "ui.menu.save_failed"), (354, 280), self.small_font, self.MUTED)
        self.text(surface, self.game.localization.text("ui.menu.footer"),
                  (40, 331), self.small_font, self.MUTED)
