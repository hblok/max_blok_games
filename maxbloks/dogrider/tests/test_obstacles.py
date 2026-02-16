# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import MagicMock, patch
import pygame

from maxbloks.dogrider.obstacles import Obstacle, ObstacleManager
from maxbloks.dogrider.constants import GROUND_Y, MAX_OBSTACLES


class TestObstacle(unittest.TestCase):

    def setUp(self):
        pygame.init()
        pygame.display.init()

    def tearDown(self):
        pygame.quit()

    def test_ramp_initialization(self):
        with patch('random.randint', side_effect=[100, 60]):
            obstacle = Obstacle(500, 'ramp')
        
        self.assertEqual(obstacle.x, 500)
        self.assertEqual(obstacle.type, 'ramp')
        self.assertEqual(obstacle.width, 100)
        self.assertEqual(obstacle.height, 60)
        self.assertEqual(obstacle.y, GROUND_Y - 60)

    def test_rock_initialization(self):
        obstacle = Obstacle(500, 'rock')
        
        self.assertEqual(obstacle.x, 500)
        self.assertEqual(obstacle.type, 'rock')
        self.assertEqual(obstacle.width, 30)
        self.assertEqual(obstacle.height, 50)
        self.assertEqual(obstacle.y, 300)

    def test_update(self):
        obstacle = Obstacle(500, 'rock')
        obstacle.update(2.0)
        
        self.assertEqual(obstacle.x, 498)

    def test_update_negative_speed(self):
        obstacle = Obstacle(500, 'rock')
        obstacle.update(-1.0)
        
        self.assertEqual(obstacle.x, 501)

    def test_collides_with_true(self):
        obstacle = Obstacle(200, 'rock')
        dog = MagicMock()
        dog.x = 200
        dog.width = 80
        dog.y = 300
        dog.height = 60
        
        self.assertTrue(obstacle.collides_with(dog))

    def test_collides_with_false_x(self):
        obstacle = Obstacle(200, 'rock')
        dog = MagicMock()
        dog.x = 100
        dog.width = 80
        dog.y = 300
        dog.height = 60
        
        self.assertFalse(obstacle.collides_with(dog))

    def test_collides_with_false_y(self):
        obstacle = Obstacle(200, 'rock')
        dog = MagicMock()
        dog.x = 200
        dog.width = 80
        dog.y = 100
        dog.height = 60
        
        self.assertFalse(obstacle.collides_with(dog))


class TestObstacleManager(unittest.TestCase):

    def setUp(self):
        pygame.init()
        pygame.display.init()
        self.screen_width = 800
        self.screen_height = 600
        self.manager = ObstacleManager(self.screen_width, self.screen_height)

    def tearDown(self):
        pygame.quit()

    def test_initialization(self):
        self.assertEqual(self.manager.screen_width, 800)
        self.assertEqual(self.manager.screen_height, 600)
        self.assertEqual(self.manager.obstacles, [])
        self.assertEqual(self.manager.obstacle_timer, 0)
        self.assertEqual(self.manager.obstacles_spawned, 0)
        self.assertEqual(self.manager.obstacles_cleared, 0)

    def test_reset(self):
        self.manager.obstacles.append(Obstacle(500, 'rock'))
        self.manager.obstacle_timer = 100
        self.manager.obstacles_spawned = 10
        self.manager.obstacles_cleared = 5
        
        self.manager.reset()
        
        self.assertEqual(self.manager.obstacles, [])
        self.assertEqual(self.manager.obstacle_timer, 0)
        self.assertEqual(self.manager.obstacles_spawned, 0)
        self.assertEqual(self.manager.obstacles_cleared, 0)

    @patch('random.random')
    @patch('random.randint')
    def test_spawn_rock(self, mock_randint, mock_random):
        mock_randint.return_value = 200
        mock_random.return_value = 0.5
        self.manager.obstacle_timer = 200
        self.manager.next_obstacle_delay = 180
        
        self.manager.update(2.0)
        
        self.assertEqual(len(self.manager.obstacles), 1)
        self.assertEqual(self.manager.obstacles[0].type, 'rock')
        self.assertEqual(self.manager.obstacles[0].x, 800 - 2.0)

    @patch('random.random')
    @patch('random.randint')
    def test_spawn_ramp(self, mock_randint, mock_random):
        mock_randint.return_value = 200
        mock_random.return_value = 0.2
        self.manager.obstacle_timer = 200
        self.manager.next_obstacle_delay = 180
        
        self.manager.update(2.0)
        
        self.assertEqual(len(self.manager.obstacles), 1)
        self.assertEqual(self.manager.obstacles[0].type, 'ramp')

    def test_no_spawn_before_delay(self):
        self.manager.obstacle_timer = 100
        self.manager.next_obstacle_delay = 180
        
        self.manager.update(2.0)
        
        self.assertEqual(len(self.manager.obstacles), 0)

    def test_max_obstacles_reached(self):
        self.manager.obstacles_spawned = MAX_OBSTACLES
        self.manager.obstacle_timer = 200
        self.manager.next_obstacle_delay = 180
        
        self.manager.update(2.0)
        
        self.assertEqual(len(self.manager.obstacles), 0)

    def test_update_obstacle_position(self):
        obstacle = Obstacle(800, 'rock')
        self.manager.obstacles.append(obstacle)
        initial_x = obstacle.x
        
        self.manager.update(2.0)
        
        self.assertEqual(obstacle.x, initial_x - 2.0)

    def test_remove_offscreen_obstacle(self):
        obstacle = Obstacle(-50, 'rock')
        obstacle.width = 30
        self.manager.obstacles.append(obstacle)
        
        self.manager.update(2.0)
        
        self.assertEqual(len(self.manager.obstacles), 0)
        self.assertEqual(self.manager.obstacles_cleared, 1)

    def test_check_collisions_rock(self):
        obstacle = Obstacle(200, 'rock')
        self.manager.obstacles.append(obstacle)
        dog = MagicMock()
        dog.x = 200
        dog.width = 80
        dog.y = 300
        dog.height = 60
        
        result = self.manager.check_collisions(dog)
        
        self.assertTrue(result)

    def test_check_collisions_no_rock(self):
        obstacle = Obstacle(800, 'rock')
        self.manager.obstacles.append(obstacle)
        dog = MagicMock()
        dog.x = 200
        dog.width = 80
        dog.y = 300
        dog.height = 60
        
        result = self.manager.check_collisions(dog)
        
        self.assertFalse(result)

    def test_check_collisions_ramp_no_collision(self):
        obstacle = Obstacle(800, 'ramp')
        self.manager.obstacles.append(obstacle)
        dog = MagicMock()
        dog.x = 200
        dog.width = 80
        dog.y = 300
        dog.height = 60
        
        result = self.manager.check_collisions(dog)
        
        self.assertFalse(result)

    def test_check_collisions_ramp_calls_handle(self):
        obstacle = Obstacle(200, 'ramp')
        self.manager.obstacles.append(obstacle)
        dog = MagicMock()
        dog.x = 200
        dog.width = 80
        dog.y = 300
        dog.height = 60
        
        self.manager.check_collisions(dog)
        
        dog.handle_ramp_collision.assert_called_once_with(obstacle)

    def test_is_complete_false(self):
        self.assertFalse(self.manager.is_complete())

    def test_is_complete_true(self):
        self.manager.obstacles_spawned = MAX_OBSTACLES
        
        self.assertTrue(self.manager.is_complete())

    def test_is_complete_obstacles_remaining(self):
        self.manager.obstacles_spawned = MAX_OBSTACLES
        self.manager.obstacles.append(Obstacle(500, 'rock'))
        
        self.assertFalse(self.manager.is_complete())