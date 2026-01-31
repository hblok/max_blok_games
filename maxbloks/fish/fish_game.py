import random
import pygame

from maxbloks.fish.game_framework import GameFramework
from maxbloks.fish.entities import PlayerFish, Fish, Shark, Bubble
from maxbloks.fish.utils import FISH_COLORS, BACKGROUND_COLOR, BUBBLE_SPAWN_RATE
from maxbloks.fish.utils import generate_eat_sound, generate_game_over_sound, generate_level_up_sound, create_beep


class FishGame(GameFramework):
    def __init__(self, width=800, height=600, title="Fish Feeding Frenzy", fps=60):
        super().__init__(width, height, title, fps)
        self.init_game()
        
    def init_game(self):
        """Initialize game state and entities"""
        # Game state
        self.score = 0
        self.game_over = False
        self.game_won = False
        self.level = 1
        
        # Create entities
        self.player = PlayerFish(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2)
        self.fishes = []
        self.shark = Shark(self.SCREEN_WIDTH + 100, random.randint(50, self.SCREEN_HEIGHT - 50))
        self.bubbles = []
        
        # Spawn initial fish
        self.spawn_fish(10)
        
        # Load background image
        self.background = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.background.fill(BACKGROUND_COLOR)
        
        # Load sounds with fallbacks
        #pygame.mixer.init()
        
        # Try to load sound files first
        self.eat_sound = None
        self.game_over_sound = None
        self.level_up_sound = None
        
        try:
            #self.eat_sound = pygame.mixer.Sound("eat.wav")
            pass
        except:
            print("Warning: Could not load eat.wav, using generated sound")
            # Try numpy-generated sounds
            self.eat_sound = generate_eat_sound()
            # If that fails, try simple beep
            if not self.eat_sound:
                self.eat_sound = create_beep(440, 100)
        
        try:
            #self.game_over_sound = pygame.mixer.Sound("game_over.wav")
            pass
        except:
            print("Warning: Could not load game_over.wav, using generated sound")
            self.game_over_sound = generate_game_over_sound()
            if not self.game_over_sound:
                self.game_over_sound = create_beep(220, 500)
        
        try:
            #self.level_up_sound = pygame.mixer.Sound("level_up.wav")
            pass
        except:
            print("Warning: Could not load level_up.wav, using generated sound")
            self.level_up_sound = generate_level_up_sound()
            if not self.level_up_sound:
                self.level_up_sound = create_beep(880, 200)
        
    def spawn_fish(self, count):
        """Spawn a number of fish with random properties"""
        for _ in range(count):
            size = random.randint(5, 30)
            # Smaller fish are more common
            if random.random() < 0.7:
                size = random.randint(5, 15)
                
            # Determine spawn side (left or right)
            from_left = random.choice([True, False])
            
            if from_left:
                x = -50
                speed = random.uniform(1, 3)
            else:
                x = self.SCREEN_WIDTH + 50
                speed = random.uniform(-3, -1)
                
            y = random.randint(50, self.SCREEN_HEIGHT - 50)
            color = random.choice(FISH_COLORS)
            
            self.fishes.append(Fish(x, y, size, speed, color))
    
    def handle_input(self):
        """Handle player input"""
        super().handle_input()
        
        # Restart game if game over and restart button pressed
        if (self.game_over or self.game_won) and self.restart_button_pressed:
            self.init_game()
            
    def update(self):
        """Update game state"""
        if self.game_over or self.game_won:
            return
            
        # Update player
        self.player.update(self.movement_x, self.movement_y, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        
        # Update fish
        for fish in self.fishes[:]:
            fish.update()
            
            # Remove fish that are off-screen
            if (fish.x < -100 and fish.speed < 0) or (fish.x > self.SCREEN_WIDTH + 100 and fish.speed > 0):
                self.fishes.remove(fish)
                
            # Check collision with player
            if self.player.collides_with(fish):
                if self.player.size >= fish.size:
                    # Player eats fish
                    self.fishes.remove(fish)
                    self.player.grow(fish.size * 0.1)  # Growth proportional to eaten fish size
                    self.score += int(fish.size)
                    if self.eat_sound:
                        self.eat_sound.play()
                    
                    # Level up if player reaches certain sizes
                    if self.player.size >= 20 and self.level == 1:
                        self.level = 2
                        if self.level_up_sound:
                            self.level_up_sound.play()
                    elif self.player.size >= 40 and self.level == 2:
                        self.level = 3
                        if self.level_up_sound:
                            self.level_up_sound.play()
        
        # Update shark
        self.shark.update(self.player.x, self.player.y, self.SCREEN_WIDTH)
        
        # Check collision with shark
        if self.player.collides_with(self.shark):
            if self.player.size > self.shark.size:
                # Player eats shark - win condition
                self.game_won = True
                if self.level_up_sound:
                    self.level_up_sound.play()
            else:
                # Shark eats player - game over
                self.game_over = True
                if self.game_over_sound:
                    self.game_over_sound.play()
        
        # Spawn new fish if needed
        if len(self.fishes) < 10:
            self.spawn_fish(5)
            
        # Randomly spawn bubbles
        if random.random() < BUBBLE_SPAWN_RATE:
            x = random.randint(0, self.SCREEN_WIDTH)
            y = self.SCREEN_HEIGHT + 10
            size = random.randint(2, 8)
            speed = random.uniform(1, 3)
            self.bubbles.append(Bubble(x, y, size, speed))
            
        # Update bubbles
        for bubble in self.bubbles[:]:
            bubble.update()
            if bubble.y < -20:
                self.bubbles.remove(bubble)
    
    def draw(self):
        """Draw game elements"""
        # Draw background
        self.screen.blit(self.background, (0, 0))
        
        # Draw bubbles
        for bubble in self.bubbles:
            bubble.draw(self.screen)
        
        # Draw fish
        for fish in self.fishes:
            fish.draw(self.screen)
            
        # Draw shark
        self.shark.draw(self.screen)
        
        # Draw player
        self.player.draw(self.screen)
        
        # Draw UI
        self.draw_text(f"Score: {self.score}", 10, 10, 24, self.WHITE)
        self.draw_text(f"Size: {int(self.player.size)}", 10, 40, 24, self.WHITE)
        self.draw_text(f"Level: {self.level}", 10, 70, 24, self.WHITE)
        
        # Draw game over/win screen
        if self.game_over:
            self.draw_text("GAME OVER", self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 50, 
                          48, self.RED, center=True)
            self.draw_text(f"Final Score: {self.score}", self.SCREEN_WIDTH // 2, 
                          self.SCREEN_HEIGHT // 2, 36, self.WHITE, center=True)
            self.draw_text("Press R to restart", self.SCREEN_WIDTH // 2, 
                          self.SCREEN_HEIGHT // 2 + 50, 24, self.WHITE, center=True)
        elif self.game_won:
            self.draw_text("YOU WIN!", self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 50, 
                          48, self.GREEN, center=True)
            self.draw_text(f"Final Score: {self.score}", self.SCREEN_WIDTH // 2, 
                          self.SCREEN_HEIGHT // 2, 36, self.WHITE, center=True)
            self.draw_text("Press R to restart", self.SCREEN_WIDTH // 2, 
                          self.SCREEN_HEIGHT // 2 + 50, 24, self.WHITE, center=True)
        
        # Draw button prompts
        if not self.game_over and not self.game_won:
            self.draw_button_prompts(["WASD/Arrows: Move", "Grow by eating smaller fish", 
                                     "Avoid the shark until you're bigger!"])
        
        pygame.display.flip()
        
