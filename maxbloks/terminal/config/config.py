"""
Configuration file for Terminal Editor
Easy to modify command definitions and settings
"""

# Screen settings
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Color scheme (terminal-like dark theme)
COLORS = {
    'background': (18, 18, 18),
    'panel_bg': (30, 30, 30),
    'text': (220, 220, 220),
    'text_dim': (128, 128, 128),
    'highlight': (0, 122, 204),
    'highlight_text': (255, 255, 255),
    'success': (78, 201, 176),
    'error': (244, 71, 71),
    'warning': (255, 193, 7),
    'border': (60, 60, 60),
    'command_text': (86, 156, 214),
    'argument_text': (206, 145, 120),
    'output_text': (212, 212, 212),
}

# Font settings
FONT_SIZE_LARGE = 24
FONT_SIZE_MEDIUM = 20
FONT_SIZE_SMALL = 16

# UI Layout
HEADER_HEIGHT = 80
FOOTER_HEIGHT = 60
LIST_ITEM_HEIGHT = 36
OUTPUT_PANEL_HEIGHT = 200

# Scroll settings
SCROLL_SPEED = 1
PAGE_SCROLL_ITEMS = 10

# History settings
MAX_HISTORY_SIZE = 10
MAX_RECENT_DIRS = 10

# Button mappings (pygame joystick buttons - may vary by device)
# These are common mappings, adjust for your specific device
BUTTON_MAP = {
    'A': 0,        # Select/Confirm
    'B': 1,        # Back/Cancel
    'X': 2,        # Execute
    'Y': 3,        # Clear
    'L': 4,        # Edit chips / Cursor left
    'R': 5,        # Cursor right
    'SELECT': 6,   # Toggle output view
    'START': 7,    # Exit
}

# D-pad axis mappings
DPAD_AXIS_X = 0  # Left/Right
DPAD_AXIS_Y = 1  # Up/Down

# Keyboard fallback mappings (for testing on PC)
KEY_MAP = {
    'UP': 'up',
    'DOWN': 'down',
    'LEFT': 'left',
    'RIGHT': 'right',
    'A': 'return',
    'B': 'escape',
    'X': 'x',
    'Y': 'y',
    'START': 'q',
    'SELECT': 'tab',
}

# Commands that require confirmation before execution
DANGEROUS_COMMANDS = [
    'rm',
    'reboot',
    'poweroff',
    'shutdown',
    'kill',
    'killall',
    'chmod',
    'chown',
    'dd',
    'mkfs',
    'fdisk',
]

# Command definitions with their arguments
# Format: 'command': {
#     'description': 'Brief description',
#     'arguments': [list of static arguments],
#     'dynamic_args': 'type of dynamic arguments to fetch',
#     'dangerous': bool
# }
COMMANDS = {
    'ls': {
        'description': 'List directory contents',
        'arguments': [
            {'arg': '-l', 'desc': 'Long format'},
            {'arg': '-a', 'desc': 'Show hidden files'},
            {'arg': '-lh', 'desc': 'Long format, human readable'},
            {'arg': '-la', 'desc': 'Long format with hidden'},
            {'arg': '-R', 'desc': 'Recursive listing'},
        ],
        'dynamic_args': 'directories',
        'dangerous': False,
    },
    'cd': {
        'description': 'Change directory',
        'arguments': [
            {'arg': '/', 'desc': 'Root directory'},
            {'arg': '~', 'desc': 'Home directory'},
            {'arg': '..', 'desc': 'Parent directory'},
            {'arg': '/home', 'desc': 'Home folder'},
            {'arg': '/media', 'desc': 'Media folder'},
            {'arg': '/tmp', 'desc': 'Temp folder'},    # nosec
            {'arg': '/var/log', 'desc': 'Log files'},
            {'arg': '/etc', 'desc': 'Config files'},
        ],
        'dynamic_args': 'directories',
        'dangerous': False,
    },
    'cat': {
        'description': 'Display file contents',
        'arguments': [
            {'arg': '-n', 'desc': 'Number lines'},
        ],
        'dynamic_args': 'files',
        'dangerous': False,
    },
    'head': {
        'description': 'Display first lines of file',
        'arguments': [
            {'arg': '-n 10', 'desc': 'First 10 lines'},
            {'arg': '-n 20', 'desc': 'First 20 lines'},
            {'arg': '-n 50', 'desc': 'First 50 lines'},
        ],
        'dynamic_args': 'files',
        'dangerous': False,
    },
    'tail': {
        'description': 'Display last lines of file',
        'arguments': [
            {'arg': '-n 10', 'desc': 'Last 10 lines'},
            {'arg': '-n 20', 'desc': 'Last 20 lines'},
            {'arg': '-f', 'desc': 'Follow (live updates)'},
        ],
        'dynamic_args': 'files',
        'dangerous': False,
    },
    'grep': {
        'description': 'Search text patterns',
        'arguments': [
            {'arg': '-i', 'desc': 'Case insensitive'},
            {'arg': '-r', 'desc': 'Recursive search'},
            {'arg': '-n', 'desc': 'Show line numbers'},
            {'arg': '-v', 'desc': 'Invert match'},
            {'arg': '-c', 'desc': 'Count matches'},
        ],
        'dynamic_args': 'files',
        'dangerous': False,
    },
    'find': {
        'description': 'Find files and directories',
        'arguments': [
            {'arg': '.', 'desc': 'Current directory'},
            {'arg': '-name "*.txt"', 'desc': 'Find .txt files'},
            {'arg': '-name "*.py"', 'desc': 'Find .py files'},
            {'arg': '-type f', 'desc': 'Files only'},
            {'arg': '-type d', 'desc': 'Directories only'},
        ],
        'dynamic_args': 'directories',
        'dangerous': False,
    },
    'ps': {
        'description': 'List running processes',
        'arguments': [
            {'arg': 'aux', 'desc': 'All processes (BSD style)'},
            {'arg': '-ef', 'desc': 'All processes (standard)'},
            {'arg': '-aux --sort=-%mem', 'desc': 'Sort by memory'},
            {'arg': '-aux --sort=-%cpu', 'desc': 'Sort by CPU'},
        ],
        'dynamic_args': None,
        'dangerous': False,
    },
    'kill': {
        'description': 'Terminate a process',
        'arguments': [
            {'arg': '-9', 'desc': 'Force kill (SIGKILL)'},
            {'arg': '-15', 'desc': 'Graceful (SIGTERM)'},
        ],
        'dynamic_args': 'processes',
        'dangerous': True,
    },
    'killall': {
        'description': 'Kill processes by name',
        'arguments': [
            {'arg': '-9', 'desc': 'Force kill'},
        ],
        'dynamic_args': 'process_names',
        'dangerous': True,
    },
    'df': {
        'description': 'Disk space usage',
        'arguments': [
            {'arg': '-h', 'desc': 'Human readable'},
            {'arg': '-T', 'desc': 'Show filesystem type'},
            {'arg': '-i', 'desc': 'Show inodes'},
        ],
        'dynamic_args': None,
        'dangerous': False,
    },
    'free': {
        'description': 'Memory usage',
        'arguments': [
            {'arg': '-h', 'desc': 'Human readable'},
            {'arg': '-m', 'desc': 'Show in MB'},
            {'arg': '-g', 'desc': 'Show in GB'},
        ],
        'dynamic_args': None,
        'dangerous': False,
    },
    'top': {
        'description': 'System monitor (view only)',
        'arguments': [
            {'arg': '-b -n 1', 'desc': 'Batch mode, single run'},
            {'arg': '-b -n 1 -o %MEM', 'desc': 'Sort by memory'},
            {'arg': '-b -n 1 -o %CPU', 'desc': 'Sort by CPU'},
        ],
        'dynamic_args': None,
        'dangerous': False,
    },
    'htop': {
        'description': 'Interactive process viewer',
        'arguments': [],
        'dynamic_args': None,
        'dangerous': False,
    },
    'pwd': {
        'description': 'Print working directory',
        'arguments': [],
        'dynamic_args': None,
        'dangerous': False,
    },
    'whoami': {
        'description': 'Current username',
        'arguments': [],
        'dynamic_args': None,
        'dangerous': False,
    },
    'uname': {
        'description': 'System information',
        'arguments': [
            {'arg': '-a', 'desc': 'All information'},
            {'arg': '-r', 'desc': 'Kernel release'},
            {'arg': '-m', 'desc': 'Machine hardware'},
        ],
        'dynamic_args': None,
        'dangerous': False,
    },
    'date': {
        'description': 'Current date and time',
        'arguments': [
            {'arg': '+%Y-%m-%d', 'desc': 'Date only'},
            {'arg': '+%H:%M:%S', 'desc': 'Time only'},
        ],
        'dynamic_args': None,
        'dangerous': False,
    },
    'uptime': {
        'description': 'System uptime',
        'arguments': [],
        'dynamic_args': None,
        'dangerous': False,
    },
    'mkdir': {
        'description': 'Create directory',
        'arguments': [
            {'arg': '-p', 'desc': 'Create parent dirs'},
        ],
        'dynamic_args': None,
        'dangerous': False,
    },
    'rmdir': {
        'description': 'Remove empty directory',
        'arguments': [],
        'dynamic_args': 'directories',
        'dangerous': True,
    },
    'rm': {
        'description': 'Remove files/directories',
        'arguments': [
            {'arg': '-f', 'desc': 'Force removal'},
            {'arg': '-r', 'desc': 'Recursive'},
            {'arg': '-rf', 'desc': 'Force recursive (DANGER!)'},
            {'arg': '-i', 'desc': 'Interactive mode'},
        ],
        'dynamic_args': 'files_and_dirs',
        'dangerous': True,
    },
    'cp': {
        'description': 'Copy files/directories',
        'arguments': [
            {'arg': '-r', 'desc': 'Recursive copy'},
            {'arg': '-v', 'desc': 'Verbose'},
            {'arg': '-i', 'desc': 'Interactive'},
        ],
        'dynamic_args': 'files_and_dirs',
        'dangerous': False,
    },
    'mv': {
        'description': 'Move/rename files',
        'arguments': [
            {'arg': '-v', 'desc': 'Verbose'},
            {'arg': '-i', 'desc': 'Interactive'},
        ],
        'dynamic_args': 'files_and_dirs',
        'dangerous': False,
    },
    'chmod': {
        'description': 'Change file permissions',
        'arguments': [
            {'arg': '755', 'desc': 'rwxr-xr-x (executable)'},
            {'arg': '644', 'desc': 'rw-r--r-- (read only)'},
            {'arg': '777', 'desc': 'rwxrwxrwx (full access)'},
            {'arg': '600', 'desc': 'rw------- (private)'},
            {'arg': '+x', 'desc': 'Add execute'},
            {'arg': '-x', 'desc': 'Remove execute'},
            {'arg': '-R', 'desc': 'Recursive'},
        ],
        'dynamic_args': 'files_and_dirs',
        'dangerous': True,
    },
    'chown': {
        'description': 'Change file owner',
        'arguments': [
            {'arg': '-R', 'desc': 'Recursive'},
        ],
        'dynamic_args': 'files_and_dirs',
        'dangerous': True,
    },
    'du': {
        'description': 'Directory disk usage',
        'arguments': [
            {'arg': '-h', 'desc': 'Human readable'},
            {'arg': '-s', 'desc': 'Summary only'},
            {'arg': '-sh *', 'desc': 'Size of each item'},
        ],
        'dynamic_args': 'directories',
        'dangerous': False,
    },
    'wc': {
        'description': 'Word/line/byte count',
        'arguments': [
            {'arg': '-l', 'desc': 'Line count'},
            {'arg': '-w', 'desc': 'Word count'},
            {'arg': '-c', 'desc': 'Byte count'},
        ],
        'dynamic_args': 'files',
        'dangerous': False,
    },
    'echo': {
        'description': 'Print text',
        'arguments': [
            {'arg': '$PATH', 'desc': 'Show PATH'},
            {'arg': '$HOME', 'desc': 'Show HOME'},
            {'arg': '$USER', 'desc': 'Show USER'},
        ],
        'dynamic_args': None,
        'dangerous': False,
    },
    'clear': {
        'description': 'Clear terminal',
        'arguments': [],
        'dynamic_args': None,
        'dangerous': False,
    },
    'history': {
        'description': 'Command history (app)',
        'arguments': [],
        'dynamic_args': None,
        'dangerous': False,
    },
    'reboot': {
        'description': 'Restart system',
        'arguments': [],
        'dynamic_args': None,
        'dangerous': True,
    },
    'poweroff': {
        'description': 'Shutdown system',
        'arguments': [],
        'dynamic_args': None,
        'dangerous': True,
    },
    'ip': {
        'description': 'Network information',
        'arguments': [
            {'arg': 'addr', 'desc': 'Show IP addresses'},
            {'arg': 'link', 'desc': 'Show interfaces'},
            {'arg': 'route', 'desc': 'Show routing table'},
        ],
        'dynamic_args': None,
        'dangerous': False,
    },
    'ping': {
        'description': 'Test network connection',
        'arguments': [
            {'arg': '-c 4 localhost', 'desc': 'Ping localhost'},
            {'arg': '-c 4 8.8.8.8', 'desc': 'Ping Google DNS'},
            {'arg': '-c 4 1.1.1.1', 'desc': 'Ping Cloudflare'},
        ],
        'dynamic_args': None,
        'dangerous': False,
    },
    'wget': {
        'description': 'Download files',
        'arguments': [
            {'arg': '-q', 'desc': 'Quiet mode'},
            {'arg': '-O', 'desc': 'Output filename'},
        ],
        'dynamic_args': None,
        'dangerous': False,
    },
    'curl': {
        'description': 'Transfer data / HTTP client',
        'arguments': [
            {'arg': '-X GET', 'desc': 'GET request'},
            {'arg': '-X POST', 'desc': 'POST request'},
            {'arg': '-X PUT', 'desc': 'PUT request'},
            {'arg': '-X DELETE', 'desc': 'DELETE request'},
            {'arg': '-X PATCH', 'desc': 'PATCH request'},
            {'arg': '-H', 'desc': 'Add header', 'needs_input': True, 'input_type': 'text', 'input_prompt': 'Enter header (e.g., Content-Type: application/json)'},
            {'arg': '-d', 'desc': 'POST data', 'needs_input': True, 'input_type': 'text', 'input_prompt': 'Enter POST data'},
            {'arg': '-u', 'desc': 'Authentication', 'needs_input': True, 'input_type': 'text', 'input_prompt': 'Enter user:password'},
            {'arg': '-o', 'desc': 'Output file', 'needs_input': True, 'input_type': 'filename', 'input_prompt': 'Enter output filename'},
            {'arg': '-s', 'desc': 'Silent mode'},
            {'arg': '-I', 'desc': 'Headers only'},
            {'arg': '-k', 'desc': 'Insecure (ignore SSL)'},
            {'arg': '-L', 'desc': 'Follow redirects'},
            {'arg': '-v', 'desc': 'Verbose output'},
            {'arg': '-O', 'desc': 'Save with remote name'},
        ],
        'dynamic_args': 'recent_urls',
        'needs_url_input': True,
        'dangerous': False,
    },
    'tar': {
        'description': 'Archive files',
        'arguments': [
            {'arg': '-cvf', 'desc': 'Create archive'},
            {'arg': '-xvf', 'desc': 'Extract archive'},
            {'arg': '-tvf', 'desc': 'List contents'},
            {'arg': '-czvf', 'desc': 'Create gzip archive'},
            {'arg': '-xzvf', 'desc': 'Extract gzip archive'},
        ],
        'dynamic_args': 'files',
        'dangerous': False,
    },
    'unzip': {
        'description': 'Extract zip files',
        'arguments': [
            {'arg': '-l', 'desc': 'List contents'},
        ],
        'dynamic_args': 'files',
        'dangerous': False,
    },
    'zip': {
        'description': 'Create zip archive',
        'arguments': [
            {'arg': '-r', 'desc': 'Recursive'},
        ],
        'dynamic_args': 'files_and_dirs',
        'dangerous': False,
    },
    'mount': {
        'description': 'Mount filesystem',
        'arguments': [],
        'dynamic_args': None,
        'dangerous': True,
    },
    'umount': {
        'description': 'Unmount filesystem',
        'arguments': [],
        'dynamic_args': None,
        'dangerous': True,
    },
    'dmesg': {
        'description': 'Kernel messages',
        'arguments': [
            {'arg': '| tail -50', 'desc': 'Last 50 lines'},
            {'arg': '-T', 'desc': 'Human timestamps'},
        ],
        'dynamic_args': None,
        'dangerous': False,
    },
    'lsblk': {
        'description': 'List block devices',
        'arguments': [
            {'arg': '-f', 'desc': 'Show filesystems'},
        ],
        'dynamic_args': None,
        'dangerous': False,
    },
    'lsusb': {
        'description': 'List USB devices',
        'arguments': [],
        'dynamic_args': None,
        'dangerous': False,
    },
    'lspci': {
        'description': 'List PCI devices',
        'arguments': [],
        'dynamic_args': None,
        'dangerous': False,
    },
    # APT Package Manager
    'apt': {
        'description': 'Package manager',
        'arguments': [
            {'arg': 'update', 'desc': 'Update package lists'},
            {'arg': 'upgrade', 'desc': 'Upgrade all packages', 'dangerous': True},
            {'arg': 'install', 'desc': 'Install package', 'has_submenu': True, 'submenu_type': 'packages'},
            {'arg': 'remove', 'desc': 'Remove package', 'dangerous': True, 'has_submenu': True, 'submenu_type': 'installed_packages'},
            {'arg': 'search', 'desc': 'Search packages', 'needs_input': True, 'input_type': 'text', 'input_prompt': 'Enter search term'},
            {'arg': 'list --installed', 'desc': 'List installed packages'},
            {'arg': 'autoremove', 'desc': 'Remove unused packages', 'dangerous': True},
            {'arg': 'clean', 'desc': 'Clear package cache'},
        ],
        'dynamic_args': None,
        'dangerous': False,
    },
    # SSH Command
    'ssh': {
        'description': 'Secure shell connection',
        'arguments': [
            {'arg': '-p', 'desc': 'Port number', 'needs_input': True, 'input_type': 'port', 'input_prompt': 'Enter port number (1-65535)'},
            {'arg': '-i', 'desc': 'Identity file', 'has_submenu': True, 'submenu_type': 'ssh_keys'},
            {'arg': '-L', 'desc': 'Local port forward', 'needs_input': True, 'input_type': 'text', 'input_prompt': 'Enter local:remote:port (e.g., 8080:localhost:80)'},
            {'arg': '-R', 'desc': 'Remote port forward', 'needs_input': True, 'input_type': 'text', 'input_prompt': 'Enter remote:local:port (e.g., 8080:localhost:80)'},
            {'arg': '-D', 'desc': 'Dynamic SOCKS proxy', 'needs_input': True, 'input_type': 'port', 'input_prompt': 'Enter SOCKS port'},
            {'arg': '-o', 'desc': 'SSH options', 'has_submenu': True, 'submenu_type': 'ssh_options'},
            {'arg': '-v', 'desc': 'Verbose mode'},
            {'arg': '-N', 'desc': 'No remote command'},
            {'arg': '-f', 'desc': 'Background mode'},
            {'arg': '-C', 'desc': 'Enable compression'},
        ],
        'dynamic_args': 'ssh_hosts',
        'needs_host_input': True,
        'dangerous': False,
    },
    # SCP Command
    'scp': {
        'description': 'Secure copy',
        'arguments': [
            {'arg': '-P', 'desc': 'Port number', 'needs_input': True, 'input_type': 'port', 'input_prompt': 'Enter port number'},
            {'arg': '-i', 'desc': 'Identity file', 'has_submenu': True, 'submenu_type': 'ssh_keys'},
            {'arg': '-r', 'desc': 'Recursive copy'},
            {'arg': '-v', 'desc': 'Verbose mode'},
            {'arg': '-C', 'desc': 'Enable compression'},
        ],
        'dynamic_args': 'files_and_dirs',
        'needs_host_input': True,
        'dangerous': False,
    },
}

# SSH Options for submenu
SSH_OPTIONS = [
    {'arg': 'StrictHostKeyChecking=no', 'desc': 'Skip host key check'},
    {'arg': 'UserKnownHostsFile=/dev/null', 'desc': 'Ignore known hosts'},
    {'arg': 'ServerAliveInterval=60', 'desc': 'Keep connection alive'},
    {'arg': 'ServerAliveCountMax=3', 'desc': 'Max alive retries'},
    {'arg': 'Compression=yes', 'desc': 'Enable compression'},
    {'arg': 'ForwardAgent=yes', 'desc': 'Forward SSH agent'},
    {'arg': 'ForwardX11=yes', 'desc': 'Forward X11'},
    {'arg': 'LogLevel=DEBUG', 'desc': 'Debug logging'},
    {'arg': 'ConnectTimeout=10', 'desc': '10 second timeout'},
    {'arg': 'CUSTOM', 'desc': 'Custom option...', 'needs_input': True, 'input_type': 'text', 'input_prompt': 'Enter SSH option (e.g., Option=value)'},
]

# Common packages for apt install
COMMON_PACKAGES = {
    'Development': [
        {'name': 'build-essential', 'desc': 'C/C++ compiler and tools'},
        {'name': 'git', 'desc': 'Version control system'},
        {'name': 'python3', 'desc': 'Python 3 interpreter'},
        {'name': 'python3-pip', 'desc': 'Python package manager'},
        {'name': 'python3-venv', 'desc': 'Python virtual environments'},
        {'name': 'nodejs', 'desc': 'JavaScript runtime'},
        {'name': 'npm', 'desc': 'Node package manager'},
        {'name': 'gcc', 'desc': 'GNU C compiler'},
        {'name': 'g++', 'desc': 'GNU C++ compiler'},
        {'name': 'make', 'desc': 'Build automation tool'},
        {'name': 'cmake', 'desc': 'Cross-platform build system'},
        {'name': 'golang', 'desc': 'Go programming language'},
        {'name': 'rustc', 'desc': 'Rust compiler'},
        {'name': 'cargo', 'desc': 'Rust package manager'},
    ],
    'Utilities': [
        {'name': 'htop', 'desc': 'Interactive process viewer'},
        {'name': 'tmux', 'desc': 'Terminal multiplexer'},
        {'name': 'screen', 'desc': 'Terminal multiplexer'},
        {'name': 'vim', 'desc': 'Text editor'},
        {'name': 'nano', 'desc': 'Simple text editor'},
        {'name': 'curl', 'desc': 'Data transfer tool'},
        {'name': 'wget', 'desc': 'File downloader'},
        {'name': 'net-tools', 'desc': 'Network utilities'},
        {'name': 'tree', 'desc': 'Directory tree viewer'},
        {'name': 'jq', 'desc': 'JSON processor'},
        {'name': 'ripgrep', 'desc': 'Fast grep alternative'},
        {'name': 'fd-find', 'desc': 'Fast find alternative'},
        {'name': 'bat', 'desc': 'Cat with syntax highlighting'},
        {'name': 'ncdu', 'desc': 'Disk usage analyzer'},
        {'name': 'ranger', 'desc': 'File manager'},
        {'name': 'mc', 'desc': 'Midnight Commander'},
    ],
    'System': [
        {'name': 'openssh-server', 'desc': 'SSH server'},
        {'name': 'openssh-client', 'desc': 'SSH client'},
        {'name': 'ufw', 'desc': 'Firewall manager'},
        {'name': 'fail2ban', 'desc': 'Intrusion prevention'},
        {'name': 'cron', 'desc': 'Task scheduler'},
        {'name': 'rsync', 'desc': 'File synchronization'},
        {'name': 'unzip', 'desc': 'ZIP extractor'},
        {'name': 'p7zip-full', 'desc': '7-Zip archiver'},
        {'name': 'gzip', 'desc': 'Gzip compression'},
        {'name': 'bzip2', 'desc': 'Bzip2 compression'},
        {'name': 'xz-utils', 'desc': 'XZ compression'},
    ],
    'Media': [
        {'name': 'ffmpeg', 'desc': 'Media converter'},
        {'name': 'imagemagick', 'desc': 'Image manipulation'},
        {'name': 'vlc', 'desc': 'Media player'},
        {'name': 'mpv', 'desc': 'Media player'},
        {'name': 'youtube-dl', 'desc': 'Video downloader'},
        {'name': 'yt-dlp', 'desc': 'Video downloader (fork)'},
    ],
    'Network': [
        {'name': 'nmap', 'desc': 'Network scanner'},
        {'name': 'netcat', 'desc': 'Network utility'},
        {'name': 'tcpdump', 'desc': 'Packet analyzer'},
        {'name': 'iftop', 'desc': 'Network monitor'},
        {'name': 'mtr', 'desc': 'Network diagnostic'},
        {'name': 'dnsutils', 'desc': 'DNS utilities'},
        {'name': 'whois', 'desc': 'WHOIS client'},
        {'name': 'traceroute', 'desc': 'Route tracer'},
    ],
}

# File extensions to show for different file types
FILE_EXTENSIONS = {
    'text': ['.txt', '.md', '.log', '.conf', '.cfg', '.ini', '.json', '.xml', '.yaml', '.yml'],
    'code': ['.py', '.sh', '.bash', '.c', '.cpp', '.h', '.java', '.js', '.html', '.css'],
    'all': None,  # Show all files
}

# Directories to exclude from listings
EXCLUDED_DIRS = [
    '.git',
    '__pycache__',
    'node_modules',
    '.cache',
]

# Virtual Keyboard Settings
KEYBOARD_SETTINGS = {
    'key_width': 70,
    'key_height': 55,
    'key_spacing': 4,
    'max_input_length': 256,
}

# Live Command Settings
LIVE_COMMANDS = ['htop', 'top', 'tail -f', 'watch', 'ping', 'iotop', 'iftop']
LIVE_UPDATE_INTERVAL = 500  # milliseconds
LIVE_MAX_LINES = 1000

# History Settings
MAX_SSH_HOSTS = 10
MAX_RECENT_URLS = 10
