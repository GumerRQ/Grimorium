import math
import os
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import pygame
from game.entities.enemies.chaser_enemy import ChaserEnemy
from game.entities.enemies.shooter_enemy import ShooterEnemy
from game.entities.enemies.golem_enemy import GolemEnemy
from game.systems.enemy_navigation import clear_segment

class Room:
    def __init__(self, rows):
        self.layout = rows
        self.blockers = [pygame.Rect(c*32, r*32, 32, 32) for r, row in enumerate(rows) for c, tile in enumerate(row) if tile == '#']
    def world_to_cell(self, x, y):
        return int(y//32), int(x//32)
    def cell_to_world(self, r, c):
        return c*32+16, r*32+16

class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init()
        pygame.display.set_mode((1, 1))
    @classmethod
    def tearDownClass(cls):
        pygame.display.quit()
    def enemy(self, kind, pos):
        enemy = kind(pos)
        enemy.detection_distance = math.inf
        if enemy.visual is None:
            enemy.visual = Mock()
        return enemy
    def target(self, x, y):
        return SimpleNamespace(x=x, y=y, invulnerability_timer=0)
    def test_all_enemy_types_round_wall(self):
        room = Room(['#########', '#...#...#', '#...#...#', '#...#...#', '#.......#', '#########'])
        target = self.target(240, 48)
        for kind in (ChaserEnemy, GolemEnemy, ShooterEnemy):
            with self.subTest(kind=kind.__name__):
                enemy = self.enemy(kind, (48, 48))
                for _ in range(1800):
                    enemy.move(target, 1/60, room.blockers, [], room)
                    self.assertFalse(enemy.collides_with_rects(room.blockers))
                self.assertGreater(enemy.x, 160)
                self.assertTrue(clear_segment((enemy.x, enemy.y), (target.x, target.y), enemy.radius, room.blockers))
    def test_golem_navigates_several_tight_corners(self):
        room = Room(['#########', '#...#...#', '###.#.#.#', '#...#.#.#', '#.###.#.#', '#.....#.#', '#########'])
        enemy = self.enemy(GolemEnemy, (48, 48))
        target = self.target(240, 176)
        for _ in range(3600):
            enemy.move(target, 1/60, room.blockers, [], room)
            self.assertFalse(enemy.collides_with_rects(room.blockers))
        self.assertLess(math.dist((enemy.x, enemy.y), (target.x, target.y)), 1)

    def test_wandering_turns_before_wall(self):
        enemy = self.enemy(ChaserEnemy, (48, 48))
        enemy.random_dir_x, enemy.random_dir_y = 1, 0
        enemy.random_move_timer = 5
        target = self.target(1000, 48)
        target.invulnerability_timer = 1
        wall = pygame.Rect(62, 0, 32, 200)
        enemy.move(target, 1/60, [wall], [])
        self.assertNotEqual(enemy.y, 48)
        self.assertFalse(enemy.collides_with_rects([wall]))

    def test_unreachable_target_and_retry_limit(self):
        room = Room(['#######', '#..#..#', '#..#..#', '#######'])
        enemy = self.enemy(ChaserEnemy, (48, 48))
        with patch.object(enemy.navigator, '_plan', wraps=enemy.navigator._plan) as plan:
            for _ in range(60):
                enemy.move(self.target(176, 48), 1/60, room.blockers, [], room)
        self.assertGreater(enemy.x, 48)
        self.assertFalse(enemy.collides_with_rects(room.blockers))
        self.assertLessEqual(plan.call_count, 4)
    def test_golem_approaches_player_tight_against_wall(self):
        room = Room(['#########', '#.......#', '#.......#', '#########'])
        enemy = self.enemy(GolemEnemy, (240, 48))
        target = self.target(42, 48)  # Player fits; the golem's center cannot.
        for _ in range(900):
            enemy.move(target, 1/60, room.blockers, [], room)
        self.assertLess(enemy.x, 65)
        self.assertFalse(enemy.collides_with_rects(room.blockers))

    def test_hitboxes_match_visible_sprite_and_do_not_change_with_pose(self):
        from game.entities.enemies.rat_enemy import RatEnemy
        from game.entities.enemies.goblin_enemy import GoblinEnemy
        from game.entities.enemies.dragon_enemy import DragonEnemy
        for kind, size in ((GolemEnemy, (56, 43)), (RatEnemy, (32, 29)),
                           (GoblinEnemy, (31, 30)), (DragonEnemy, (30, 30))):
            enemy = self.enemy(kind, (100, 100))
            self.assertEqual(enemy.hitbox.size, size)
            original = enemy.get_hitbox_bounds()
            for facing in ('left', 'right', 'up', 'down'):
                enemy.visual.set_facing(facing)
                enemy.visual.update(0.3)
                self.assertEqual(enemy.get_hitbox_bounds(), original)

    def test_bullets_hit_rectangular_body_outside_old_circle(self):
        from game.systems.collisions import circles_collide
        enemy = self.enemy(GolemEnemy, (100, 100))
        self.assertTrue(circles_collide(self.target_circle(126, 80), enemy))
        self.assertFalse(circles_collide(self.target_circle(134, 80), enemy))

    def target_circle(self, x, y):
        return SimpleNamespace(x=x, y=y, radius=1)

    def test_alternating_small_movements_do_not_flip_facing(self):
        enemy = self.enemy(GolemEnemy, (100, 100))
        enemy.visual.set_facing('right')
        for _ in range(60):
            enemy.update_visual_from_movement(-0.1, 0)
            enemy.update_visual_from_movement(0.1, 0)
        self.assertEqual(enemy.visual.animator.facing, 'right')
        for _ in range(10):
            enemy.update_visual_from_movement(-0.1, 0)
        self.assertEqual(enemy.visual.animator.facing, 'left')

    def test_two_overlapping_golems_escape_without_flipping(self):
        from game.systems.collision_shapes import overlap_area
        enemies = [self.enemy(GolemEnemy, (100, 100)), self.enemy(GolemEnemy, (100, 100))]
        turns = [[], []]
        for _ in range(600):
            for i, enemy in enumerate(enemies):
                enemy.move(self.target(1000, 100), 1/60, [], enemies)
                turns[i].append(enemy.visual.animator.facing)
        for enemy, facing in zip(enemies, turns):
            self.assertGreater(enemy.x, 200)
            self.assertLessEqual(sum(a != b for a, b in zip(facing, facing[1:])), 1)
        self.assertLess(overlap_area(enemies[0].get_movement_bounds(), enemies[1].get_movement_bounds()), 1e-6)

    def test_body_width_and_short_segment(self):
        blockers = [pygame.Rect(0, 0, 100, 32), pygame.Rect(0, 64, 100, 32)]
        self.assertTrue(clear_segment((16, 48), (80, 48), 13, blockers))
        self.assertFalse(clear_segment((16, 48), (80, 48), 17, blockers))
        self.assertFalse(clear_segment((10, 48), (10, 47), 16, blockers))
    def test_opened_door(self):
        room = Room(['#######', '#..#..#', '#..#..#', '#######'])
        enemy = self.enemy(ChaserEnemy, (48, 48))
        target = self.target(176, 48)
        enemy.move(target, 1/60, room.blockers, [], room)
        blockers = [r for r in room.blockers if r.topleft != (96, 32)]
        enemy.move(target, 1/60, blockers, [], room)
        self.assertGreater(enemy.x, 48)
    def test_shooter_update_passes_room(self):
        enemy = self.enemy(ShooterEnemy, (48, 48))
        room = Room(['#########', '#...#...#', '#.......#', '#########'])
        with patch.object(enemy.navigator, 'movement', wraps=enemy.navigator.movement) as movement:
            enemy.update(self.target(240, 48), 1/60, room.blockers, [], room)
        self.assertIs(movement.call_args.args[3], room)
    def test_flying_uses_supplied_blockers(self):
        room = Room(['#######', '#..#..#', '#..#..#', '#######'])
        enemy = self.enemy(ShooterEnemy, (48, 48))
        blockers = [r for r in room.blockers if r.x != 96 or r.y in (0, 96)]
        enemy.move(self.target(176, 48), 1/60, blockers, [], room)
        self.assertGreater(enemy.x, 48)
    def test_large_dt_no_tunnelling(self):
        enemy = self.enemy(ChaserEnemy, (48, 48))
        wall = pygame.Rect(80, 0, 3, 200)
        enemy.move_safely(200, 0, [wall], [])
        self.assertLessEqual(enemy.x + enemy.radius, wall.left)
    def test_retreat_at_wall(self):
        enemy = self.enemy(ShooterEnemy, (48, 48))
        wall = pygame.Rect(0, 0, 36, 160)
        enemy.move(self.target(70, 48), 1/60, [wall], [])
        self.assertFalse(enemy.collides_with_rects([wall]))
        self.assertNotEqual(enemy.y, 48)
    def test_golem_speed_and_pose_across_fps(self):
        results = []
        for fps in (15, 60, 144):
            enemy = self.enemy(GolemEnemy, (0, 0))
            duration = 4 * enemy.speed_animation
            remaining = duration
            while remaining > 1e-9:
                dt = min(1/fps, remaining)
                enemy.update(self.target(10000, 0), dt, [], [])
                remaining -= dt
            self.assertAlmostEqual(enemy.x, enemy.base_speed * duration)
            results.append(enemy.visual.fixed_frame)
        self.assertEqual(results, [results[0]] * 3)
    def test_golem_slow_frame_plans_once(self):
        enemy = self.enemy(GolemEnemy, (48, 48))
        room = Room(['#########', '#...#...#', '#.......#', '#########'])
        with patch.object(enemy.navigator, '_plan', wraps=enemy.navigator._plan) as plan:
            enemy.move(self.target(240, 48), 1, room.blockers, [], room)
        self.assertEqual(plan.call_count, 1)

if __name__ == '__main__':
    unittest.main()
