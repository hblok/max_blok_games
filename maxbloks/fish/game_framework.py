import pygame
import sys


class GameFramework:
    def __init__(self, screen, display_info, title="Game", fps=60):
        pygame.init()
        pygame.joystick.init()
        
        # Screen setup
        self.screen = screen
        self.screen_width = display_info["width"]
        self.screen_height = display_info["height"]
        self.FPS = fps

        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        
        # Joystick setup
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
        
        # Game state
        self.running = True
        self.game_over = False
        self.game_won = False
        
        # Input state
        self.keys_pressed = set()
        self.mouse_pos = (0, 0)
        self.mouse_clicked = False
        self.shoot_button_pressed = False
        self.action_button_pressed = False
        self.restart_button_pressed = False
        
        # Movement input
        self.movement_x = 0
        self.movement_y = 0
        
        # Colors - commonly used
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.GRAY = (128, 128, 128)
        self.BROWN = (139, 69, 19)
        self.YELLOW = (255, 255, 0)
        self.PURPLE = (128, 0, 128)
        self.ORANGE = (255, 165, 0)
        self.DARK_GREEN = (0, 128, 0)
        self.LIGHT_BLUE = (173, 216, 230)
        self.DARK_GRAY = (64, 64, 64)
    
    def handle_input(self):
        """Handle common input - override this method to add game-specific input"""
        # Reset frame-based inputs
        self.mouse_clicked = False
        self.shoot_button_pressed = False
        self.action_button_pressed = False
        self.restart_button_pressed = False
        self.movement_x = 0
        self.movement_y = 0
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.keys_pressed.add(event.key)
                if event.key == pygame.K_SPACE:
                    self.shoot_button_pressed = True
                if event.key == pygame.K_x:
                    self.action_button_pressed = True
                if event.key == pygame.K_r:
                    self.restart_button_pressed = True
            elif event.type == pygame.KEYUP:
                self.keys_pressed.discard(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.mouse_clicked = True
                    self.shoot_button_pressed = True
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button in [8, 13]:  # Start/Options buttons (exit)
                    self.running = False
                elif event.button in [0, 1]:  # A/B buttons (shoot/action)
                    self.shoot_button_pressed = True
                elif event.button == 2:  # X button (action)
                    self.action_button_pressed = True
                elif event.button == 11:  # Y button (restart)
                    self.restart_button_pressed = True
        
        # Get mouse position
        self.mouse_pos = pygame.mouse.get_pos()
        
        # Handle continuous keyboard input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.movement_x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.movement_x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.movement_y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.movement_y += 1
        
        # Handle joystick movement
        if self.joystick:
            axis_x = self.joystick.get_axis(0)
            axis_y = self.joystick.get_axis(1)
            
            if abs(axis_x) > 0.1:
                self.movement_x += axis_x
            if abs(axis_y) > 0.1:
                self.movement_y += axis_y
        
        # Normalize movement (prevent faster diagonal movement)
        if self.movement_x != 0 and self.movement_y != 0:
            self.movement_x *= 0.707  # 1/sqrt(2)
            self.movement_y *= 0.707
    
    def update(self):
        """Override this method with your game logic"""
        pass
    
    def draw(self):
        """Override this method with your drawing code"""
        self.screen.fill(self.BLACK)
        pygame.display.flip()
    
    def draw_text(self, text, x, y, size=24, color=None, center=False):
        """Helper method to draw text"""
        if color is None:
            color = self.WHITE
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)
        if center:
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)
        else:
            self.screen.blit(text_surface, (x, y))
    
    def draw_health_bar(self, x, y, width, height, current_health, max_health, 
                       bg_color=None, health_color=None, border_color=None):
        """Helper method to draw health bars"""
        if bg_color is None:
            bg_color = self.RED
        if health_color is None:
            health_color = self.GREEN
        if border_color is None:
            border_color = self.WHITE
        
        health_ratio = max(0, min(1, current_health / max_health))
        
        # Background
        pygame.draw.rect(self.screen, bg_color, (x, y, width, height))
        # Health
        pygame.draw.rect(self.screen, health_color, (x, y, width * health_ratio, height))
        # Border
        pygame.draw.rect(self.screen, border_color, (x, y, width, height), 2)
    
    def draw_button_prompts(self, prompts):
        """Draw button prompts at the bottom of the screen"""
        y_pos = self.screen_height - 30
        x_pos = 10
        
        for prompt in prompts:
            self.draw_text(prompt, x_pos, y_pos, 16)
            x_pos += len(prompt) * 8 + 20
    
    def is_key_pressed(self, key):
        """Check if a key is currently pressed"""
        return key in self.keys_pressed
    
    def distance(self, x1, y1, x2, y2):
        """Calculate distance between two points"""
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    
    def clamp(self, value, min_val, max_val):
        """Clamp a value between min and max"""
        return max(min_val, min(value, max_val))
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(self.FPS)
        
        pygame.quit()
        sys.exit()

