"""Pantalla de pausa."""

import pygame

from game import config
from game.screens.base_screen import BaseScreen
from game.ui.button import Button
from game.ui.actions import activate_button, is_confirmation
from game.ui.fonts import create_font


class PauseScreen(BaseScreen):
    VIRTUAL_WIDTH = 640
    VIRTUAL_HEIGHT = 360
    def __init__(self, game, previous_screen):
        super().__init__(game)
        self.previous_screen = previous_screen
        frozen = pygame.Surface(previous_screen.get_virtual_size())
        previous_screen.draw(frozen)
        self.frozen = pygame.transform.scale(frozen, self.get_virtual_size())
        self.title_font = create_font(15)
        self.selected = 0
        self.buttons = []
        self.on_enter()

        self.overlay = pygame.Surface((self.VIRTUAL_WIDTH, self.VIRTUAL_HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 160))

    def on_enter(self):
        t = self.game.localization.text
        actions = [(t("ui.pause.resume"), self._resume),
                   (t("ui.menu.options"), self._options),
                   (t("ui.pause.menu"), self._go_menu)]
        self.buttons = [Button((220, 140 + index * 40, 200, 30), label, callback,
                               font_size=14)
                        for index, (label, callback) in enumerate(actions)]

    def _options(self):
        from game.screens.menu_screen import MenuScreen
        self.game.screen_manager.set_screen(MenuScreen(self.game, return_screen=self))

    def _resume(self):
        self.game.screen_manager.set_screen(self.previous_screen)

    def _go_menu(self):
        from game.screens.menu_screen import MenuScreen

        self.game.screen_manager.set_screen(MenuScreen(self.game))

    def screen_to_virtual(self, pos):
        return super().screen_to_virtual(pos)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if not getattr(event, "repeat", False):
                activate_button(self, 0)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F12:
                self.game.toggle_fullscreen()
            elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s, pygame.K_TAB):
                backwards = event.key in (pygame.K_UP, pygame.K_w) or (
                    event.key == pygame.K_TAB and event.mod & pygame.KMOD_SHIFT)
                self.selected = (self.selected + (-1 if backwards else 1)) % len(self.buttons)
            elif is_confirmation(event):
                activate_button(self, self.selected)
            return
        if event.type == pygame.MOUSEMOTION:
            for index, button in enumerate(self.buttons):
                if button.rect.collidepoint(self.screen_to_virtual(event.pos)):
                    self.selected = index

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = self.screen_to_virtual(event.pos)

            for index, button in enumerate(self.buttons):
                if button.rect.collidepoint(mouse_pos):
                    activate_button(self, index)
                    return

    def draw(self, surface):
        # Dibujamos antes la partida congelada debajo.
        surface.blit(self.frozen, (0, 0))

        surface_width = surface.get_width()

        surface.blit(self.overlay, (0, 0))

        title = self.title_font.render(self.game.localization.text("ui.pause.title"), True, config.HUD_COLOR)
        surface.blit(title, title.get_rect(center=(surface_width // 2, 110)))

        mouse_pos = self.screen_to_virtual(pygame.mouse.get_pos())

        for index, button in enumerate(self.buttons):
            button.draw(surface, focused=index == self.selected)
