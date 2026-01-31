import pygame

# TODO: Doesn't work on Trimui
#import numpy as np

# Colors for fish - removed teal/turquoise to keep it distinct for player
FISH_COLORS = [
    (255, 0, 0),      # Red
    (0, 255, 0),      # Green
    (0, 0, 255),      # Blue
    (255, 255, 0),    # Yellow
    (255, 0, 255),    # Magenta
    (255, 165, 0),    # Orange
    (128, 0, 128),    # Purple
    (0, 128, 0),      # Dark Green
    (70, 130, 180),   # Steel Blue
    (255, 105, 180),  # Hot Pink
]

# Background color (ocean blue)
BACKGROUND_COLOR = (0, 105, 148)

# Game constants
BUBBLE_SPAWN_RATE = 0.03  # Chance per frame to spawn a bubble

def generate_eat_sound():
    """Generate a simple 'gulp' sound effect"""
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
        arr = np.random.randint(-32768, 32767, 44100 // 3, dtype=np.int16)
        # Apply a simple envelope
        for i in range(len(arr)):
            if i < 5000:
                arr[i] = arr[i] * i // 5000
            else:
                arr[i] = arr[i] * (len(arr) - i) // (len(arr) - 5000)
        sound = pygame.sndarray.make_sound(arr)
        return sound
    except:
        return None

def generate_game_over_sound():
    """Generate a simple 'game over' sound effect"""
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
        arr = np.zeros(44100, dtype=np.int16)
        for i in range(44100):
            t = i / 44100.0
            if t < 0.5:
                freq = 440 - 200 * t
            else:
                freq = 340 - 300 * (t - 0.5)
            arr[i] = int(32767 * 0.8 * np.sin(2 * np.pi * freq * t))
        sound = pygame.sndarray.make_sound(arr)
        return sound
    except:
        return None

def generate_level_up_sound():
    """Generate a simple 'level up' sound effect"""
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
        arr = np.zeros(44100 // 2, dtype=np.int16)
        for i in range(len(arr)):
            t = i / 44100.0
            freq = 440 + 440 * t
            arr[i] = int(32767 * 0.7 * np.sin(2 * np.pi * freq * t))
        sound = pygame.sndarray.make_sound(arr)
        return sound
    except:
        return None

def create_beep(frequency, duration):
    """Create a simple beep sound as fallback"""
    try:
        sample_rate = 44100
        bits = 16
        
        pygame.mixer.init(frequency=sample_rate, size=-bits, channels=1)
        
        # Generate a square wave
        buf = bytearray(int(duration * sample_rate / 1000))
        for i in range(len(buf)):
            if (i * frequency * 2 / sample_rate) % 2 < 1:
                buf[i] = 64
            else:
                buf[i] = 196
        
        return pygame.mixer.Sound(buffer=buf)
    except:
        return None
    
