# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import MagicMock, patch
import pygame

from maxbloks.dogrider.dog_rider import DogRider
from maxbloks.dogrider.constants import JOYSTICK_DEADZONE, JUMP_POWER, FORWARD_JUMP_BOOST, GRAVITY, GROUND_Y


class TestDogRider(unittest.TestCase):

    def setUp(self):
        pygame.init()
        pygame.display.init()
        self.screen_width = 800
        self.screen_height = 600
        self.dog = DogRider(self.screen_width, self.screen_height)

    def tearDown(self):
        pygame.quit()

    def test_initialization(self):
        self.assertEqual(self.dog.screen_width, 800)
        self.assertEqual(self.dog.screen_height, 600)
        self.assertEqual(self.dog.x, 150)
        self.assertEqual(self.dog.y, 300)
        self.assertEqual(self.dog.width, 80)
        self.assertEqual(self.dog.height, 60)
        self.assertEqual(self.dog.velocity_x, 0)
        self.assertEqual(self.dog.velocity_y, 0)
        self.assertFalse(self.dog.on_ground)
        self.assertFalse(self.dog.on_ramp)
        self.assertEqual(self.dog.rotation, 0)
        self.assertEqual(self.dog.target_rotation, 0)
        self.assertEqual(self.dog.exhaust_particles, [])

    def test_reset(self):
        self.dog.x = 500
        self.dog.y = 100
        self.dog.velocity_x = 5
        self.dog.velocity_y = 10
        self.dog.on_ground = True
        self.dog.rotation = 0.5
        self.dog.exhaust_particles.append({'x': 1, 'y': 1, 'life': 10, 'dx': -1, 'dy': 0})
        
        self.dog.reset()
        
        self.assertEqual(self.dog.x, 150)
        self.assertEqual(self.dog.y, 300)
        self.assertEqual(self.dog.velocity_x, 0)
        self.assertEqual(self.dog.velocity_y, 0)
        self.assertFalse(self.dog.on_ground)
        self.assertFalse(self.dog.on_ramp)
        self.assertEqual(self.dog.rotation, 0)
        self.assertEqual(self.dog.target_rotation, 0)
        self.assertEqual(self.dog.exhaust_particles, [])

    def test_update_no_input(self):
        self.dog.y = 100
        self.dog.on_ground = False
        
        self.dog.update(0, 0, False, 2.0)
        
        self.assertEqual(self.dog.velocity_x, 0)
        self.assertEqual(self.dog.velocity_y, GRAVITY)
        self.assertEqual(self.dog.y, 100 + GRAVITY)

    def test_update_joystick_left(self):
        self.dog.on_ground = True
        
        self.dog.update(-1.0, 0, False, 2.0)
        
        self.assertLess(self.dog.velocity_x, 0)
        self.assertEqual(self.dog.target_rotation, -0.3)
        self.assertLess(self.dog.x, 150)

    def test_update_joystick_right(self):
        self.dog.on_ground = True
        
        self.dog.update(1.0, 0, False, 2.0)
        
        self.assertGreater(self.dog.velocity_x, 0)
        self.assertEqual(self.dog.target_rotation, 0.3)
        self.assertGreater(self.dog.x, 150)

    def test_update_deadzone(self):
        initial_velocity_x = self.dog.velocity_x
        
        self.dog.update(0.1, 0, False, 2.0)
        
        self.assertEqual(self.dog.velocity_x, 0)
        self.assertEqual(self.dog.target_rotation, 0)

    def test_jump(self):
        self.dog.on_ground = True
        initial_y = self.dog.y
        
        self.dog.update(0, 0, True, 2.0)
        
        self.assertEqual(self.dog.velocity_y, JUMP_POWER + GRAVITY)
        self.assertGreater(self.dog.velocity_x, 0)
        self.assertFalse(self.dog.on_ground)

    def test_jump_in_air(self):
        self.dog.on_ground = False
        initial_velocity_y = self.dog.velocity_y
        
        self.dog.update(0, 0, True, 2.0)
        
        self.assertEqual(self.dog.velocity_y, initial_velocity_y)

    def test_ground_collision(self):
        self.dog.y = GROUND_Y - 40
        self.dog.velocity_y = 10
        
        self.dog.update(0, 0, False, 2.0)
        
        self.assertEqual(self.dog.y, GROUND_Y - 60)
        self.assertEqual(self.dog.velocity_y, 0)
        self.assertTrue(self.dog.on_ground)

    def test_screen_boundaries_left(self):
        self.dog.x = -10
        self.dog.velocity_x = -5
        
        self.dog.update(-1.0, 0, False, 2.0)
        
        self.assertEqual(self.dog.x, 0)

    def test_screen_boundaries_right(self):
        self.dog.x = self.screen_width - 70
        self.dog.velocity_x = 5
        
        self.dog.update(1.0, 0, False, 2.0)
        
        self.assertEqual(self.dog.x, self.screen_width - 80)

    def test_velocity_x_decay(self):
        self.dog.velocity_x = 2.0
        self.dog.on_ground = True
        
        self.dog.update(0, 0, False, 2.0)
        
        self.assertLess(abs(self.dog.velocity_x), 2.0)

    def test_velocity_x_max_left(self):
        self.dog.on_ground = True
        self.dog.velocity_x = -2.5
        
        self.dog.update(-1.0, 0, False, 2.0)
        
        self.assertGreaterEqual(self.dog.velocity_x, -3.0)

    def test_velocity_x_max_right(self):
        self.dog.on_ground = True
        self.dog.velocity_x = 2.5
        
        self.dog.update(1.0, 0, False, 2.0)
        
        self.assertLessEqual(self.dog.velocity_x, 3.0)

    def test_rotation_smoothing(self):
        self.dog.update(1.0, 0, False, 2.0)
        
        self.assertGreater(self.dog.rotation, 0)
        self.assertLess(self.dog.rotation, 0.3)

    def test_animation_frame(self):
        initial_anim_frame = self.dog.anim_frame
        
        self.dog.update(0, 0, False, 2.0)
        
        self.assertGreater(self.dog.anim_frame, initial_anim_frame)

    def test_wheel_rotation(self):
        initial_wheel_rotation = self.dog.wheel_rotation
        
        self.dog.update(0, 0, False, 2.0)
        
        self.assertGreater(self.dog.wheel_rotation, initial_wheel_rotation)

    @patch('random.random')
    @patch('random.uniform')
    def test_exhaust_particles_spawn(self, mock_uniform, mock_random):
        mock_random.return_value = 0.2
        mock_uniform.return_value = -1.5
        
        self.dog.on_ground = True
        
        self.dog.update(0, 0, False, 2.0)
        
        self.assertEqual(len(self.dog.exhaust_particles), 1)

    @patch('random.random')
    def test_no_exhaust_when_slow(self, mock_random):
        mock_random.return_value = 0.2
        initial_particle_count = len(self.dog.exhaust_particles)
        
        self.dog.on_ground = True
        
        self.dog.update(0, 0, False, 0.5)
        
        self.assertEqual(len(self.dog.exhaust_particles), initial_particle_count)