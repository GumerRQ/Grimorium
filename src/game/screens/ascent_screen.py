"""Ascend over the persistent stack of previously visited rooms."""
import pygame
from game import config
from game.screens.base_screen import BaseScreen
from game.visuals.ascent_dust import AscentDust


class AscentScreen(BaseScreen):
    CAN_PAUSE = True
    VIRTUAL_WIDTH = 640
    VIRTUAL_HEIGHT = 360
    HOLD_SECONDS = .3

    def __init__(self, game, previous_room, destination):
        super().__init__(game)
        self.destination = destination
        self.previous_room = previous_room
        self.next_room = destination.capture_room_layer(include_enemies=True, include_structure=False)
        self.pivot = destination.room.perimeter_rect.center
        self.elapsed = 0.0
        self.duration = max(.1, config.TOWER_ASCENT_SECONDS)
        self.dust = (AscentDust(destination.capture_room_layer(include_structure=False),
                               self.pivot, self.duration)
                     if destination.tower_track.roof_removed else None)

    def update(self, dt):
        previous = min(self.duration, max(0.0, self.elapsed - self.HOLD_SECONDS))
        self.elapsed += max(0.0, dt)
        self.destination.tower_track.update(max(0.0, dt))
        current = min(self.duration, max(0.0, self.elapsed - self.HOLD_SECONDS))
        self.destination.tower_background.update(current - previous)
        end = self.dust.end_time if self.dust else self.duration
        if self.elapsed - self.HOLD_SECONDS >= end:
            self.game.screen_manager.set_screen(self.destination)

    @staticmethod
    def ease(value):
        value = max(0.0, min(1.0, value))
        return value * value * (3 - 2 * value)

    def draw(self, surface):
        progress = max(0.0, min(1.0, (self.elapsed - self.HOLD_SECONDS) / self.duration))
        amount = self.ease(progress)
        screen = self.destination
        screen.tower_background.draw(surface)
        history = self.game.run_state.tower_history
        previous_count = len(history.layers) - 1
        history.draw_below(surface, previous_count - 1 + amount, self.pivot, previous_count)
        # While descending, the incoming room passes in front of the entire HUD.
        if progress < 1.0:
            screen.draw_floor_track(surface)
            screen.draw_room_info(surface)
            screen.draw_hud(surface)
        # The arriving room alone comes into view; every older floor remains.
        scale = 1 + 1.1 * (1 - amount)
        reveal = self.ease(progress / .94)
        if reveal > 0:
            width, height = self.next_room.get_size()
            room = pygame.transform.scale(self.next_room, (round(width * scale), round(height * scale)))
            room.set_alpha(round(255 * reveal))
            surface.blit(room, (round(self.pivot[0] * (1 - scale)),
                                round(self.pivot[1] * (1 - scale))))
        if self.dust:
            self.dust.draw(surface, max(0, self.elapsed - self.HOLD_SECONDS))
        # Restore the HUD as soon as the room lands, even if dust is still fading.
        if progress >= 1.0:
            screen.draw_floor_track(surface)
            screen.draw_room_info(surface)
            screen.draw_hud(surface)
