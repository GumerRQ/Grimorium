import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame

from game.core.game import Game
from game.core.screen_manager import ScreenManager
from game.screens.intro_screen import IntroScreen
from game.screens.menu_screen import MenuScreen
from game.systems.localization import Localization


class FakeSequence:
    duration = 2.0

    def draw(self, surface, seconds):
        surface.fill((round(seconds * 50), 60, 90))


class IntroScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.mixer_patch = patch("pygame.mixer.get_init", return_value=None)
        self.mixer_patch.start()
        self.addCleanup(self.mixer_patch.stop)
        self.game = SimpleNamespace(
            screen_manager=ScreenManager(),
            screen=pygame.display.get_surface(),
            localization=Localization("es"),
            toggle_fullscreen=Mock(),
            start_new_run=Mock(),
            start_boss_test=Mock(),
            run_state=object(),
            show_fps=True,
            is_fullscreen=False,
        )
        self.destination = SimpleNamespace(on_enter=Mock(), on_exit=Mock())

    def intro(self, return_screen=True):
        screen = IntroScreen(self.game,
                             return_screen=self.destination if return_screen else None,
                             sequence=FakeSequence())
        self.game.screen_manager.set_screen(screen)
        return screen

    def key(self, key, repeat=False):
        self.game.screen_manager.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=key, repeat=repeat))

    def test_duration_finishes_once_without_changing_run_or_fps_preference(self):
        state = self.game.run_state
        screen = self.intro()
        screen.update(-5)
        self.assertEqual(screen.elapsed, 0)
        screen.update(1.5)
        self.assertIs(self.game.screen_manager.current_screen, screen)
        screen.update(100)
        screen.update(100)
        screen.finish()
        self.assertEqual(screen.elapsed, screen.sequence.duration)
        self.assertIs(self.game.screen_manager.current_screen, self.destination)
        self.destination.on_enter.assert_called_once()
        self.game.start_new_run.assert_not_called()
        self.assertIs(self.game.run_state, state)
        self.assertTrue(self.game.show_fps)
        self.assertFalse(screen.SHOW_FPS)

    def test_each_skip_key_works_through_screen_manager(self):
        for key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
            with self.subTest(key=key):
                screen = self.intro()
                self.key(key, repeat=True)
                self.assertIs(self.game.screen_manager.current_screen, screen)
                self.key(key)
                self.assertIs(self.game.screen_manager.current_screen, self.destination)
        self.game.start_new_run.assert_not_called()

    def test_startup_destination_is_menu(self):
        screen = self.intro(return_screen=False)
        screen.update(screen.sequence.duration)
        self.assertIsInstance(self.game.screen_manager.current_screen, MenuScreen)
        self.game.start_new_run.assert_not_called()

    def test_reenter_resets_clock_and_finish_guard(self):
        screen = self.intro()
        screen.update(2)
        self.game.screen_manager.set_screen(screen)
        self.assertEqual(screen.elapsed, 0)
        self.assertFalse(screen.finished)
        screen.update(1)
        self.assertIs(self.game.screen_manager.current_screen, screen)
        screen.finish()
        self.assertEqual(self.destination.on_enter.call_count, 2)

    def test_draw_does_not_advance_time(self):
        screen = self.intro()
        screen.update(.5)
        screen.draw(screen.virtual_surface)
        before = pygame.image.tobytes(screen.virtual_surface, "RGB")
        screen.draw(screen.virtual_surface)
        self.assertEqual(screen.elapsed, .5)
        self.assertEqual(before, pygame.image.tobytes(screen.virtual_surface, "RGB"))

    def test_fullscreen_and_mute_ignore_repeats(self):
        screen = self.intro()
        self.key(pygame.K_F12, repeat=True)
        self.game.toggle_fullscreen.assert_not_called()
        self.key(pygame.K_F12)
        self.game.toggle_fullscreen.assert_called_once()
        self.key(pygame.K_m, repeat=True)
        self.assertFalse(screen.muted)
        self.key(pygame.K_m)
        self.assertTrue(screen.muted)
        self.assertIs(self.game.screen_manager.current_screen, screen)

    def test_audio_uses_own_channel_and_mutes_without_restart(self):
        sound = Mock()
        channel = Mock(get_sound=Mock(return_value=sound))
        with patch("pygame.mixer.get_init", return_value=(44100, -16, 2)), \
             patch("game.screens.intro_screen.asset_path") as audio_path, \
             patch("pygame.mixer.Sound", return_value=sound), \
             patch("pygame.mixer.find_channel", return_value=channel):
            audio_path.return_value.is_file.return_value = True
            screen = self.intro()
            channel.play.assert_called_once_with(sound)
            self.key(pygame.K_m)
            channel.set_volume.assert_called_with(0.0)
            self.key(pygame.K_m)
            channel.set_volume.assert_called_with(1.0)
            channel.play.assert_called_once()
            screen.finish()
            channel.stop.assert_called_once()
            self.assertIsNone(screen._channel)

    def test_exit_does_not_stop_a_channel_reused_by_other_audio(self):
        screen = self.intro()
        screen._sound = Mock()
        channel = Mock(get_sound=Mock(return_value=object()))
        screen._channel = channel
        with patch("pygame.mixer.get_init", return_value=(44100, -16, 2)):
            screen.on_exit()
        channel.stop.assert_not_called()

    def test_missing_mixer_missing_wav_and_audio_errors_are_optional(self):
        with patch("pygame.mixer.Sound") as sound:
            self.intro()
            sound.assert_not_called()
        with patch("pygame.mixer.get_init", return_value=(44100, -16, 2)), \
             patch("game.screens.intro_screen.asset_path") as audio_path, \
             patch("pygame.mixer.Sound") as sound:
            audio_path.return_value.is_file.return_value = False
            self.intro()
            sound.assert_not_called()
            audio_path.return_value.is_file.return_value = True
            sound.side_effect = pygame.error("unavailable audio")
            screen = self.intro()
            screen.update(100)
            self.assertIs(self.game.screen_manager.current_screen, self.destination)

    def test_busy_audio_channels_do_not_block_intro(self):
        with patch("pygame.mixer.get_init", return_value=(44100, -16, 2)), \
             patch("game.screens.intro_screen.asset_path") as audio_path, \
             patch("pygame.mixer.Sound"), \
             patch("pygame.mixer.find_channel", return_value=None):
            audio_path.return_value.is_file.return_value = True
            screen = self.intro()
            screen.update(.5)
            self.assertEqual(screen.elapsed, .5)

    def test_game_starts_with_intro_and_replay_returns_to_same_options(self):
        def fake_intro(game, return_screen=None):
            return IntroScreen(game, return_screen, sequence=FakeSequence())

        def dummy_display(game):
            game.screen = pygame.display.set_mode((1280, 720))

        with patch.object(Game, "apply_display_mode", dummy_display), \
             patch("game.screens.intro_screen.IntroScreen", side_effect=fake_intro):
            game = Game()
            self.assertIsInstance(game.screen_manager.current_screen, IntroScreen)
            game.screen_manager.current_screen.finish()
            menu = game.screen_manager.current_screen
            menu.open_page("options", 3)
            menu.buttons[3].callback()
            replay = game.screen_manager.current_screen
            self.assertIsInstance(replay, IntroScreen)
            self.assertEqual(replay.elapsed, 0)
            replay.finish()
            self.assertIs(game.screen_manager.current_screen, menu)
            self.assertEqual(menu.page, "options")
            self.assertEqual(menu.selected, 3)


if __name__ == "__main__":
    unittest.main()
