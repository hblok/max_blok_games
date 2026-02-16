# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Obstacle management - ramps and rocks
"""
import pygame
import random
from maxbloks.dogrider.constants import *

class Obstacle:
    def __init__(self, x, obstacle_type):
        self.x = x
        self.type = obstacle_type
        if obstacle_type == 'ramp':
            self.width = random.randint(80, 120)
            self.height = random.randint(30, 90)  # Taller ramps
            self.y = GROUND_Y - self.height
        else:
            self.width = 30
            self.height = 50
            self.y = 300
        
    def update(self, game_speed):
        self.x -= game_speed
        
    def draw(self, screen):
        if self.type == 'ramp':
            # Draw ramp triangle
            points = [(self.x, self.y + self.height),
                     (self.x + self.width, self.y + self.height),
                     (self.x + self.width, self.y)]
            pygame.draw.polygon(screen, BROWN, points)
            
            # Ramp stripes
            stripe_count = max(2, self.width // 30)
            for i in range(stripe_count):
                stripe_x = self.x + (i + 1) * (self.width / (stripe_count + 1))
                start_x = stripe_x - 5
                start_y = self.y + self.height
                end_x = stripe_x + 5
                end_y = self.y + 10
                pygame.draw.line(screen, GOLD, (start_x, start_y), (end_x, end_y), 3)
        else:
            # Draw rock obstacle
            pygame.draw.circle(screen, GRAY, (self.x + 15, self.y + 35), 15)
            pygame.draw.circle(screen, GRAY, (self.x + 5, self.y + 45), 12)
            pygame.draw.circle(screen, GRAY, (self.x + 23, self.y + 42), 10)
            
    def collides_with(self, dog):
        return (dog.x < self.x + self.width and
                dog.x + dog.width > self.x and
                dog.y < self.y + self.height and
                dog.y + dog.height > self.y)

class ObstacleManager:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.obstacles = []
        self.obstacle_timer = 0
        self.next_obstacle_delay = random.randint(180, 360)
        self.obstacles_spawned = 0
        self.obstacles_cleared = 0
        
    def reset(self):
        self.obstacles = []
        self.obstacle_timer = 0
        self.next_obstacle_delay = random.randint(180, 360)
        self.obstacles_spawned = 0
        self.obstacles_cleared = 0
        
    def update(self, game_speed):
        # Spawn obstacles
        self.obstacle_timer += 1
        if self.obstacle_timer >= self.next_obstacle_delay and self.obstacles_spawned < MAX_OBSTACLES:
            obstacle_type = 'ramp' if random.random() < 0.3 else 'rock'
            self.obstacles.append(Obstacle(self.screen_width, obstacle_type))
            self.obstacles_spawned += 1
            self.obstacle_timer = 0
            
            # Set next random delay
            min_delay = max(120, 300 - int(game_speed * 20))
            max_delay = max(180, 480 - int(game_speed * 30))
            self.next_obstacle_delay = random.randint(min_delay, max_delay)
            
        # Update obstacles
        for i in range(len(self.obstacles) - 1, -1, -1):
            self.obstacles[i].update(game_speed)
            
            if self.obstacles[i].x < -self.obstacles[i].width:
                self.obstacles.pop(i)
                self.obstacles_cleared += 1
                
    def draw(self, screen):
        for obstacle in self.obstacles:
            obstacle.draw(screen)
            
    def check_collisions(self, dog):
        for obstacle in self.obstacles:
            if obstacle.type == 'rock' and obstacle.collides_with(dog):
                return True
            elif obstacle.type == 'ramp':
                dog.handle_ramp_collision(obstacle)
        return False
        
    def is_complete(self):
        return self.obstacles_spawned >= MAX_OBSTACLES and len(self.obstacles) == 0
