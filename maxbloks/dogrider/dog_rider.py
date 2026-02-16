# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""
DogRider class - handles the player character (dog on motorcycle)
"""
import pygame
import math
import random
from maxbloks.dogrider.constants import *

class DogRider:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.x = 150
        self.y = 300
        self.width = 80
        self.height = 60
        self.velocity_y = 0
        self.velocity_x = 0
        self.on_ground = False
        self.on_ramp = False
        self.rotation = 0
        self.target_rotation = 0
        self.anim_frame = 0
        self.wheel_rotation = 0
        self.ramp_angle = 0
        self.exhaust_particles = []
        
    def reset(self):
        """Reset dog to initial state"""
        self.x = 150
        self.y = 300
        self.velocity_y = 0
        self.velocity_x = 0
        self.on_ground = False
        self.on_ramp = False
        self.rotation = 0
        self.target_rotation = 0
        self.anim_frame = 0
        self.wheel_rotation = 0
        self.ramp_angle = 0
        self.exhaust_particles = []
        
    def update(self, joystick_x, joystick_y, jump_pressed, game_speed):
        # Handle joystick input
        if abs(joystick_x) > JOYSTICK_DEADZONE:
            if joystick_x < 0:  # Left
                self.target_rotation = -0.3
                self.velocity_x = max(self.velocity_x - 0.5, -3)
            else:  # Right
                self.target_rotation = 0.3
                self.velocity_x = min(self.velocity_x + 0.5, 3)
        else:
            self.target_rotation = 0
            self.velocity_x *= 0.95
            
        # Jump with forward momentum
        if jump_pressed and (self.on_ground or self.on_ramp):
            self.velocity_y = JUMP_POWER
            self.velocity_x += FORWARD_JUMP_BOOST
            self.on_ground = False
            self.on_ramp = False
            
        # Smooth rotation
        self.rotation += (self.target_rotation - self.rotation) * 0.1
        
        # Physics
        if not self.on_ramp:
            self.velocity_y += GRAVITY
        
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Ground collision
        if self.y + self.height > GROUND_Y and not self.on_ramp:
            self.y = GROUND_Y - self.height
            self.velocity_y = 0
            self.on_ground = True
            
        # Keep on screen
        if self.x < 0:
            self.x = 0
        if self.x > self.screen_width - self.width:
            self.x = self.screen_width - self.width
            
        # Animation
        self.anim_frame += 0.2
        self.wheel_rotation += game_speed * 0.3
        
        # Update exhaust particles
        if self.on_ground and game_speed > 1:
            if random.random() < 0.3:
                self.exhaust_particles.append({
                    'x': self.x - 30,
                    'y': self.y + 20,
                    'life': 20,
                    'dx': random.uniform(-1, -2),
                    'dy': random.uniform(-0.5, 0.5)
                })
        
        # Update particles
        for i in range(len(self.exhaust_particles) - 1, -1, -1):
            particle = self.exhaust_particles[i]
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.exhaust_particles.pop(i)
        
        # Reset ramp state
        self.on_ramp = False
        
    def handle_ramp_collision(self, ramp):
        """Handle collision with ramp - follow ramp surface"""
        rel_x = self.x + self.width/2 - ramp.x
        if 0 <= rel_x <= ramp.width:
            ramp_progress = rel_x / ramp.width
            ramp_y = ramp.y + ramp.height - (ramp_progress * ramp.height)
            
            if self.y + self.height >= ramp_y - 10:
                self.y = ramp_y - self.height
                self.velocity_y = 0
                self.on_ramp = True
                self.on_ground = False
                
                self.ramp_angle = -math.atan(ramp.height / ramp.width)
                self.rotation = self.ramp_angle * 0.5
                
                if ramp_progress < 0.8:
                    self.velocity_x += 0.2
                else:
                    launch_power = ramp.height / 20
                    self.velocity_y = -12 - launch_power
                    self.velocity_x += 3 + launch_power
                    self.on_ramp = False
                    
    def draw(self, screen):
        # Draw exhaust particles first
        for particle in self.exhaust_particles:
            alpha = int(255 * (particle['life'] / 20))
            size = max(1, particle['life'] // 4)
            color = (min(255, 100 + alpha), min(255, 100 + alpha//2), min(255, 100 + alpha//4))
            pygame.draw.circle(screen, color, (int(particle['x']), int(particle['y'])), size)
        
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        
        surf = pygame.Surface((self.width * 2, self.height * 2), pygame.SRCALPHA)
        surf_center_x = self.width
        surf_center_y = self.height
        
        self.draw_motorcycle(surf, surf_center_x, surf_center_y)
        self.draw_dog(surf, surf_center_x, surf_center_y)
        
        if abs(self.rotation) > 0.01:
            rotated_surf = pygame.transform.rotate(surf, math.degrees(-self.rotation))
            rotated_rect = rotated_surf.get_rect(center=(center_x, center_y))
            screen.blit(rotated_surf, rotated_rect)
        else:
            surf_rect = surf.get_rect(center=(center_x, center_y))
            screen.blit(surf, surf_rect)
    
    def draw_motorcycle(self, surf, center_x, center_y):
        # Main frame
        pygame.draw.line(surf, CHROME, (center_x - 30, center_y), (center_x + 25, center_y - 5), 4)
        pygame.draw.line(surf, CHROME, (center_x - 15, center_y), (center_x + 10, center_y - 20), 3)
        
        # Engine block
        pygame.draw.rect(surf, DARK_GRAY, (center_x - 20, center_y - 5, 25, 15))
        pygame.draw.rect(surf, SILVER, (center_x - 18, center_y - 3, 21, 11))
        
        # Fuel tank
        pygame.draw.ellipse(surf, RED_ORANGE, (center_x - 10, center_y - 25, 35, 20))
        pygame.draw.ellipse(surf, ORANGE, (center_x - 8, center_y - 23, 31, 16))
        
        # Seat
        pygame.draw.ellipse(surf, BLACK, (center_x - 25, center_y - 20, 30, 12))
        pygame.draw.ellipse(surf, DARK_GRAY, (center_x - 23, center_y - 18, 26, 8))
        
        # Exhaust pipe
        pygame.draw.line(surf, CHROME, (center_x - 25, center_y + 5), (center_x - 35, center_y + 10), 3)
        pygame.draw.circle(surf, DARK_GRAY, (center_x - 35, center_y + 10), 4)
        
        # Front fork
        pygame.draw.line(surf, CHROME, (center_x + 20, center_y - 5), (center_x + 25, center_y + 15), 3)
        
        # Handlebars
        pygame.draw.line(surf, CHROME, (center_x + 15, center_y - 20), (center_x + 20, center_y - 30), 3)
        pygame.draw.line(surf, BLACK, (center_x + 10, center_y - 30), (center_x + 30, center_y - 30), 4)
        pygame.draw.circle(surf, BLACK, (center_x + 10, center_y - 30), 3)
        pygame.draw.circle(surf, BLACK, (center_x + 30, center_y - 30), 3)
        
        # Headlight
        pygame.draw.circle(surf, YELLOW, (center_x + 25, center_y - 15), 6)
        pygame.draw.circle(surf, WHITE, (center_x + 25, center_y - 15), 4)
        
        # Wheels
        self.draw_detailed_wheel(surf, center_x + 25, center_y + 15)
        self.draw_detailed_wheel(surf, center_x - 25, center_y + 15)
        
    def draw_detailed_wheel(self, surf, x, y):
        # Tire tread
        pygame.draw.circle(surf, BLACK, (int(x), int(y)), 14)
        for i in range(8):
            angle = (i * math.pi / 4) + self.wheel_rotation
            tread_x = x + math.cos(angle) * 12
            tread_y = y + math.sin(angle) * 12
            pygame.draw.circle(surf, DARK_GRAY, (int(tread_x), int(tread_y)), 2)
        
        # Rim
        pygame.draw.circle(surf, SILVER, (int(x), int(y)), 10)
        pygame.draw.circle(surf, CHROME, (int(x), int(y)), 8)
        
        # Spokes
        for i in range(6):
            angle = (i * math.pi / 3) + self.wheel_rotation
            end_x = x + math.cos(angle) * 7
            end_y = y + math.sin(angle) * 7
            pygame.draw.line(surf, SILVER, (x, y), (end_x, end_y), 2)
        
        # Hub
        pygame.draw.circle(surf, CHROME, (int(x), int(y)), 3)
            
    def draw_dog(self, surf, center_x, center_y):
        # Dog body
        body_rect = pygame.Rect(center_x - 15, center_y - 35, 25, 20)
        pygame.draw.ellipse(surf, BROWN, body_rect)
        pygame.draw.ellipse(surf, LIGHT_BROWN, (center_x - 13, center_y - 33, 21, 16))
        
        # Dog head
        pygame.draw.circle(surf, LIGHT_BROWN, (center_x + 5, center_y - 45), 12)
        pygame.draw.ellipse(surf, LIGHT_BROWN, (center_x + 10, center_y - 48, 8, 6))
        
        # Ears (animated)
        ear_flap = math.sin(self.anim_frame) * 0.1
        # Left ear
        ear_points = [(center_x + 15, center_y - 50), 
                     (center_x + 25, center_y - 52 + ear_flap * 10),
                     (center_x + 20, center_y - 35)]
        pygame.draw.polygon(surf, BROWN, ear_points)
        pygame.draw.polygon(surf, PINK, [(center_x + 17, center_y - 48), 
                                        (center_x + 22, center_y - 50 + ear_flap * 5),
                                        (center_x + 19, center_y - 40)])
        
        # Right ear
        ear_points = [(center_x - 5, center_y - 50), 
                     (center_x - 15, center_y - 52 - ear_flap * 10),
                     (center_x - 10, center_y - 35)]
        pygame.draw.polygon(surf, BROWN, ear_points)
        pygame.draw.polygon(surf, PINK, [(center_x - 7, center_y - 48), 
                                        (center_x - 12, center_y - 50 - ear_flap * 5),
                                        (center_x - 9, center_y - 40)])
        
        # Eyes
        pygame.draw.circle(surf, WHITE, (center_x + 10, center_y - 48), 3)
        pygame.draw.circle(surf, BLACK, (center_x + 11, center_y - 48), 2)
        pygame.draw.circle(surf, WHITE, (center_x + 12, center_y - 49), 1)
        
        pygame.draw.circle(surf, WHITE, (center_x + 2, center_y - 48), 3)
        pygame.draw.circle(surf, BLACK, (center_x + 3, center_y - 48), 2)
        pygame.draw.circle(surf, WHITE, (center_x + 4, center_y - 49), 1)
        
        # Nose
        pygame.draw.ellipse(surf, BLACK, (center_x + 14, center_y - 44, 4, 3))
        pygame.draw.circle(surf, PINK, (center_x + 15, center_y - 43), 1)
        
        # Mouth
        pygame.draw.arc(surf, BLACK, (center_x + 8, center_y - 42, 8, 4), 0, math.pi, 2)
        
        # Tongue (when jumping)
        if not self.on_ground and not self.on_ramp:
            tongue_length = 4 + math.sin(self.anim_frame * 2) * 2
            pygame.draw.ellipse(surf, PINK, (center_x + 16, center_y - 40, 3, tongue_length))
            
        # Arms
        pygame.draw.line(surf, BROWN, (center_x + 8, center_y - 30), 
                        (center_x + 18, center_y - 25), 4)
        pygame.draw.circle(surf, BROWN, (center_x + 18, center_y - 25), 3)
        
        pygame.draw.line(surf, BROWN, (center_x + 2, center_y - 30), 
                        (center_x + 12, center_y - 25), 4)
        pygame.draw.circle(surf, BROWN, (center_x + 12, center_y - 25), 3)
        
        # Legs
        pygame.draw.line(surf, BROWN, (center_x - 8, center_y - 20), 
                        (center_x - 5, center_y - 5), 3)
        pygame.draw.line(surf, BROWN, (center_x + 5, center_y - 20), 
                        (center_x + 8, center_y - 5), 3)
        
        # Tail (animated)
        excitement = 1.0 if not (self.on_ground or self.on_ramp) else 0.5
        tail_wag = math.sin(self.anim_frame * 3 * excitement) * 15 * excitement
        tail_end_x = center_x - 20 + tail_wag
        tail_end_y = center_y - 35 + abs(tail_wag) * 0.3
        
        mid_x = center_x - 12 + tail_wag * 0.5
        mid_y = center_y - 30
        
        pygame.draw.line(surf, BROWN, (center_x - 8, center_y - 25), 
                        (mid_x, mid_y), 4)
        pygame.draw.line(surf, BROWN, (mid_x, mid_y), 
                        (tail_end_x, tail_end_y), 4)
        
        # Collar
        pygame.draw.ellipse(surf, RED, (center_x - 8, center_y - 38, 20, 6))
        pygame.draw.circle(surf, GOLD, (center_x + 8, center_y - 35), 2)

        
