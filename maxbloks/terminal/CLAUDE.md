# Terminal Editor for Handheld Gaming Devices

## Overview
A minimal terminal command launcher designed for handheld gaming devices like Anbernic or R46H. This application provides a gamepad-friendly interface for executing Linux shell commands without requiring a physical keyboard. It features a virtual keyboard, multi-stage command selection, intelligent argument suggestions, and live output monitoring.

## Purpose and Main Features

### Gamepad-First Design
- Full D-pad and button navigation
- No physical keyboard required
- Smooth scrolling and visual feedback
- Intuitive multi-stage command selection

### Virtual Keyboard
- Full QWERTY on-screen keyboard
- Multiple input modes (lowercase, uppercase, numbers, symbols)
- D-pad navigation optimized for gamepad
- Input validation for different types (ports, URLs, hostnames)

### Smart Command Selection
- **Stage 1**: Select from 49+ common Linux commands
- **Stage 2**: Choose context-appropriate arguments
- **Stage 3**: Submenus for complex options (SSH options, package selection)

### Intelligent Arguments
- Static arguments with descriptions
- Dynamic arguments based on context:
  - Directory listings for `cd`, `ls`
  - File listings for `cat`, `grep`
  - Running processes for `kill`
  - SSH hosts from `~/.ssh/config` and history
  - Recent URLs for curl
  - Package lists for apt

### Live Output Mode
- Real-time output for long-running commands (`htop`, `top`, `tail -f`)
- Auto-scrolling with manual scroll override
- Live indicator with line count
- Cancel running commands with B button

### Safety Features
- Confirmation dialogs for dangerous commands (`rm`, `reboot`, etc.)
- Clear warning messages explaining potential risks
- Visual indicators for dangerous operations

## Dependencies

### External
- Python 3.7+
- pygame 2.0+

### Internal (from maxbloks)
- `maxbloks.terminal.core.compat_sdl` - SDL display initialization (symlink to `../../common/compat_sdl.py`)

## File Structure

```
terminal/
├── main.py                    # Entry point
├── core/
│   ├── __init__.py
│   ├── terminal_editor.py     # Main application with state management
│   ├── command_executor.py    # Command execution with live output support
│   └── compat_sdl.py          # SDL compatibility layer (symlink)
├── ui/
│   ├── __init__.py
│   ├── font_manager.py        # Font loading and management
│   ├── virtual_keyboard.py    # On-screen keyboard for text input
│   ├── output_display.py      # Command output viewer
│   ├── scrollable_list.py     # Navigable list with smooth scrolling
│   ├── command_builder.py     # Current command display with chips
│   ├── confirm_dialog.py      # Dangerous command confirmation
│   └── button_hints.py        # Control hints display
├── config/
│   └── config.py              # Configuration, commands, SSH options, packages
├── tests/
│   ├── test_font_manager.py
│   ├── test_command_executor.py
│   ├── test_scrollable_list.py
│   ├── test_output_display.py
│   ├── test_command_builder.py
│   └── test_button_hints.py
├── BUILD                      # Bazel build configuration
├── README.md                  # Detailed documentation
├── game.json                  # Game metadata
├── version.json               # Version information
├── Terminal.png               # Application icon
└── Terminal.sh                # Launch script
```

## Architecture

### Application States
```
COMMAND_SELECT → ARGUMENT_SELECT → SUBMENU_SELECT
       ↓               ↓                  ↓
       ←───────────────←──────────────────←
                       ↓
              KEYBOARD_INPUT
                       ↓
               CONFIRM_DIALOG
                       ↓
                 RUNNING/LIVE_OUTPUT
                       ↓
                OUTPUT_VIEW
```

### Key Classes

1. **TerminalEditor** (`core/terminal_editor.py`)
   - Main application class with state management
   - Event handling and game loop
   - Coordinates all UI components

2. **CommandExecutor** (`core/command_executor.py`)
   - Safe command execution with subprocess
   - Timeout handling and working directory management
   - Command history and live output support

3. **VirtualKeyboard** (`ui/virtual_keyboard.py`)
   - Full QWERTY keyboard with multiple modes
   - Input validation by type
   - Gamepad-optimized navigation

4. **ScrollableList** (`ui/scrollable_list.py`)
   - Navigable list with smooth scrolling
   - Page scroll support
   - Item selection callbacks

5. **OutputDisplay** (`ui/output_display.py`)
   - Scrollable output panel
   - Live mode with auto-scroll
   - Color-coded success/error messages

6. **CommandBuilder** (`ui/command_builder.py`)
   - Visual command construction with removable chips
   - Status display (running, success, error)
   - Working directory display

7. **ConfirmDialog** (`ui/confirm_dialog.py`)
   - Warning display for dangerous commands
   - Confirm/cancel options

### Configuration System (`config/config.py`)

#### Button Mappings
```python
BUTTON_MAP = {
    'A': 0,        # Select/Confirm
    'B': 1,        # Back/Cancel
    'X': 2,        # Execute
    'Y': 3,        # Clear
    'START': 7,    # Exit
    'SELECT': 6,   # Toggle output view
}
```

#### Adding New Commands
```python
COMMANDS = {
    'mycommand': {
        'description': 'My custom command',
        'arguments': [
            {'arg': '-v', 'desc': 'Verbose mode'},
            {'arg': '-f', 'desc': 'File path', 
             'needs_input': True, 'input_type': 'text'},
        ],
        'dynamic_args': 'files',  # or 'directories', 'processes', etc.
        'dangerous': False,
    },
}
```

#### Dynamic Argument Types
- `None` - No dynamic arguments
- `'files'` - List files in current directory
- `'directories'` - List directories
- `'files_and_dirs'` - List both
- `'processes'` - List running processes (PID and info)
- `'process_names'` - List process names
- `'ssh_hosts'` - SSH hosts from config and history
- `'recent_urls'` - Recently used URLs

#### Input Types for Virtual Keyboard
- `'text'` - Any text input
- `'numeric'` - Numbers only
- `'port'` - Port number (1-65535)
- `'url'` - URL format validation
- `'ssh_host'` - user@hostname format
- `'filename'` - Valid filename characters

## How to Run

```bash
# From the repository root:
pip install pygame

# Run the application:
python -m maxbloks.terminal.main
```

Or use the provided script:
```bash
./Terminal.sh
```

## Controls

### Keyboard (for testing on PC)
| Key | Action |
|-----|--------|
| Arrow Keys | Navigate |
| Enter | Select/Confirm |
| Escape | Back/Cancel |
| X | Execute |
| Y | Clear/Mode toggle |
| L | Edit chips |
| Tab | Toggle output |
| Q | Exit |

### Gamepad
| Button | Action |
|--------|--------|
| D-pad | Navigate |
| A | Select/Confirm |
| B | Back/Cancel/Delete |
| X | Execute/Confirm input |
| Y | Clear/Mode toggle |
| L | Edit argument chips |
| Start | Exit |
| Select | Toggle output view |

### Virtual Keyboard Controls
| Button | Action |
|--------|--------|
| D-pad | Move between keys |
| A | Type selected character |
| B | Delete character (backspace) |
| X | Confirm and submit input |
| Y | Toggle keyboard mode (abc/ABC/123/symbols) |
| Start | Cancel input |

## Included Commands

### File Operations
`ls`, `cd`, `cat`, `head`, `tail`, `cp`, `mv`, `rm`, `mkdir`, `rmdir`, `chmod`, `chown`, `find`, `grep`, `wc`

### System Information
`ps`, `top`, `htop`, `df`, `free`, `du`, `uname`, `uptime`, `date`, `whoami`, `pwd`

### Process Management
`kill`, `killall`

### Network & Remote Access
`ip`, `ping`, `wget`, `curl`, `ssh`, `scp`

### Package Management
`apt` - Install, remove, search, update with package suggestions

### Archives
`tar`, `zip`, `unzip`

### System Control
`reboot`, `poweroff`, `mount`, `umount`

### Device Information
`lsblk`, `lsusb`, `lspci`, `dmesg`

## Development Notes

### Running Tests
```bash
python -m unittest discover -s maxbloks/terminal/tests
```

### Device-Specific Setup
For Anbernic/R36S/R46H devices, verify button mappings:
```python
import pygame
pygame.init()
pygame.joystick.init()
js = pygame.joystick.Joystick(0)
js.init()

while True:
    for event in pygame.event.get():
        if event.type == pygame.JOYBUTTONDOWN:
            print(f"Button {event.button} pressed")
```

### Adding New SSH Options
Edit `SSH_OPTIONS` in `config/config.py`:
```python
SSH_OPTIONS = [
    {'arg': '-o StrictHostKeyChecking=no', 'desc': 'Skip host key check'},
    # Add more options...
]
```

### Adding Common Packages
Edit `COMMON_PACKAGES` in `config/config.py`:
```python
COMMON_PACKAGES = {
    'Development': [
        {'name': 'build-essential', 'desc': 'Build tools'},
    ],
    # Add more categories...
}
```

## Troubleshooting

### No Joystick Detected
- Ensure device gamepad is properly configured
- Check `pygame.joystick.get_count()`
- Use keyboard controls as fallback

### Commands Not Executing
- Verify command exists on system
- Check file permissions
- Review output panel for errors

### Display Issues
- Adjust `DEFAULT_SCREEN_WIDTH` and `DEFAULT_SCREEN_HEIGHT` in `config.py`
- Try different font sizes

## License
GPL-3.0-or-later