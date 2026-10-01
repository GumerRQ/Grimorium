"""Gestiona que pantalla esta activa en cada momento."""

import pygame


class ScreenManager:
    """Guarda la pantalla actual y la cambia cuando haga falta."""

    def __init__(self):
        self.current_screen = None

    def set_screen(self, new_screen):
        """Cambia de pantalla.

        Si la pantalla anterior necesita limpiar algo, usa `on_exit`.
        Si la nueva necesita prepararse, usa `on_enter`.
        """
        if self.current_screen is not None:
            self.current_screen.on_exit()

        self.current_screen = new_screen

        if self.current_screen is not None:
            self.current_screen.on_enter()

    def handle_event(self, event):
        if self.current_screen is not None:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_F9, pygame.K_F5):
                if getattr(event, 'repeat', False):
                    return
                from game.screens.debug_screen import DebugScreen
                from game.screens.combat_screen import CombatScreen
                from game.screens.menu_screen import MenuScreen
                if isinstance(self.current_screen, (CombatScreen, MenuScreen)):
                    debug = DebugScreen(self.current_screen.game, self.current_screen)
                    self.set_screen(debug)
                    if event.key == pygame.K_F5:
                        debug.reload()
                    return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if getattr(event, "repeat", False):
                    return
                if self.current_screen.CAN_PAUSE:
                    from game.screens.pause_screen import PauseScreen
                    self.set_screen(PauseScreen(self.current_screen.game, self.current_screen))
                    return
            self.current_screen.handle_event(event)

    def update(self, dt):
        if self.current_screen is not None:
            self.current_screen.update(dt)

    def draw(self, surface):
        if self.current_screen is not None:
            self.current_screen.draw(surface)
