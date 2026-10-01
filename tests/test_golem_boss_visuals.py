import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame

from game.entities.bosses.leaping_boss import LeapingBoss


class GolemBossVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.display.quit()

    def boss(self):
        boss = LeapingBoss()
        boss.x = boss.y = 200
        boss.detection_distance = math.inf
        return boss

    def test_pursuit_animates_in_every_direction(self):
        for facing, delta, row in (("down", (0, 150), 0),
                                   ("right", (150, 0), 1),
                                   ("left", (-150, 0), 2),
                                   ("up", (0, -150), 3)):
            with self.subTest(facing=facing):
                boss = self.boss()
                player = SimpleNamespace(x=200 + delta[0], y=200 + delta[1],
                                         invulnerability_timer=0)
                frames = set()
                for _ in range(60):
                    boss.update(player, 1 / 60, [], [])
                    frames.add(boss.visual.animator.get_frame_coords())
                self.assertEqual(boss.visual.animator.state, "walk")
                self.assertEqual(boss.visual.animator.facing, facing)
                self.assertGreater(len({col for col, r in frames if r == row}), 1)
                self.assertEqual(boss.visual.get_surface().get_at((0, 0)).a, 0)

    def test_attack_cycle_preserves_sprite_and_collision_size(self):
        boss = self.boss()
        player = SimpleNamespace(x=500, y=200, invulnerability_timer=0)
        surface = pygame.Surface((640, 480), pygame.SRCALPHA)
        states = set()
        shot_count = 0
        baseline = boss.hitbox.size
        for _ in range(720):
            shot_count += len(boss.update(player, 1 / 60, [], []))
            states.add(boss.state)
            if boss.state != "pursue":
                self.assertEqual(boss.visual.animator.state, "idle")
            before = boss.get_hitbox_bounds()
            boss.draw_ground_shadow(surface)
            boss.draw(surface)
            self.assertEqual(boss.visual.get_surface().get_size(), (96, 96))
            self.assertEqual(boss.get_hitbox_bounds(), before)
            self.assertEqual(boss.hitbox.size, baseline)
        self.assertTrue({"pursue", "jump_warning", "jump", "recover",
                         "spit_warning"}.issubset(states))
        self.assertGreaterEqual(shot_count, 7)

    def test_jump_faces_locked_target_and_stops_walking(self):
        boss = self.boss()
        boss.visual.set_state("walk")
        boss.visual.update(.31)
        boss.lock_jump_target(SimpleNamespace(x=200, y=50), [])
        boss.enter("jump_warning")
        self.assertEqual(boss.visual.animator.get_frame_coords(), (0, 3))
        boss.update_animation(.6)
        self.assertEqual(boss.visual.animator.get_frame_coords(), (0, 3))


if __name__ == "__main__":
    unittest.main()
