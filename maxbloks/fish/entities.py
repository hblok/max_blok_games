import pygame
import math
import random

from maxbloks.fish.utils import FISH_COLORS


class Entity:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size
        
    def collides_with(self, other):
        """Check if this entity collides with another entity"""
        distance = math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
        return distance < (self.size + other.size) * 0.7  # 0.7 for more forgiving collisions

class Fish(Entity):
    def __init__(self, x, y, size, speed, color):
        super().__init__(x, y, size)
        self.speed = speed
        self.color = color
        self.wobble = 0
        self.wobble_speed = random.uniform(0.05, 0.1)
        self.wobble_amount = random.uniform(0.5, 1.5)
        
    def update(self):
        """Update fish position"""
        self.x += self.speed
        self.wobble += self.wobble_speed
        self.y += math.sin(self.wobble) * self.wobble_amount
        
    def draw(self, screen):
        """Draw the fish"""
        # Fish body
        body_rect = pygame.Rect(
            self.x - self.size, 
            self.y - self.size // 2, 
            self.size * 2, 
            self.size
        )
        pygame.draw.ellipse(screen, self.color, body_rect)
        
        # Fish tail
        tail_points = []
        if self.speed > 0:  # Fish facing right
            tail_points = [
                (self.x - self.size, self.y),
                (self.x - self.size * 1.5, self.y - self.size // 2),
                (self.x - self.size * 1.5, self.y + self.size // 2)
            ]
            # Eye
            eye_x = self.x + self.size // 2
            eye_y = self.y - self.size // 4
        else:  # Fish facing left
            tail_points = [
                (self.x + self.size, self.y),
                (self.x + self.size * 1.5, self.y - self.size // 2),
                (self.x + self.size * 1.5, self.y + self.size // 2)
            ]
            # Eye
            eye_x = self.x - self.size // 2
            eye_y = self.y - self.size // 4
            
        pygame.draw.polygon(screen, self.color, tail_points)
        
        # Eye
        pygame.draw.circle(screen, (255, 255, 255), (int(eye_x), int(eye_y)), max(2, self.size // 5))
        pygame.draw.circle(screen, (0, 0, 0), (int(eye_x), int(eye_y)), max(1, self.size // 8))

class PlayerFish(Fish):
    def __init__(self, x, y, size=10):
        # Use a distinct color for player fish - teal/turquoise that's not in FISH_COLORS
        super().__init__(x, y, size, 0, (0, 200, 200))  # Teal/turquoise player fish
        self.base_speed = 5
        self.facing_right = True
        
    def update(self, move_x, move_y, screen_width, screen_height):
        """Update player position based on input"""
        # Update position
        self.x += move_x * self.base_speed
        self.y += move_y * self.base_speed
        
        # Update facing direction
        if move_x > 0:
            self.facing_right = True
        elif move_x < 0:
            self.facing_right = False
            
        # Keep player on screen
        self.x = max(self.size, min(screen_width - self.size, self.x))
        self.y = max(self.size, min(screen_height - self.size, self.y))
        
    def grow(self, amount):
        """Increase player size"""
        self.size += amount
        
    def draw(self, screen):
        """Draw the player fish"""
        # Fish body
        body_rect = pygame.Rect(
            self.x - self.size, 
            self.y - self.size // 2, 
            self.size * 2, 
            self.size
        )
        pygame.draw.ellipse(screen, self.color, body_rect)
        
        # Fish tail
        tail_points = []
        if self.facing_right:  # Fish facing right
            tail_points = [
                (self.x - self.size, self.y),
                (self.x - self.size * 1.5, self.y - self.size // 2),
                (self.x - self.size * 1.5, self.y + self.size // 2)
            ]
            # Eye
            eye_x = self.x + self.size // 2
            eye_y = self.y - self.size // 4
        else:  # Fish facing left
            tail_points = [
                (self.x + self.size, self.y),
                (self.x + self.size * 1.5, self.y - self.size // 2),
                (self.x + self.size * 1.5, self.y + self.size // 2)
            ]
            # Eye
            eye_x = self.x - self.size // 2
            eye_y = self.y - self.size // 4
            
        pygame.draw.polygon(screen, self.color, tail_points)
        
        # Eye
        pygame.draw.circle(screen, (255, 255, 255), (int(eye_x), int(eye_y)), max(2, self.size // 5))
        pygame.draw.circle(screen, (0, 0, 0), (int(eye_x), int(eye_y)), max(1, self.size // 8))

class Shark(Entity):
    def __init__(self, x, y, size=30):
        super().__init__(x, y, size)
        self.speed = 2
        self.color = (100, 100, 100)  # Gray shark
        self.aggression = 0.5  # How aggressively it follows the player
        self.direction = -1  # -1 for left, 1 for right
        
    def update(self, player_x, player_y, screen_width):
        """Update shark position, moving toward player"""
        # Determine if shark should be on screen
        if self.x < -100:
            self.x = screen_width + 100
            self.y = random.randint(50, screen_width - 50)
            self.direction = -1
        elif self.x > screen_width + 100:
            self.x = -100
            self.y = random.randint(50, screen_width - 50)
            self.direction = 1
            
        # Move shark
        self.x += self.speed * self.direction
        
        # Sometimes change direction to follow player
        if random.random() < self.aggression * 0.02:
            if player_x > self.x:
                self.direction = 1
            else:
                self.direction = -1
                
        # Occasionally adjust y position to move toward player
        if random.random() < self.aggression * 0.05:
            if player_y > self.y:
                self.y += 1
            else:
                self.y -= 1
        
    def draw(self, screen):
        """Draw the shark"""
        # Shark body
        body_rect = pygame.Rect(
            self.x - self.size, 
            self.y - self.size // 2, 
            self.size * 2, 
            self.size
        )
        pygame.draw.ellipse(screen, self.color, body_rect)
        
        # Shark fin
        fin_points = [
            (self.x, self.y - self.size // 2),
            (self.x, self.y - self.size),
            (self.x + self.size // 2 * self.direction, self.y - self.size // 2)
        ]
        pygame.draw.polygon(screen, self.color, fin_points)
        
        # Shark tail
        tail_points = []
        if self.direction > 0:  # Shark facing right
            tail_points = [
                (self.x - self.size, self.y),
                (self.x - self.size * 1.5, self.y - self.size // 2),
                (self.x - self.size * 1.5, self.y + self.size // 2)
            ]
            # Eye
            eye_x = self.x + self.size // 2
            eye_y = self.y - self.size // 4
        else:  # Shark facing left
            tail_points = [
                (self.x + self.size, self.y),
                (self.x + self.size * 1.5, self.y - self.size // 2),
                (self.x + self.size * 1.5, self.y + self.size // 2)
            ]
            # Eye
            eye_x = self.x - self.size // 2
            eye_y = self.y - self.size // 4
            
        pygame.draw.polygon(screen, self.color, tail_points)
        
        # Eye
        pygame.draw.circle(screen, (255, 255, 255), (int(eye_x), int(eye_y)), max(2, self.size // 5))
        pygame.draw.circle(screen, (255, 0, 0), (int(eye_x), int(eye_y)), max(1, self.size // 8))

class Bubble:
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        self.alpha = random.randint(100, 200)
        
    def update(self):
        """Update bubble position"""
        self.y -= self.speed
        self.x += random.uniform(-0.5, 0.5)  # Slight horizontal movement
        
    def draw(self, screen):
        """Draw the bubble"""
        bubble_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(bubble_surface, (255, 255, 255, self.alpha), 
                          (self.size, self.size), self.size)
        screen.blit(bubble_surface, (int(self.x - self.size), int(self.y - self.size)))
        
