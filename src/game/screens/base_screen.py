"""Clase base para todas las pantallas.

La idea es que todas las pantallas compartan la misma forma:
- reaccionar a eventos
- actualizarse
- dibujarse
"""
import pygame


class BaseScreen:
    CAN_PAUSE = False
    VIRTUAL_WIDTH = 320
    VIRTUAL_HEIGHT = 180

    def __init__(self, game):
        self.game = game
        self.virtual_surface = pygame.Surface(
            (self.VIRTUAL_WIDTH, self.VIRTUAL_HEIGHT)
        )

    def get_virtual_size(self):
        return self.VIRTUAL_WIDTH, self.VIRTUAL_HEIGHT

    def screen_to_virtual(self, pos):
        width, height = self.game.screen.get_size()
        scale = max(1, min(width // self.VIRTUAL_WIDTH, height // self.VIRTUAL_HEIGHT))
        return ((pos[0] - (width - self.VIRTUAL_WIDTH * scale) // 2) / scale,
                (pos[1] - (height - self.VIRTUAL_HEIGHT * scale) // 2) / scale)

    def on_enter(self):
        """Se llama al entrar en esta pantalla."""

    def on_exit(self):
        """Se llama justo antes de salir de esta pantalla."""

    def handle_event(self, event):
        """Aqui gestionas teclado, raton y otros eventos."""

    def update(self, dt):
        """Aqui actualizas logica del juego."""

    def draw(self, surface):
        """Aqui dibujas la pantalla."""
