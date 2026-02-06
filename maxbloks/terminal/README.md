# Terminal Editor for Handheld Gaming Devices

A minimal terminal command launcher designed for handheld gaming devices like Anbernic or R46H. This application provides a gamepad-friendly interface for executing Linux shell commands without requiring a physical keyboard.

![Terminal Editor](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

### 🎮 Gamepad-First Design
- Full D-pad and button navigation
- No physical keyboard required
- Smooth scrolling and visual feedback
- Intuitive multi-stage command selection

### ⌨️ Virtual Keyboard
- Full QWERTY on-screen keyboard
- Multiple input modes (lowercase, uppercase, numbers, symbols)
- D-pad navigation optimized for gamepad
- Input validation for different types (ports, URLs, hostnames)
- Essential for SSH, curl, and other commands requiring text input

### 📋 Smart Command Selection
- **Stage 1**: Select from a list of common Linux commands
- **Stage 2**: Choose context-appropriate arguments for the selected command
- **Stage 3**: Submenus for complex options (SSH options, package selection)

### 🔧 Intelligent Arguments
- Static arguments with descriptions (e.g., `-l` for "Long format")
- Dynamic arguments based on context:
  - Directory listings for `cd`, `ls`
  - File listings for `cat`, `grep`
  - Running processes for `kill`
  - SSH hosts from `~/.ssh/config` and history
  - Recent URLs for curl
  - Package lists for apt
- Removable argument "chips" for easy command editing

### 🌐 Advanced Commands
- **SSH**: Full support with port, identity files, port forwarding, and options
- **APT**: Package management with search, install, remove, and common packages
- **curl**: HTTP client with methods, headers, authentication, and URL history
- **SCP**: Secure file copy with all SSH options

### 🔴 Live Output Mode
- Real-time output for long-running commands (`htop`, `top`, `tail -f`)
- Auto-scrolling with manual scroll override
- Live indicator with line count
- Cancel running commands with B button

### 🛡️ Safety Features
- Confirmation dialogs for dangerous commands (`rm`, `reboot`, etc.)
- Clear warning messages explaining potential risks
- Visual indicators for dangerous operations

### 📊 Output Display
- Scrollable output panel
- Expandable full-screen output view
- Color-coded success/error messages
- Command history tracking
- Live mode with blinking indicator

## Screenshots

```
┌─────────────────────────────────────────────────────────────┐
│ 📁 ~/projects                                        Ready  │
│ $ ls -la                                                    │
├─────────────────────────────────────────────────────────────┤
│ ▶ ls                              List directory contents   │
│ ▶ cd                              Change directory          │
│ ▶ cat                             Display file contents     │
│ ▶ grep                            Search text patterns      │
│ ▶ ps                              List running processes    │
│ ...                                                         │
├─────────────────────────────────────────────────────────────┤
│ OUTPUT                                                      │
│ ✓ Command completed successfully                            │
├─────────────────────────────────────────────────────────────┤
│ ↑↓ Navigate  ←→ Page  A Select  X Execute  SELECT Output    │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.7 or higher
- Pygame 2.0 or higher

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install pygame directly:

```bash
pip install pygame
```

### Running the Application

```bash
python terminal_editor.py
```

Or make it executable:

```bash
chmod +x terminal_editor.py
./terminal_editor.py
```

## Controls

### Default Button Mapping

| Button | Action |
|--------|--------|
| **D-pad Up/Down** | Navigate through lists |
| **D-pad Left/Right** | Page scroll (fast navigation) |
| **A** | Select/Confirm/Type character |
| **B** | Back/Cancel/Delete character |
| **X** | Execute command/Confirm input |
| **Y** | Clear command/Toggle keyboard mode |
| **L** | Edit argument chips |
| **R** | (Reserved for cursor movement) |
| **Start** | Exit application/Cancel keyboard |
| **Select** | Toggle output view |

### Keyboard Controls (for testing on PC)

| Key | Action |
|-----|--------|
| **Arrow Keys** | Navigate |
| **Enter** | Select/Confirm |
| **Escape** | Back/Cancel |
| **X** | Execute |
| **Y** | Clear/Mode toggle |
| **L** | Edit chips |
| **R** | (Reserved) |
| **Tab** | Toggle output |
| **Q** | Exit |

### Virtual Keyboard Controls

| Button | Action |
|--------|--------|
| **D-pad** | Move between keys |
| **A** | Type selected character |
| **B** | Delete character (backspace) |
| **X** | Confirm and submit input |
| **Y** | Toggle keyboard mode (abc/ABC/123/symbols) |
| **Start** | Cancel input |

## Configuration

Edit `config.py` to customize:

### Button Mappings
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

### Adding New Commands
```python
COMMANDS = {
    'mycommand': {
        'description': 'My custom command',
        'arguments': [
            {'arg': '-v', 'desc': 'Verbose mode'},
            {'arg': '-h', 'desc': 'Show help'},
            # Argument requiring text input:
            {'arg': '-f', 'desc': 'File path', 'needs_input': True, 'input_type': 'text', 'input_prompt': 'Enter file path'},
            # Argument with submenu:
            {'arg': '-o', 'desc': 'Options', 'has_submenu': True, 'submenu_type': 'my_options'},
        ],
        'dynamic_args': None,  # or 'files', 'directories', 'processes', 'ssh_hosts', 'recent_urls'
        'needs_host_input': False,  # True for SSH-like commands
        'needs_url_input': False,   # True for curl-like commands
        'dangerous': False,
    },
    # ... more commands
}
```

### Dynamic Argument Types
- `None` - No dynamic arguments
- `'files'` - List files in current directory
- `'directories'` - List directories in current directory
- `'files_and_dirs'` - List both files and directories
- `'processes'` - List running processes (PID and info)
- `'process_names'` - List process names
- `'ssh_hosts'` - SSH hosts from config and history
- `'recent_urls'` - Recently used URLs

### Input Types for Virtual Keyboard
- `'text'` - Any text input
- `'numeric'` - Numbers only
- `'port'` - Port number (1-65535)
- `'url'` - URL format validation
- `'ssh_host'` - user@hostname format
- `'filename'` - Valid filename characters

### Color Scheme
```python
COLORS = {
    'background': (18, 18, 18),
    'text': (220, 220, 220),
    'highlight': (0, 122, 204),
    'error': (244, 71, 71),
    'success': (78, 201, 176),
    # ... more colors
}
```

## Included Commands

The application comes pre-configured with 49 common Linux commands:

### File Operations
- `ls`, `cd`, `cat`, `head`, `tail`
- `cp`, `mv`, `rm`, `mkdir`, `rmdir`
- `chmod`, `chown`
- `find`, `grep`, `wc`

### System Information
- `ps`, `top`, `htop`
- `df`, `free`, `du`
- `uname`, `uptime`, `date`
- `whoami`, `pwd`

### Process Management
- `kill`, `killall`

### Network & Remote Access
- `ip`, `ping`, `wget`
- `curl` - Enhanced with HTTP methods, headers, auth, URL history
- `ssh` - Full support with port, identity, forwarding, options
- `scp` - Secure copy with SSH options

### Package Management
- `apt` - Install, remove, search, update with common package suggestions

### Archives
- `tar`, `zip`, `unzip`

### System Control
- `reboot`, `poweroff`
- `mount`, `umount`

### Device Information
- `lsblk`, `lsusb`, `lspci`, `dmesg`

### Common Packages (for apt install)
Pre-configured package suggestions organized by category:
- **Development**: build-essential, git, python3, nodejs, gcc, make, cmake, golang, rustc
- **Utilities**: htop, tmux, vim, nano, curl, wget, jq, ripgrep, ranger
- **System**: openssh-server, ufw, fail2ban, rsync, cron
- **Media**: ffmpeg, imagemagick, vlc, mpv, yt-dlp
- **Network**: nmap, netcat, tcpdump, iftop, mtr, dnsutils

## Project Structure

```
terminal_editor/
├── terminal_editor.py   # Main application with state management
├── config.py            # Configuration, commands, SSH options, packages
├── ui_components.py     # UI components (lists, dialogs, command builder)
├── virtual_keyboard.py  # On-screen keyboard for text input
├── command_executor.py  # Command execution with live output support
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Architecture

### Main Components

1. **TerminalEditor** (`terminal_editor.py`)
   - Main application class
   - Event handling and game loop
   - State management

2. **CommandExecutor** (`command_executor.py`)
   - Safe command execution with subprocess
   - Timeout handling
   - Working directory management
   - Command history

3. **UI Components** (`ui_components.py`)
   - `ScrollableList` - Navigable list with smooth scrolling
   - `OutputDisplay` - Command output viewer
   - `CommandBuilder` - Current command display
   - `ConfirmDialog` - Dangerous command confirmation
   - `ButtonHints` - Control hints display

4. **Configuration** (`config.py`)
   - Screen settings
   - Color scheme
   - Command definitions
   - Button mappings

## Device-Specific Setup

### Anbernic Devices
Most Anbernic devices use a standard button layout. The default configuration should work, but you may need to adjust `BUTTON_MAP` in `config.py` based on your specific model.

### R36S / R46H
These devices typically have the following button indices:
```python
BUTTON_MAP = {
    'A': 0,
    'B': 1,
    'X': 2,
    'Y': 3,
    'START': 7,
    'SELECT': 6,
}
```

### Finding Your Button Mappings
Run this test script to identify your device's button mappings:

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
        elif event.type == pygame.JOYHATMOTION:
            print(f"Hat: {event.value}")
        elif event.type == pygame.JOYAXISMOTION:
            if abs(event.value) > 0.5:
                print(f"Axis {event.axis}: {event.value}")
```

## Troubleshooting

### No Joystick Detected
- Ensure your device's gamepad is properly configured
- Check if pygame can see the joystick: `pygame.joystick.get_count()`
- Use keyboard controls as fallback

### Commands Not Executing
- Check if the command exists on your system
- Verify file permissions
- Check the output panel for error messages

### Display Issues
- Adjust `SCREEN_WIDTH` and `SCREEN_HEIGHT` in `config.py`
- Try different font sizes if text is too small/large

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Designed for the retro handheld gaming community
- Built with [Pygame](https://www.pygame.org/)
- Inspired by the need for keyboard-free terminal access on portable devices