"""Bucle principal del juego.

Este archivo es el "corazon" del proyecto.
Lo normal es que aqui no metas logica de enemigos o balas:
solo coordina el juego y deja el trabajo a las pantallas.
"""

import pygame
import secrets
from game.systems.run_random import content_random

from game import config
from game.core.screen_manager import ScreenManager
from game.core.run_state import RunState
from game.config import RUN_PATTERN
from game.systems.localization import Localization
from game.visuals.tower_background import TowerBackground

from game.screens.menu_screen import MenuScreen
from game.screens.play_screen import PlayScreen
from game.screens.shop_screen import ShopScreen
from game.screens.boss_screen import BossScreen
from game.screens.game_over_screen import GameOverScreen
from game.screens.ascent_screen import AscentScreen



class Game:
    """Objeto principal que arranca pygame y mantiene el bucle general."""

    def __init__(self):
        pygame.init()
        # Keyboard/mouse only. Pygame 2.6.1 can raise KeyError inside
        # event.get() for an unmapped joystick removal (pygame issue #3954).
        # Block before quitting: set_blocked also removes queued device events.
        pygame.event.set_blocked((
            pygame.JOYAXISMOTION, pygame.JOYBALLMOTION, pygame.JOYHATMOTION,
            pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP,
            pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED,
            pygame.CONTROLLERAXISMOTION,
            pygame.CONTROLLERBUTTONDOWN, pygame.CONTROLLERBUTTONUP,
            pygame.CONTROLLERDEVICEADDED, pygame.CONTROLLERDEVICEREMOVED,
            pygame.CONTROLLERDEVICEREMAPPED,
        ))
        pygame.joystick.quit()
        pygame.font.init()

        self.screen = None
        self.is_fullscreen = False
        self.apply_display_mode()
        pygame.display.set_caption(config.WINDOW_TITLE)
        self.localization = Localization()
        self.run_state = RunState()

        self.clock = pygame.time.Clock()
        self.running = True
        self.screen_manager = ScreenManager()

        self.tower_background = None
        self.previous_room_layer = None

        self.debug_font = pygame.font.Font(None, 24)
        self.show_fps = True       

        self.start_intro()


    def start_intro(self, return_screen=None):
        from game.screens.intro_screen import IntroScreen
        self.screen_manager.set_screen(IntroScreen(self, return_screen=return_screen))


    def go_to_next_run_screen(self):
        step = self.run_state.advance(RUN_PATTERN)

        if step == "normal":
            self.enter_combat_screen(PlayScreen(self))
        elif step == "shop":
            with self.content_random('shop'):
                self.screen_manager.set_screen(ShopScreen(self))
        elif step == "boss":
            self.enter_combat_screen(BossScreen(self))
        else:
            raise ValueError(f"Paso desconocido: {step}")


    def enter_combat_screen(self, screen):
        self.run_state.tower_history.record(screen)
        screen.room.structure = self.run_state.tower_history.underlay(screen)
        previous = self.previous_room_layer
        self.previous_room_layer = None
        if previous is not None:
            screen = AscentScreen(self, previous, screen)
        self.screen_manager.set_screen(screen)

    def finish_current_screen(self, source):
        if source is not self.screen_manager.current_screen or getattr(source, '_transitioned', False):
            return
        if hasattr(source, 'room_flow') and source.room_flow.result.phase != 'leaving':
            return
        if not hasattr(source, 'room_flow') and not isinstance(source, ShopScreen):
            return
        source._transitioned = True
        if self.run_state.mode == "boss_test":
            self.screen_manager.set_screen(MenuScreen(self))
            return

        # Save only the cleared room, before the shop changes the shared player.
        # Keep it across the shop so the ascent always starts on the previous floor.
        if self.run_state.current_step in ("normal", "boss"):
            current = self.screen_manager.current_screen
            self.run_state.tower_history.complete(current)
            self.previous_room_layer = current.capture_room_layer(include_structure=False)

        if self.run_state.finish_step(RUN_PATTERN):
            self.screen_manager.set_screen(GameOverScreen(self))
            return
        self.go_to_next_run_screen()

    def content_random(self, section):
        return content_random(self.run_state.run_seed, f'{section}:{self.run_state.run_cycles}:{self.run_state.current_step_index}')

    def start_new_run(self, seed=None):
        chosen_seed = str(seed).strip() if seed is not None and str(seed).strip() else str(secrets.randbits(32))
        self.run_state = RunState(run_seed=chosen_seed, mode="normal_run")
        self.previous_room_layer = None
        self.tower_background = None
        self.go_to_next_run_screen()

    def start_boss_test(self, boss_type="basic"):
        self.run_state = RunState(mode="boss_test", current_step="boss")
        self.previous_room_layer = None
        self.tower_background = None
        self.screen_manager.set_screen(BossScreen(self, boss_type=boss_type))

    def get_tower_floor_index(self):
        return self.run_state.floor_index(RUN_PATTERN)

    def get_tower_background(self):
        if self.tower_background is None:
            floors_per_loop = sum(step in ("normal", "boss") for step in RUN_PATTERN)
            self.tower_background = TowerBackground(floors_per_loop * self.run_state.max_cycles)
        return self.tower_background


    def run(self):
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    continue

                self.screen_manager.handle_event(event)

            self.screen_manager.update(dt)

            current_screen = self.screen_manager.current_screen
            self.update_render_metrics(current_screen)
            virtual_surface = current_screen.virtual_surface

            virtual_surface.fill(config.BACKGROUND_COLOR)
            current_screen.draw(virtual_surface)

            scaled_surface = pygame.transform.scale(
                virtual_surface,
                (self.render_width, self.render_height)
            )

            self.screen.fill((0, 0, 0))
            self.screen.blit(
                scaled_surface,
                (self.render_offset_x, self.render_offset_y)
            )

            if self.show_fps and getattr(current_screen, "SHOW_FPS", True):
                fps = self.clock.get_fps()
                ms = 1000 / fps if fps > 0 else 0
                fps_text = self.debug_font.render(f"FPS: {fps:.1f}  MS: {ms:.2f}", True, (255, 255, 0))
                self.screen.blit(fps_text, (20, 20))

            pygame.display.flip()

        pygame.quit()


    def update_render_metrics(self, current_screen):
        vw, vh = current_screen.get_virtual_size()

        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        self.render_scale = min(
            screen_width // vw,
            screen_height // vh,
        )

        self.render_width = vw * self.render_scale
        self.render_height = vh * self.render_scale

        self.render_offset_x = (screen_width - self.render_width) // 2
        self.render_offset_y = (screen_height - self.render_height) // 2

    def apply_display_mode(self):
        if self.is_fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode(
                (info.current_w, info.current_h),
                pygame.FULLSCREEN | pygame.SCALED
            )
        else:
            self.screen = pygame.display.set_mode(
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
                pygame.SCALED
            )

        pygame.display.set_caption(config.WINDOW_TITLE)

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.apply_display_mode()
