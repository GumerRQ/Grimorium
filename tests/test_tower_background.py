import os
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame

from game import config
from game.core.game import Game
from game.screens.game_over_screen import GameOverScreen
from game.visuals.tower_background import TowerBackground
from game.utils.paths import asset_path


def dummy_display(game):
    game.screen = pygame.display.set_mode((1280, 720))


class TowerBackgroundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((640, 360))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.background = TowerBackground(18)
        self.surface = pygame.Surface((640, 360))

    def test_ascent_is_gradual_and_finishes_exactly(self):
        bg = self.background
        bg.set_floor(1)
        self.assertEqual(bg.floor, 0)
        previous = bg.floor
        for _ in range(60):
            bg.update(config.TOWER_ASCENT_SECONDS / 60)
            self.assertGreaterEqual(bg.floor, previous)
            self.assertLessEqual(bg.floor, 1)
            previous = bg.floor
        self.assertAlmostEqual(bg.floor, 1)
        bg.update(100)
        self.assertEqual(bg.floor, 1)

    def test_retarget_does_not_jump_or_restart_when_unchanged(self):
        bg = self.background
        bg.set_floor(1)
        bg.update(config.TOWER_ASCENT_SECONDS / 2)
        self.assertAlmostEqual(bg.floor, .5)
        bg.set_floor(1)
        bg.update(config.TOWER_ASCENT_SECONDS / 2)
        self.assertEqual(bg.floor, 1)
        bg.set_floor(2)
        bg.update(config.TOWER_ASCENT_SECONDS / 2)
        height = bg.floor
        bg.set_floor(3)
        self.assertEqual(bg.floor, height)
        bg.update(config.TOWER_ASCENT_SECONDS)
        self.assertEqual(bg.floor, 3)

    def test_draw_does_not_advance_time_and_no_gaps_at_any_height(self):
        bg = self.background
        for floor in range(18):
            bg.set_floor(floor, immediate=True)
            self.surface.fill((255, 0, 255))
            bg.draw(self.surface)
            first = pygame.image.tobytes(self.surface, "RGB")
            bg.draw(self.surface)
            self.assertEqual(first, pygame.image.tobytes(self.surface, "RGB"))
            self.assertEqual(bg.floor, floor)
            self.assertEqual(bg.cloud_time, 0)
            for point in ((0, 0), (639, 0), (0, 359), (639, 359)):
                self.assertNotEqual(self.surface.get_at(point)[:3], (255, 0, 255))
        # The minimum zoom also covers the viewport in longer configured runs.
        bg.total_floors = 1000
        bg.set_floor(999, immediate=True)
        bg.draw(self.surface)
        self.assertEqual(bg.ground_scale, config.TOWER_MIN_GROUND_SCALE)

    def test_terrain_stays_identical_and_does_not_consume_combat_randomness(self):
        state = random.getstate()
        other = TowerBackground(18, seed=self.background.seed)
        self.assertEqual(state, random.getstate())
        original = pygame.image.tobytes(self.background.terrain, "RGB")
        self.assertEqual(original, pygame.image.tobytes(other.terrain, "RGB"))
        self.background.set_floor(17)
        self.background.update(20)
        self.background.draw(self.surface)
        self.assertEqual(original, pygame.image.tobytes(self.background.terrain, "RGB"))

    def test_png_alpha_preserves_hud_panels(self):
        hud = pygame.image.load(asset_path("images", "backgrounds", "tower", "combat_hud.png"))
        self.assertEqual(hud.get_at((320, 10)).a, 0)
        self.assertEqual(hud.get_at((595, 271)).a, 255)
        self.assertEqual(hud.get_at((595, 307)).a, 255)
        self.assertGreater(hud.get_at((21, 45)).a, 0)
        for name in TowerBackground.ASSET_NAMES:
            if name != "ground_moss":
                sprite = self.background._sprites[name]
                self.assertEqual(sprite.get_at((0, 0)).a, 0)
                self.assertGreater(pygame.mask.from_surface(sprite).count(), 0)

    @patch.object(Game, "apply_display_mode", dummy_display)
    def test_complete_run_preserves_height_across_shops_and_loops(self):
        game = Game()
        game.start_new_run()
        background = game.tower_background
        visited = []
        for _ in range(len(config.RUN_PATTERN) * game.max_cycles):
            screen = game.screen_manager.current_screen
            if isinstance(screen, GameOverScreen):
                break
            if game.current_step in ("normal", "boss"):
                visited.append(game.get_tower_floor_index())
                self.assertEqual(background.target_floor, len(visited) - 1)
                background.update(config.TOWER_ASCENT_SECONDS)
            else:
                self.assertEqual(game.get_tower_floor_index(), len(visited) - 1)
                self.assertEqual(background.target_floor, len(visited) - 1)
            self.assertIs(game.tower_background, background)
            game.update_render_metrics(screen)
            screen.draw(screen.virtual_surface)
            game.finish_current_screen()
        self.assertEqual(visited, list(range(18)))
        self.assertIsInstance(game.screen_manager.current_screen, GameOverScreen)
        game.start_new_run()
        self.assertIsNot(game.tower_background, background)
        self.assertEqual(game.tower_background.floor, 0)
        game.start_boss_test()
        self.assertEqual(game.get_tower_floor_index(), 0)
        self.assertEqual(game.tower_background.floor, 0)

    @patch.object(Game, "apply_display_mode", dummy_display)
    def test_height_changes_only_background_not_opaque_room(self):
        game = Game()
        game.start_new_run()
        screen = game.screen_manager.current_screen
        rect = screen.room.floors[0]["rect"].inflate(-10, -10)
        screen.draw(screen.virtual_surface)
        original = pygame.image.tobytes(screen.virtual_surface.subsurface(rect), "RGB")
        game.tower_background.set_floor(17, immediate=True)
        screen.draw(screen.virtual_surface)
        self.assertEqual(original, pygame.image.tobytes(screen.virtual_surface.subsurface(rect), "RGB"))


if __name__ == "__main__":
    unittest.main()
