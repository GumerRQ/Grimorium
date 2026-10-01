"""Pantalla de game over, basada en la version simple."""

import pygame

from game import config
from game.screens.base_screen import BaseScreen
from game.ui.fonts import create_font
from game.ui.button import Button
from game.ui.actions import activate_button, is_confirmation


class GameOverScreen(BaseScreen):
    VIRTUAL_WIDTH = 640
    VIRTUAL_HEIGHT = 360

    def __init__(self, game):
        super().__init__(game)
        self.final_score = self.game.run_state.player.coins
        self.title_font = create_font(15)
        self.info_font = create_font(8)
        self.history = game.run_state.tower_history
        self.won = game.run_state.run_cycles >= game.run_state.max_cycles and game.run_state.player.health > 0
        self.history.save("completed" if self.won else "defeated")
        self.tower_view = pygame.Surface(self.get_virtual_size(), pygame.SRCALPHA)
        self.history.draw_side(self.tower_view, 437, 300, 230)
        self.selected = 0
        self.buttons = [Button((40, 207, 230, 32), self.game.localization.text("ui.end.again"), game.start_new_run, font_size=14),
                        Button((40, 249, 230, 32), self.game.localization.text("ui.end.menu"), self.go_menu, font_size=14)]

    def go_menu(self):
        from game.screens.menu_screen import MenuScreen
        self.game.screen_manager.set_screen(MenuScreen(self.game))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if is_confirmation(event):
                activate_button(self, self.selected)
            elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s, pygame.K_TAB):
                self.selected = (self.selected + 1) % len(self.buttons)

            elif event.key == pygame.K_ESCAPE:
                if not getattr(event, 'repeat', False):
                    activate_button(self, 1)
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            for index, button in enumerate(self.buttons):
                if button.rect.collidepoint(self.screen_to_virtual(event.pos)):
                    self.selected = index
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        activate_button(self, index)
                    break

    def draw(self, surface):
        surface.fill(config.BACKGROUND_COLOR)

        surface_width = surface.get_width()
        surface_height = surface.get_height()

        title = self.title_font.render(self.game.localization.text("ui.end.win") if self.won else self.game.localization.text("ui.end.lose"), True, config.HUD_COLOR)
        score = self.info_font.render(self.game.localization.text("ui.end.score").format(score=self.final_score), True, config.HUD_COLOR)
        info = self.info_font.render(self.game.localization.text("ui.end.hint"), True, config.HUD_COLOR)

        surface.blit(self.tower_view, (0, 0))
        surface.blit(title, title.get_rect(center=(155, 100)))
        surface.blit(score, score.get_rect(center=(155, 140)))
        floors = self.info_font.render(self.game.localization.text("ui.end.floors").format(count=len(self.history.floors)), True, config.HUD_COLOR)
        surface.blit(floors, floors.get_rect(center=(155, 165)))
        label = self.info_font.render(self.game.localization.text("ui.end.tower"), True, config.HUD_COLOR)
        surface.blit(label, label.get_rect(center=(437, 28)))
        surface.blit(info, info.get_rect(center=(surface_width // 2, surface_height - 20)))
        for index, button in enumerate(self.buttons):
            button.draw(surface, focused=index == self.selected)
