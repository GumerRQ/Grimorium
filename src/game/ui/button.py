"""Boton basico reutilizable para menus."""

import pygame

from game import config
from game.ui.fonts import create_font


class Button:
    def __init__(self, rect, text, callback, font_size=42):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.font = create_font(font_size)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, surface, mouse_pos=None, focused=False):
        hovered = focused or (mouse_pos is not None and self.rect.collidepoint(mouse_pos))
        color = (getattr(config, "BUTTON_HOVER_COLOR", (56, 73, 70)) if hovered
                 else getattr(config, "BUTTON_COLOR", (37, 44, 54)))

        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        if focused:
            pygame.draw.rect(surface, (183, 208, 170), self.rect, width=2, border_radius=10)

        text_surface = self.font.render(self.text, True, config.HUD_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
