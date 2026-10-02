"""Exercise the shipped drawings and timeline, beyond screen lifecycle mocks."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import wave

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame

from game.core.game import Game
from game.screens.intro_screen import IntroScreen
from game.screens.menu_screen import MenuScreen
from game.visuals.intro_sequence import IntroSequence


class IntroSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((640, 360))
        cls.sequence = IntroSequence()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_shipped_audio_and_visual_timeline_end_together(self):
        with wave.open(str(self.sequence.root / "intro-audio.wav"), "rb") as audio:
            seconds = audio.getnframes() / audio.getframerate()
        self.assertAlmostEqual(seconds, self.sequence.duration, places=3)
        self.assertFalse(any(name.isdigit() for _, name in self.sequence.layers))

    def test_can_seek_backwards_across_every_cut_without_changing_frames(self):
        surface = pygame.Surface(self.sequence.size)
        times = sorted(set([0, .8, 5.53, 7.2, 13.8, 19.5] +
                           [max(0, t + delta) for t in self.sequence.ends
                            for delta in (-.001, 0, .001)]))
        frames = {}
        for time in times:
            self.sequence.draw(surface, time)
            frames[time] = pygame.image.tobytes(surface, "RGB")
        for time in reversed(times):
            self.sequence.draw(surface, time)
            self.assertEqual(frames[time], pygame.image.tobytes(surface, "RGB"))
        self.assertGreater(len(set(frames.values())), 10)

    def test_invalid_render_target_or_time_is_rejected(self):
        with self.assertRaises(ValueError):
            self.sequence.draw(pygame.Surface((640, 360)), 0)
        for time in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(time=time), self.assertRaises(ValueError):
                self.sequence.draw(pygame.Surface(self.sequence.size), time)

    def test_real_game_can_render_finish_and_replay_the_shipped_intro(self):
        def dummy_display(game):
            game.screen = pygame.display.set_mode((1280, 720))

        with patch.object(Game, "apply_display_mode", dummy_display):
            game = Game()
            intro = game.screen_manager.current_screen
            self.assertIsInstance(intro, IntroScreen)
            self.assertIsInstance(intro.sequence, IntroSequence)
            self.assertEqual(intro.virtual_surface.get_size(), (320, 180))
            self.assertEqual(intro.sequence.size, (320, 180))
            intro.update(5.53)
            intro.draw(intro.virtual_surface)
            intro.update(intro.sequence.duration)
            menu = game.screen_manager.current_screen
            self.assertIsInstance(menu, MenuScreen)
            game.start_intro(return_screen=menu)
            replay = game.screen_manager.current_screen
            replay.update(13.8)
            replay.draw(replay.virtual_surface)
            replay.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
            self.assertIs(game.screen_manager.current_screen, menu)


if __name__ == "__main__":
    unittest.main()
