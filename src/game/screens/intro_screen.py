"""Play the illustrated opening without changing or starting a run."""
import pygame

from game.screens.base_screen import BaseScreen
from game.ui.fonts import create_font
from game.utils.paths import asset_path


class IntroScreen(BaseScreen):
    VIRTUAL_WIDTH = 320
    VIRTUAL_HEIGHT = 180
    CAN_PAUSE = False
    SHOW_FPS = False

    def __init__(self, game, return_screen=None, sequence=None):
        super().__init__(game)
        if sequence is None:
            from game.visuals.intro_sequence import IntroSequence
            sequence = IntroSequence(size=self.get_virtual_size())
        self.sequence = sequence
        self.return_screen = return_screen
        self.elapsed = 0.0
        self.finished = False
        self.muted = False
        self._sound = None
        self._channel = None
        self.hint_font = create_font(10)

    def on_enter(self):
        self.elapsed = 0.0
        self.finished = False
        self._stop_audio()
        if not pygame.mixer.get_init():
            return
        audio_path = asset_path("video", "intro", "intro-audio.wav")
        if not audio_path.is_file():
            return
        try:
            self._sound = pygame.mixer.Sound(str(audio_path))
            self._channel = pygame.mixer.find_channel()
            if self._channel is not None:
                self._channel.set_volume(0.0 if self.muted else 1.0)
                self._channel.play(self._sound)
        except (pygame.error, OSError):
            # Sound is optional: a missing device or unsupported WAV must not
            # prevent the intro, or the rest of the game, from starting.
            self._stop_audio()

    def _owns_channel(self):
        return (self._channel is not None and pygame.mixer.get_init()
                and self._channel.get_sound() is self._sound)

    def _stop_audio(self):
        if self._owns_channel():
            self._channel.stop()
        self._channel = None
        self._sound = None

    def on_exit(self):
        self._stop_audio()

    def finish(self):
        if self.finished or self.game.screen_manager.current_screen is not self:
            return
        self.finished = True
        destination = self.return_screen
        if destination is None:
            from game.screens.menu_screen import MenuScreen
            destination = MenuScreen(self.game)
        self.game.screen_manager.set_screen(destination)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or getattr(event, "repeat", False):
            return
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                         pygame.K_SPACE, pygame.K_ESCAPE):
            self.finish()
        elif event.key == pygame.K_F12:
            self.game.toggle_fullscreen()
        elif event.key == pygame.K_m:
            self.muted = not self.muted
            if self._owns_channel():
                self._channel.set_volume(0.0 if self.muted else 1.0)

    def update(self, dt):
        if self.finished:
            return
        self.elapsed = min(self.sequence.duration, self.elapsed + max(0.0, dt))
        if self.elapsed >= self.sequence.duration:
            self.finish()

    def draw(self, surface):
        self.sequence.draw(surface, self.elapsed)
        text = self.game.localization.text("ui.intro.skip")
        text += "   |   " + self.game.localization.text(
            "ui.intro.unmute" if self.muted else "ui.intro.mute")
        hint = self.hint_font.render(text, True, (255, 255, 255))
        backing = pygame.Surface((hint.get_width() + 16, hint.get_height() + 10),
                                 pygame.SRCALPHA)
        backing.fill((15, 18, 22, 180))
        backing.blit(hint, (8, 5))
        surface.blit(backing, (surface.get_width() - backing.get_width() - 10,
                               surface.get_height() - backing.get_height() - 8))
