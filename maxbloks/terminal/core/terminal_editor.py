# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Terminal Editor for Handheld Gaming Devices
A minimal terminal command launcher with gamepad/D-pad controls

Designed for devices like Anbernic or R46H with 1024x768 resolution

Enhanced with:
- Virtual keyboard for text input
- SSH, APT, and enhanced curl commands
- Multi-argument command support
- Live output updates
"""

import pygame
import sys
from typing import List, Dict, Optional, Any
from enum import Enum, auto
import logging

# Import local modules
from maxbloks.terminal.config import config
from maxbloks.terminal.config.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLORS, COMMANDS,
    HEADER_HEIGHT, FOOTER_HEIGHT, OUTPUT_PANEL_HEIGHT,
    BUTTON_MAP, DPAD_AXIS_X, DPAD_AXIS_Y, KEY_MAP,
    SSH_OPTIONS, COMMON_PACKAGES
)
from maxbloks.terminal.ui import (
    FontManager, ScrollableList, OutputDisplay, 
    CommandBuilder, ConfirmDialog, ButtonHints
)
from maxbloks.terminal.core.command_executor import CommandExecutor
from maxbloks.terminal.ui.virtual_keyboard import VirtualKeyboard, InputType
from maxbloks.terminal.core.compat_sdl import init_display


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AppState(Enum):
    """Application states"""
    COMMAND_SELECT = auto()      # Selecting a command
    ARGUMENT_SELECT = auto()     # Selecting arguments
    SUBMENU_SELECT = auto()      # Selecting from a submenu (SSH options, packages, etc.)
    KEYBOARD_INPUT = auto()      # Virtual keyboard input
    OUTPUT_VIEW = auto()         # Viewing output (expanded)
    CONFIRM_DIALOG = auto()      # Showing confirmation dialog
    RUNNING = auto()             # Command is running
    LIVE_OUTPUT = auto()         # Live output mode
    CHIP_EDIT = auto()           # Editing command chips


class TerminalEditor:
    """
    Main application class for the terminal editor
    """
    
    def __init__(self):
        logger.info("TerminalEditor")
        
        """Initialize the terminal editor"""
        pygame.joystick.init()
        
        # Set up display using compat_sdl for better handheld device compatibility
        screen, display_info = init_display(
            size=(SCREEN_WIDTH, SCREEN_HEIGHT),
            fullscreen=True, # TODO: Consider full-screen?
            vsync=True
        )
        logger.info(f"screen: {str(screen)}")
        logger.info(f"display_info: {str(display_info)}")
        
        self.screen = screen
        config.SCREEN_WIDTH = screen.width
        config.SCREEN_HEIGHT = screen.height
        pygame.display.set_caption("Terminal Editor")
        
        # Initialize clock
        self.clock = pygame.time.Clock()
        
        # Initialize joystick if available
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Joystick detected: {self.joystick.get_name()}")
        else:
            print("No joystick detected, using keyboard controls")
        
        # Initialize components
        self.font_manager = FontManager.get_instance()
        self.executor = CommandExecutor()
        
        # Calculate layout
        list_width = SCREEN_WIDTH - 40
        list_height = SCREEN_HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT - OUTPUT_PANEL_HEIGHT - 30
        
        # Create UI components
        self.command_builder = CommandBuilder(
            20, 10, SCREEN_WIDTH - 40, HEADER_HEIGHT
        )
        
        self.item_list = ScrollableList(
            20, HEADER_HEIGHT + 20, list_width, list_height
        )
        
        self.output_display = OutputDisplay(
            20, SCREEN_HEIGHT - FOOTER_HEIGHT - OUTPUT_PANEL_HEIGHT - 10,
            list_width, OUTPUT_PANEL_HEIGHT
        )
        
        self.button_hints = ButtonHints(
            0, SCREEN_HEIGHT - FOOTER_HEIGHT, SCREEN_WIDTH, FOOTER_HEIGHT
        )
        
        self.confirm_dialog = ConfirmDialog(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Virtual keyboard
        self.virtual_keyboard = VirtualKeyboard(
            SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, self.font_manager
        )
        
        # Application state
        self.state = AppState.COMMAND_SELECT
        self.previous_state = AppState.COMMAND_SELECT
        self.running = True
        self.current_command: Optional[str] = None
        
        # Submenu state
        self.submenu_type: Optional[str] = None
        self.submenu_parent_arg: Optional[str] = None
        
        # Keyboard input state
        self.pending_arg: Optional[Dict] = None
        self.keyboard_callback: Optional[callable] = None
        
        # D-pad state tracking (for axis-based D-pad)
        self.dpad_state = {'up': False, 'down': False, 'left': False, 'right': False}
        self.dpad_repeat_timer = 0
        self.dpad_repeat_delay = 200  # ms before repeat starts
        self.dpad_repeat_rate = 80    # ms between repeats
        
        # Initialize UI
        self._setup_command_list()
        self._update_hints()
        self._update_cwd()
    
    def _setup_command_list(self):
        """Set up the command list"""
        items = []
        for cmd, info in sorted(COMMANDS.items()):
            item = {
                'text': cmd,
                'desc': info['description'],
                'type': 'command',
                'dangerous': info.get('dangerous', False)
            }
            items.append(item)
        self.item_list.set_items(items)
    
    def _setup_argument_list(self, command: str):
        """
        Set up the argument list for a command
        
        Args:
            command: The selected command
        """
        if command not in COMMANDS:
            return
        
        cmd_info = COMMANDS[command]
        items = []
        
        # Add static arguments
        for arg_info in cmd_info.get('arguments', []):
            item = {
                'text': arg_info['arg'],
                'desc': arg_info.get('desc', ''),
                'type': 'argument',
                'arg_info': arg_info  # Store full arg info for later use
            }
            
            # Mark if needs input or has submenu
            if arg_info.get('needs_input'):
                item['desc'] = f"{item['desc']} [input]" if item['desc'] else "[input]"
            if arg_info.get('has_submenu'):
                item['desc'] = f"{item['desc']} ▶" if item['desc'] else "▶"
            if arg_info.get('dangerous'):
                item['type'] = 'dangerous_arg'
            
            items.append(item)
        
        # Add dynamic arguments based on type
        dynamic_type = cmd_info.get('dynamic_args')
        self._add_dynamic_args(items, dynamic_type)
        
        # Add host input option for SSH-like commands
        if cmd_info.get('needs_host_input'):
            items.insert(0, {
                'text': '[Enter Host]',
                'desc': 'Type user@hostname',
                'type': 'action',
                'action': 'host_input'
            })
        
        # Add URL input option for curl-like commands
        if cmd_info.get('needs_url_input'):
            items.insert(0, {
                'text': '[Enter URL]',
                'desc': 'Type URL',
                'type': 'action',
                'action': 'url_input'
            })
        
        # Add option to execute without more arguments
        items.insert(0, {
            'text': '[Execute Now]',
            'desc': 'Run command as-is',
            'type': 'action',
            'action': 'execute'
        })
        
        # Add option to go back
        items.insert(0, {
            'text': '[Back]',
            'desc': 'Return to commands',
            'type': 'action',
            'action': 'back'
        })
        
        self.item_list.set_items(items)
    
    def _add_dynamic_args(self, items: List[Dict], dynamic_type: Optional[str]):
        """Add dynamic arguments to the items list"""
        if dynamic_type == 'directories':
            # Add recent directories first
            for dir_path in self.executor.get_recent_directories()[:5]:
                items.append({
                    'text': dir_path,
                    'desc': 'Recent',
                    'type': 'dir'
                })
            # Add current directory contents
            for dir_name in self.executor.get_directories():
                items.append({
                    'text': dir_name,
                    'desc': '',
                    'type': 'dir'
                })
        
        elif dynamic_type == 'files':
            for file_name in self.executor.get_files():
                items.append({
                    'text': file_name,
                    'desc': '',
                    'type': 'file'
                })
        
        elif dynamic_type == 'files_and_dirs':
            for entry in self.executor.get_files_and_dirs():
                items.append({
                    'text': entry['name'],
                    'desc': '',
                    'type': entry['type']
                })
        
        elif dynamic_type == 'processes':
            for proc in self.executor.get_processes():
                items.append({
                    'text': proc['pid'],
                    'desc': f"{proc['command']} (CPU:{proc['cpu']}% MEM:{proc['mem']}%)",
                    'type': 'process'
                })
        
        elif dynamic_type == 'process_names':
            for name in self.executor.get_process_names():
                items.append({
                    'text': name,
                    'desc': '',
                    'type': 'process'
                })
        
        elif dynamic_type == 'ssh_hosts':
            for host_info in self.executor.get_ssh_hosts():
                items.append({
                    'text': host_info['host'],
                    'desc': host_info.get('desc', ''),
                    'type': 'ssh_host'
                })
        
        elif dynamic_type == 'recent_urls':
            for url in self.executor.get_recent_urls():
                items.append({
                    'text': url,
                    'desc': 'Recent',
                    'type': 'url'
                })
    
    def _setup_submenu(self, submenu_type: str, parent_arg: str = None):
        """
        Set up a submenu for nested options
        
        Args:
            submenu_type: Type of submenu (ssh_options, ssh_keys, packages, installed_packages)
            parent_arg: The parent argument that triggered this submenu
        """
        self.submenu_type = submenu_type
        self.submenu_parent_arg = parent_arg
        items = []
        
        # Add back option
        items.append({
            'text': '[Back]',
            'desc': 'Return to arguments',
            'type': 'action',
            'action': 'back'
        })
        
        if submenu_type == 'ssh_options':
            for opt in SSH_OPTIONS:
                item = {
                    'text': opt['arg'],
                    'desc': opt['desc'],
                    'type': 'ssh_option',
                    'opt_info': opt
                }
                if opt.get('needs_input'):
                    item['desc'] = f"{item['desc']} [input]"
                items.append(item)
        
        elif submenu_type == 'ssh_keys':
            for key_info in self.executor.get_ssh_keys():
                items.append({
                    'text': key_info['path'],
                    'desc': key_info['name'],
                    'type': 'ssh_key'
                })
        
        elif submenu_type == 'packages':
            # Add search option
            items.append({
                'text': '[Search Packages]',
                'desc': 'Search apt packages',
                'type': 'action',
                'action': 'search_packages'
            })
            
            # Add common packages by category
            for category, packages in COMMON_PACKAGES.items():
                items.append({
                    'text': f'── {category} ──',
                    'desc': '',
                    'type': 'category_header'
                })
                for pkg in packages:
                    items.append({
                        'text': pkg['name'],
                        'desc': pkg['desc'],
                        'type': 'package'
                    })
        
        elif submenu_type == 'installed_packages':
            for pkg in self.executor.get_installed_packages():
                items.append({
                    'text': pkg['name'],
                    'desc': pkg['desc'],
                    'type': 'package'
                })
        
        elif submenu_type == 'search_results':
            # This is populated after a search
            pass
        
        self.item_list.set_items(items)
        self.state = AppState.SUBMENU_SELECT
        self._update_hints()
    
    def _show_keyboard(self, prompt: str, callback: callable, 
                       input_type: str = 'text', initial_text: str = ''):
        """
        Show the virtual keyboard
        
        Args:
            prompt: Prompt text to display
            callback: Function to call with the result
            input_type: Type of input validation
            initial_text: Pre-filled text
        """
        self.previous_state = self.state
        self.state = AppState.KEYBOARD_INPUT
        self.keyboard_callback = callback
        
        # Map input type string to InputType enum
        type_map = {
            'text': InputType.TEXT,
            'numeric': InputType.NUMERIC,
            'port': InputType.PORT,
            'url': InputType.URL,
            'ssh_host': InputType.SSH_HOST,
            'filename': InputType.FILENAME,
        }
        kb_input_type = type_map.get(input_type, InputType.TEXT)
        
        self.virtual_keyboard.show(
            prompt=prompt,
            callback=self._keyboard_result,
            initial_text=initial_text,
            input_type=kb_input_type
        )
        self._update_hints()
    
    def _keyboard_result(self, result: Optional[str]):
        """
        Handle virtual keyboard result
        
        Args:
            result: The entered text or None if cancelled
        """
        self.state = self.previous_state
        
        if result is not None and self.keyboard_callback:
            self.keyboard_callback(result)
        
        self.keyboard_callback = None
        self._update_hints()
    
    def _update_hints(self):
        """Update button hints based on current state"""
        if self.state == AppState.COMMAND_SELECT:
            self.button_hints.set_hints([
                ("↑↓", "Navigate"),
                ("←→", "Page"),
                ("A", "Select"),
                ("X", "Execute"),
                ("SELECT", "Output"),
                ("START", "Exit"),
            ])
        elif self.state == AppState.ARGUMENT_SELECT:
            hints = [
                ("↑↓", "Navigate"),
                ("←→", "Page"),
                ("A", "Add"),
                ("B", "Back"),
                ("X", "Execute"),
                ("Y", "Clear"),
            ]
            if self.command_builder.get_parts_count() > 1:
                hints.append(("L", "Edit"))
            self.button_hints.set_hints(hints)
        elif self.state == AppState.SUBMENU_SELECT:
            self.button_hints.set_hints([
                ("↑↓", "Navigate"),
                ("A", "Select"),
                ("B", "Back"),
            ])
        elif self.state == AppState.KEYBOARD_INPUT:
            self.button_hints.set_hints([
                ("D-pad", "Move"),
                ("A", "Type"),
                ("B", "Delete"),
                ("X", "Confirm"),
                ("Y", "Mode"),
                ("START", "Cancel"),
            ])
        elif self.state == AppState.OUTPUT_VIEW:
            self.button_hints.set_hints([
                ("↑↓", "Scroll"),
                ("SELECT", "Close"),
                ("B", "Close"),
            ])
        elif self.state == AppState.CONFIRM_DIALOG:
            self.button_hints.set_hints([
                ("←→", "Select"),
                ("A", "Confirm"),
                ("B", "Cancel"),
            ])
        elif self.state == AppState.RUNNING:
            self.button_hints.set_hints([
                ("", "Running command..."),
                ("B", "Cancel"),
            ])
        elif self.state == AppState.LIVE_OUTPUT:
            self.button_hints.set_hints([
                ("↑↓", "Scroll"),
                ("B", "Stop"),
                ("SELECT", "Expand"),
            ])
        elif self.state == AppState.CHIP_EDIT:
            self.button_hints.set_hints([
                ("←→", "Select arg"),
                ("B", "Remove"),
                ("Y", "Exit edit"),
            ])
    
    def _update_cwd(self):
        """Update the current working directory display"""
        self.command_builder.set_cwd(self.executor.get_cwd())
    
    def _handle_command_select(self, selected: Dict):
        """
        Handle selection in command select state
        
        Args:
            selected: The selected item
        """
        cmd = selected['text']
        self.current_command = cmd
        self.command_builder.add_part(cmd)
        
        # Check if command has arguments
        if COMMANDS[cmd].get('arguments') or COMMANDS[cmd].get('dynamic_args'):
            self.state = AppState.ARGUMENT_SELECT
            self._setup_argument_list(cmd)
        else:
            # Execute immediately if no arguments
            self._try_execute()
        
        self._update_hints()
    
    def _handle_argument_select(self, selected: Dict):
        """
        Handle selection in argument select state
        
        Args:
            selected: The selected item
        """
        text = selected['text']
        action = selected.get('action')
        arg_info = selected.get('arg_info', {})
        
        if action == 'back':
            # Go back to command selection
            self.command_builder.clear()
            self.current_command = None
            self.state = AppState.COMMAND_SELECT
            self._setup_command_list()
        
        elif action == 'execute':
            # Execute the command
            self._try_execute()
        
        elif action == 'host_input':
            # Show keyboard for host input
            self._show_keyboard(
                "Enter host (user@hostname):",
                lambda result: self._add_host_arg(result),
                input_type='ssh_host'
            )
        
        elif action == 'url_input':
            # Show keyboard for URL input
            self._show_keyboard(
                "Enter URL:",
                lambda result: self._add_url_arg(result),
                input_type='url'
            )
        
        elif arg_info.get('has_submenu'):
            # Open submenu
            submenu_type = arg_info.get('submenu_type')
            self._setup_submenu(submenu_type, text)
        
        elif arg_info.get('needs_input'):
            # Show keyboard for argument input
            input_type = arg_info.get('input_type', 'text')
            prompt = arg_info.get('input_prompt', f"Enter value for {text}:")
            self.pending_arg = text
            self._show_keyboard(
                prompt,
                lambda result: self._add_arg_with_value(self.pending_arg, result),
                input_type=input_type
            )
        
        elif selected['type'] == 'category_header':
            # Ignore category headers
            pass
        
        else:
            # Add argument to command
            self.command_builder.add_part(text)
            # Refresh argument list (for chaining arguments)
            self._setup_argument_list(self.current_command)
        
        self._update_hints()
    
    def _handle_submenu_select(self, selected: Dict):
        """
        Handle selection in submenu state
        
        Args:
            selected: The selected item
        """
        text = selected['text']
        action = selected.get('action')
        opt_info = selected.get('opt_info', {})
        
        if action == 'back':
            # Return to argument selection
            self.state = AppState.ARGUMENT_SELECT
            self._setup_argument_list(self.current_command)
        
        elif action == 'search_packages':
            # Show keyboard for package search
            self._show_keyboard(
                "Search packages:",
                lambda result: self._search_packages(result),
                input_type='text'
            )
        
        elif selected['type'] == 'category_header':
            # Ignore category headers
            pass
        
        elif selected['type'] == 'ssh_option':
            if opt_info.get('needs_input'):
                # Custom option - show keyboard
                self._show_keyboard(
                    "Enter SSH option (Option=value):",
                    lambda result: self._add_ssh_option(result),
                    input_type='text'
                )
            else:
                # Add the option
                self._add_ssh_option(text)
        
        elif selected['type'] == 'ssh_key':
            # Add identity file argument
            self.command_builder.add_part(f"-i {text}")
            self.state = AppState.ARGUMENT_SELECT
            self._setup_argument_list(self.current_command)
        
        elif selected['type'] == 'package':
            # Add package to command
            self.command_builder.add_part(text)
            self.state = AppState.ARGUMENT_SELECT
            self._setup_argument_list(self.current_command)
        
        self._update_hints()
    
    def _add_arg_with_value(self, arg: str, value: str):
        """Add an argument with its value to the command"""
        if value:
            if arg.endswith('='):
                self.command_builder.add_part(f"{arg}{value}")
            else:
                self.command_builder.add_part(f"{arg} {value}")
        self.pending_arg = None
        self._setup_argument_list(self.current_command)
    
    def _add_host_arg(self, host: str):
        """Add a host argument"""
        if host:
            self.command_builder.add_part(host)
            self.executor.add_ssh_host(host)
        self._setup_argument_list(self.current_command)
    
    def _add_url_arg(self, url: str):
        """Add a URL argument"""
        if url:
            # Add protocol if missing
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url
            self.command_builder.add_part(url)
            self.executor.add_recent_url(url)
        self._setup_argument_list(self.current_command)
    
    def _add_ssh_option(self, option: str):
        """Add an SSH option"""
        if option and option != 'CUSTOM':
            self.command_builder.add_part(f"-o {option}")
        self.state = AppState.ARGUMENT_SELECT
        self._setup_argument_list(self.current_command)
    
    def _search_packages(self, query: str):
        """Search for packages and display results"""
        if not query:
            self._setup_submenu('packages', 'install')
            return
        
        results = self.executor.search_packages(query)
        items = [{
            'text': '[Back]',
            'desc': 'Return to packages',
            'type': 'action',
            'action': 'back'
        }]
        
        if results:
            for pkg in results:
                items.append({
                    'text': pkg['name'],
                    'desc': pkg['desc'],
                    'type': 'package'
                })
        else:
            items.append({
                'text': f'No results for "{query}"',
                'desc': '',
                'type': 'info'
            })
        
        self.item_list.set_items(items)
        self.state = AppState.SUBMENU_SELECT
        self._update_hints()
    
    def _try_execute(self):
        """Try to execute the current command"""
        command = self.command_builder.get_command()
        
        if not command:
            return
        
        # Check if command is dangerous
        if self.executor.is_dangerous(command):
            warning = self.executor.get_danger_level(command)
            self.state = AppState.CONFIRM_DIALOG
            self.confirm_dialog.show(command, warning, self._execute_callback)
            self._update_hints()
        else:
            self._execute_command(command)
    
    def _execute_callback(self, confirmed: bool):
        """
        Callback for confirmation dialog
        
        Args:
            confirmed: Whether the user confirmed
        """
        if confirmed:
            command = self.command_builder.get_command()
            self._execute_command(command)
        else:
            # Return to argument selection or command selection
            if self.current_command:
                self.state = AppState.ARGUMENT_SELECT
            else:
                self.state = AppState.COMMAND_SELECT
        self._update_hints()
    
    def _execute_command(self, command: str):
        """
        Execute a command
        
        Args:
            command: The command to execute
        """
        # Check if this is a live command
        if self.executor.is_live_command(command):
            self._execute_live_command(command)
            return
        
        self.state = AppState.RUNNING
        self.command_builder.set_status("Running...", "running")
        self._update_hints()
        
        # Force a screen update before execution
        self._draw()
        pygame.display.flip()
        
        # Execute the command
        stdout, stderr, return_code = self.executor.execute(command)
        
        # Update output display
        self.output_display.set_output(stdout, stderr, return_code)
        
        # Update status
        if return_code == 0:
            self.command_builder.set_status("Success", "success")
        else:
            self.command_builder.set_status(f"Failed (code {return_code})", "error")
        
        # Update CWD (in case cd was executed)
        self._update_cwd()
        
        # Clear command and return to command selection
        self.command_builder.clear()
        self.current_command = None
        self.state = AppState.COMMAND_SELECT
        self._setup_command_list()
        self._update_hints()
    
    def _execute_live_command(self, command: str):
        """
        Execute a command in live mode
        
        Args:
            command: The command to execute
        """
        self.state = AppState.LIVE_OUTPUT
        self.command_builder.set_status("LIVE", "live")
        self.output_display.start_live_mode()
        self._update_hints()
        
        # Start live execution
        self.executor.execute_live(command, self._live_output_callback)
    
    def _live_output_callback(self, lines: List[str], is_complete: bool):
        """
        Callback for live output updates
        
        Args:
            lines: Current output lines
            is_complete: Whether the command has completed
        """
        self.output_display.set_live_output(lines, is_complete)
        
        if is_complete:
            self.command_builder.set_status("Complete", "success")
            self.command_builder.clear()
            self.current_command = None
            self.state = AppState.COMMAND_SELECT
            self._setup_command_list()
            self._update_hints()
    
    def _stop_live_command(self):
        """Stop the currently running live command"""
        self.executor.cancel_live()
        self.output_display.stop_live_mode()
        self.command_builder.set_status("Stopped", "warning")
        self.command_builder.clear()
        self.current_command = None
        self.state = AppState.COMMAND_SELECT
        self._setup_command_list()
        self._update_hints()
    
    def _handle_input(self, action: str):
        """
        Handle an input action
        
        Args:
            action: The action name (UP, DOWN, LEFT, RIGHT, A, B, X, Y, START, SELECT, L, R)
        """
        # Handle virtual keyboard input
        if self.state == AppState.KEYBOARD_INPUT:
            if self.virtual_keyboard.handle_input(action):
                return  # Keyboard handled the input
            else:
                # Keyboard closed
                self._update_hints()
                return
        
        # Handle confirmation dialog
        if self.state == AppState.CONFIRM_DIALOG:
            if action == 'LEFT' or action == 'RIGHT':
                self.confirm_dialog.move_selection(1 if action == 'RIGHT' else -1)
            elif action == 'A':
                self.confirm_dialog.confirm()
            elif action == 'B':
                self.confirm_dialog.cancel()
                if self.current_command:
                    self.state = AppState.ARGUMENT_SELECT
                else:
                    self.state = AppState.COMMAND_SELECT
                self._update_hints()
            return
        
        # Handle running state
        if self.state == AppState.RUNNING:
            if action == 'B':
                self.executor.cancel()
            return
        
        # Handle live output state
        if self.state == AppState.LIVE_OUTPUT:
            if action == 'UP':
                self.output_display.scroll(-1)
            elif action == 'DOWN':
                self.output_display.scroll(1)
            elif action == 'B':
                self._stop_live_command()
            elif action == 'SELECT':
                self.output_display.toggle_expanded()
            return
        
        # Handle output view state
        if self.state == AppState.OUTPUT_VIEW:
            if action == 'UP':
                self.output_display.scroll(-1)
            elif action == 'DOWN':
                self.output_display.scroll(1)
            elif action == 'SELECT' or action == 'B':
                self.output_display.toggle_expanded()
                if self.current_command:
                    self.state = AppState.ARGUMENT_SELECT
                else:
                    self.state = AppState.COMMAND_SELECT
                self._update_hints()
            return
        
        # Handle chip edit mode
        if self.state == AppState.CHIP_EDIT:
            if action == 'LEFT':
                self.command_builder.move_chip_selection(-1)
            elif action == 'RIGHT':
                self.command_builder.move_chip_selection(1)
            elif action == 'B':
                if self.command_builder.remove_selected_chip():
                    if self.command_builder.get_parts_count() <= 1:
                        self.command_builder.exit_chip_mode()
                        self.state = AppState.ARGUMENT_SELECT
                        self._setup_argument_list(self.current_command)
            elif action == 'Y':
                self.command_builder.exit_chip_mode()
                self.state = AppState.ARGUMENT_SELECT
                self._setup_argument_list(self.current_command)
            self._update_hints()
            return
        
        # Handle submenu state
        if self.state == AppState.SUBMENU_SELECT:
            if action == 'UP':
                self.item_list.move_selection(-1)
            elif action == 'DOWN':
                self.item_list.move_selection(1)
            elif action == 'LEFT':
                self.item_list.page_scroll(-1)
            elif action == 'RIGHT':
                self.item_list.page_scroll(1)
            elif action == 'A':
                selected = self.item_list.get_selected()
                if selected:
                    self._handle_submenu_select(selected)
            elif action == 'B':
                self.state = AppState.ARGUMENT_SELECT
                self._setup_argument_list(self.current_command)
                self._update_hints()
            return
        
        # Normal list navigation states (COMMAND_SELECT, ARGUMENT_SELECT)
        if action == 'UP':
            self.item_list.move_selection(-1)
        elif action == 'DOWN':
            self.item_list.move_selection(1)
        elif action == 'LEFT':
            self.item_list.page_scroll(-1)
        elif action == 'RIGHT':
            self.item_list.page_scroll(1)
        elif action == 'A':
            selected = self.item_list.get_selected()
            if selected:
                if self.state == AppState.COMMAND_SELECT:
                    self._handle_command_select(selected)
                elif self.state == AppState.ARGUMENT_SELECT:
                    self._handle_argument_select(selected)
        elif action == 'B':
            if self.state == AppState.ARGUMENT_SELECT:
                # Remove last argument or go back to command selection
                if self.command_builder.get_parts_count() > 1:
                    self.command_builder.remove_last()
                    self._setup_argument_list(self.current_command)
                else:
                    self.command_builder.clear()
                    self.current_command = None
                    self.state = AppState.COMMAND_SELECT
                    self._setup_command_list()
                    self._update_hints()
        elif action == 'X':
            # Execute current command
            if self.command_builder.command_parts:
                self._try_execute()
        elif action == 'Y':
            # Clear command
            self.command_builder.clear()
            self.current_command = None
            self.state = AppState.COMMAND_SELECT
            self._setup_command_list()
            self._update_hints()
        elif action == 'L':
            # Enter chip edit mode (only in argument select with multiple parts)
            if self.state == AppState.ARGUMENT_SELECT and self.command_builder.get_parts_count() > 1:
                self.command_builder.enter_chip_mode()
                self.state = AppState.CHIP_EDIT
                self._update_hints()
        elif action == 'SELECT':
            # Toggle output view
            self.output_display.toggle_expanded()
            if self.output_display.expanded:
                self.state = AppState.OUTPUT_VIEW
            self._update_hints()
        elif action == 'START':
            # Exit application
            self.running = False
    
    def _process_events(self):
        """Process pygame events"""
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Keyboard events (for testing on PC)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self._handle_input('UP')
                elif event.key == pygame.K_DOWN:
                    self._handle_input('DOWN')
                elif event.key == pygame.K_LEFT:
                    self._handle_input('LEFT')
                elif event.key == pygame.K_RIGHT:
                    self._handle_input('RIGHT')
                elif event.key == pygame.K_RETURN:
                    self._handle_input('A')
                elif event.key == pygame.K_ESCAPE:
                    self._handle_input('B')
                elif event.key == pygame.K_x:
                    self._handle_input('X')
                elif event.key == pygame.K_y:
                    self._handle_input('Y')
                elif event.key == pygame.K_TAB:
                    self._handle_input('SELECT')
                elif event.key == pygame.K_q:
                    self._handle_input('START')
                elif event.key == pygame.K_l:
                    self._handle_input('L')
                elif event.key == pygame.K_r:
                    self._handle_input('R')
            
            # Joystick button events
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == BUTTON_MAP.get('A', 0):
                    self._handle_input('A')
                elif event.button == BUTTON_MAP.get('B', 1):
                    self._handle_input('B')
                elif event.button == BUTTON_MAP.get('X', 2):
                    self._handle_input('X')
                elif event.button == BUTTON_MAP.get('Y', 3):
                    self._handle_input('Y')
                elif event.button == BUTTON_MAP.get('START', 7):
                    self._handle_input('START')
                elif event.button == BUTTON_MAP.get('SELECT', 6):
                    self._handle_input('SELECT')
                elif event.button == BUTTON_MAP.get('L', 4):
                    self._handle_input('L')
                elif event.button == BUTTON_MAP.get('R', 5):
                    self._handle_input('R')
            
            # Joystick hat (D-pad) events
            elif event.type == pygame.JOYHATMOTION:
                x, y = event.value
                if y == 1:
                    self._handle_input('UP')
                elif y == -1:
                    self._handle_input('DOWN')
                if x == -1:
                    self._handle_input('LEFT')
                elif x == 1:
                    self._handle_input('RIGHT')
            
            # Joystick axis events (for analog D-pad)
            elif event.type == pygame.JOYAXISMOTION:
                if event.axis == DPAD_AXIS_Y:
                    if event.value < -0.5:
                        if not self.dpad_state['up']:
                            self.dpad_state['up'] = True
                            self.dpad_repeat_timer = current_time
                            self._handle_input('UP')
                    elif event.value > 0.5:
                        if not self.dpad_state['down']:
                            self.dpad_state['down'] = True
                            self.dpad_repeat_timer = current_time
                            self._handle_input('DOWN')
                    else:
                        self.dpad_state['up'] = False
                        self.dpad_state['down'] = False
                
                elif event.axis == DPAD_AXIS_X:
                    if event.value < -0.5:
                        if not self.dpad_state['left']:
                            self.dpad_state['left'] = True
                            self.dpad_repeat_timer = current_time
                            self._handle_input('LEFT')
                    elif event.value > 0.5:
                        if not self.dpad_state['right']:
                            self.dpad_state['right'] = True
                            self.dpad_repeat_timer = current_time
                            self._handle_input('RIGHT')
                    else:
                        self.dpad_state['left'] = False
                        self.dpad_state['right'] = False
        
        # Handle D-pad repeat for held directions
        if any(self.dpad_state.values()):
            elapsed = current_time - self.dpad_repeat_timer
            if elapsed > self.dpad_repeat_delay:
                repeat_elapsed = (elapsed - self.dpad_repeat_delay) % self.dpad_repeat_rate
                if repeat_elapsed < self.clock.get_time():
                    if self.dpad_state['up']:
                        self._handle_input('UP')
                    elif self.dpad_state['down']:
                        self._handle_input('DOWN')
                    elif self.dpad_state['left']:
                        self._handle_input('LEFT')
                    elif self.dpad_state['right']:
                        self._handle_input('RIGHT')
    
    def _draw(self):
        """Draw the application"""
        # Clear screen
        self.screen.fill(COLORS['background'])
        
        # Draw components
        self.command_builder.draw(self.screen)
        
        # Draw list or expanded output
        if self.output_display.expanded or self.state == AppState.LIVE_OUTPUT:
            # Draw expanded output over the list area
            expanded_rect = pygame.Rect(
                20, HEADER_HEIGHT + 20,
                SCREEN_WIDTH - 40,
                SCREEN_HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT - 30
            )
            self.output_display.draw(self.screen, expanded_rect)
        else:
            self.item_list.draw(self.screen)
            self.output_display.draw(self.screen)
        
        self.button_hints.draw(self.screen)
        
        # Draw confirmation dialog if visible
        self.confirm_dialog.draw(self.screen)
        
        # Draw virtual keyboard if visible
        if self.state == AppState.KEYBOARD_INPUT:
            self.virtual_keyboard.draw(self.screen)
    
    def run(self):
        """Main application loop"""
        while self.running:
            # Process events
            self._process_events()
            
            # Update components
            self.item_list.update()
            if self.state == AppState.KEYBOARD_INPUT:
                self.virtual_keyboard.update()
            
            # Draw
            self._draw()
            
            # Update display
            pygame.display.flip()
            
            # Cap framerate
            self.clock.tick(FPS)
        
        # Cleanup
        self.executor.cancel_live()  # Stop any live commands
        pygame.quit()


def main():
    """Main entry point"""
    try:
        app = TerminalEditor()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
