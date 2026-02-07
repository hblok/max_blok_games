"""
Command Executor Module
Handles safe execution of shell commands with subprocess
"""

import subprocess
import os
import signal
import threading
from typing import Tuple, Optional, List, Dict, Callable

from maxbloks.terminal.config.config import DANGEROUS_COMMANDS


class CommandExecutor:
    """
    Safe command execution wrapper with timeout and output capture
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the command executor
        
        Args:
            timeout: Maximum execution time in seconds
        """
        self.timeout = timeout
        self.current_process: Optional[subprocess.Popen] = None
        self.cwd = os.path.expanduser('~')
        self.history: List[Dict] = []
        self.max_history = 10
        self.recent_dirs: List[str] = [self.cwd]
        self.max_recent_dirs = 10
        self.is_running = False
        self.last_output = ""
        self.last_error = ""
        self.last_return_code = 0
        
    def is_dangerous(self, command: str) -> bool:
        """
        Check if a command is potentially dangerous
        
        Args:
            command: The command to check
            
        Returns:
            True if the command is dangerous
        """
        cmd_parts = command.strip().split()
        if not cmd_parts:
            return False
            
        base_cmd = cmd_parts[0]
        
        # Check if base command is in dangerous list
        if base_cmd in DANGEROUS_COMMANDS:
            return True
            
        # Check for dangerous patterns
        dangerous_patterns = [
            'rm -rf /',
            'rm -rf ~',
            'rm -rf *',
            'dd if=',
            'mkfs',
            '> /dev/',
            'chmod 777 /',
            ':(){:|:&};:',  # Fork bomb
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command:
                return True
                
        return False
    
    def get_danger_level(self, command: str) -> str:
        """
        Get the danger level description for a command
        
        Args:
            command: The command to check
            
        Returns:
            Danger level description
        """
        cmd_lower = command.lower()
        
        if 'rm -rf /' in cmd_lower or 'rm -rf ~' in cmd_lower:
            return "EXTREME DANGER: This will delete critical system files!"
        elif 'reboot' in cmd_lower or 'poweroff' in cmd_lower or 'shutdown' in cmd_lower:
            return "WARNING: This will restart/shutdown the system!"
        elif 'kill' in cmd_lower:
            return "WARNING: This will terminate a running process!"
        elif 'rm' in cmd_lower:
            return "CAUTION: This will permanently delete files!"
        elif 'chmod' in cmd_lower or 'chown' in cmd_lower:
            return "CAUTION: This will change file permissions/ownership!"
        else:
            return "This command may make system changes."
    
    def execute(self, command: str) -> Tuple[str, str, int]:
        """
        Execute a command and return output
        
        Args:
            command: The command to execute
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        self.is_running = True
        self.last_output = ""
        self.last_error = ""
        
        # Handle special built-in commands
        if command.strip() == 'history':
            return self._show_history()
        
        # Handle cd command specially (needs to change cwd)
        if command.strip().startswith('cd '):
            return self._handle_cd(command)
        elif command.strip() == 'cd':
            return self._handle_cd('cd ~')
        
        try:
            # Expand user home directory
            expanded_command = os.path.expanduser(command)
            
            self.current_process = subprocess.Popen(
                expanded_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.cwd,
                preexec_fn=os.setsid,  # Create new process group
                env=os.environ.copy()
            )
            
            try:
                stdout, stderr = self.current_process.communicate(timeout=self.timeout)
                return_code = self.current_process.returncode
                
                self.last_output = stdout.decode('utf-8', errors='replace')
                self.last_error = stderr.decode('utf-8', errors='replace')
                self.last_return_code = return_code
                
                # Add to history
                self._add_to_history(command, return_code == 0)
                
                return self.last_output, self.last_error, return_code
                
            except subprocess.TimeoutExpired:
                # Kill the process group
                os.killpg(os.getpgid(self.current_process.pid), signal.SIGKILL)
                self.current_process.wait()
                self.last_error = f"Command timed out after {self.timeout} seconds"
                self.last_return_code = -1
                return "", self.last_error, -1
                
        except Exception as e:
            self.last_error = str(e)
            self.last_return_code = -1
            return "", str(e), -1
            
        finally:
            self.is_running = False
            self.current_process = None
    
    def _handle_cd(self, command: str) -> Tuple[str, str, int]:
        """
        Handle cd command by changing the working directory
        
        Args:
            command: The cd command
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        try:
            # Extract path from command
            parts = command.strip().split(maxsplit=1)
            if len(parts) > 1:
                path = parts[1].strip()
            else:
                path = '~'
            
            # Expand user and resolve path
            path = os.path.expanduser(path)
            if not os.path.isabs(path):
                path = os.path.join(self.cwd, path)
            path = os.path.normpath(path)
            
            # Check if path exists and is a directory
            if not os.path.exists(path):
                self.last_error = f"cd: {path}: No such file or directory"
                return "", self.last_error, 1
            
            if not os.path.isdir(path):
                self.last_error = f"cd: {path}: Not a directory"
                return "", self.last_error, 1
            
            # Change directory
            self.cwd = path
            self._add_recent_dir(path)
            self._add_to_history(command, True)
            
            self.last_output = f"Changed directory to: {path}"
            return self.last_output, "", 0
            
        except PermissionError:
            self.last_error = f"cd: {path}: Permission denied"
            return "", self.last_error, 1
        except Exception as e:
            self.last_error = f"cd: {str(e)}"
            return "", self.last_error, 1
        finally:
            self.is_running = False
    
    def _show_history(self) -> Tuple[str, str, int]:
        """
        Show command history
        
        Returns:
            Tuple of (history output, stderr, return_code)
        """
        self.is_running = False
        if not self.history:
            return "No commands in history", "", 0
        
        lines = []
        for i, entry in enumerate(self.history, 1):
            status = "✓" if entry['success'] else "✗"
            lines.append(f"{i:3d}  {status}  {entry['command']}")
        
        return "\n".join(lines), "", 0
    
    def _add_to_history(self, command: str, success: bool):
        """
        Add a command to history
        
        Args:
            command: The executed command
            success: Whether the command succeeded
        """
        self.history.append({
            'command': command,
            'success': success
        })
        
        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def _add_recent_dir(self, path: str):
        """
        Add a directory to recent directories list
        
        Args:
            path: The directory path
        """
        # Remove if already exists
        if path in self.recent_dirs:
            self.recent_dirs.remove(path)
        
        # Add to front
        self.recent_dirs.insert(0, path)
        
        # Trim if needed
        if len(self.recent_dirs) > self.max_recent_dirs:
            self.recent_dirs = self.recent_dirs[:self.max_recent_dirs]
    
    def cancel(self):
        """
        Cancel the currently running command
        """
        if self.current_process and self.is_running:
            try:
                os.killpg(os.getpgid(self.current_process.pid), signal.SIGKILL)
            except:
                pass
            self.is_running = False
    
    def get_cwd(self) -> str:
        """
        Get current working directory
        
        Returns:
            Current working directory path
        """
        return self.cwd
    
    def get_files(self, include_hidden: bool = False) -> List[str]:
        """
        Get list of files in current directory
        
        Args:
            include_hidden: Whether to include hidden files
            
        Returns:
            List of file names
        """
        try:
            entries = os.listdir(self.cwd)
            files = []
            for entry in sorted(entries):
                if not include_hidden and entry.startswith('.'):
                    continue
                path = os.path.join(self.cwd, entry)
                if os.path.isfile(path):
                    files.append(entry)
            return files
        except PermissionError:
            return []
    
    def get_directories(self, include_hidden: bool = False) -> List[str]:
        """
        Get list of directories in current directory
        
        Args:
            include_hidden: Whether to include hidden directories
            
        Returns:
            List of directory names
        """
        try:
            entries = os.listdir(self.cwd)
            dirs = ['..']  # Always include parent
            for entry in sorted(entries):
                if not include_hidden and entry.startswith('.'):
                    continue
                path = os.path.join(self.cwd, entry)
                if os.path.isdir(path):
                    dirs.append(entry)
            return dirs
        except PermissionError:
            return ['..']
    
    def get_files_and_dirs(self, include_hidden: bool = False) -> List[Dict]:
        """
        Get list of files and directories with type info
        
        Args:
            include_hidden: Whether to include hidden entries
            
        Returns:
            List of dicts with 'name' and 'type' keys
        """
        try:
            entries = os.listdir(self.cwd)
            result = [{'name': '..', 'type': 'dir'}]
            
            for entry in sorted(entries):
                if not include_hidden and entry.startswith('.'):
                    continue
                path = os.path.join(self.cwd, entry)
                entry_type = 'dir' if os.path.isdir(path) else 'file'
                result.append({'name': entry, 'type': entry_type})
            
            return result
        except PermissionError:
            return [{'name': '..', 'type': 'dir'}]
    
    def get_processes(self) -> List[Dict]:
        """
        Get list of running processes
        
        Returns:
            List of process info dicts
        """
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            processes = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines[:50]:  # Limit to 50 processes
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    processes.append({
                        'pid': parts[1],
                        'cpu': parts[2],
                        'mem': parts[3],
                        'command': parts[10][:40]  # Truncate command
                    })
            
            return processes
        except:
            return []
    
    def get_process_names(self) -> List[str]:
        """
        Get list of unique process names
        
        Returns:
            List of process names
        """
        try:
            result = subprocess.run(
                ['ps', '-e', '-o', 'comm='],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            names = set(result.stdout.strip().split('\n'))
            return sorted(list(names))[:50]  # Limit to 50
        except:
            return []
    
    def get_history_commands(self) -> List[str]:
        """
        Get list of commands from history
        
        Returns:
            List of command strings
        """
        return [entry['command'] for entry in self.history]
    
    def get_recent_directories(self) -> List[str]:
        """
        Get list of recently accessed directories
        
        Returns:
            List of directory paths
        """
        return self.recent_dirs.copy()
    
    # ==================== NEW METHODS FOR ENHANCED FEATURES ====================
    
    def __init_extended_history(self):
        """Initialize extended history tracking (called from __init__)"""
        if not hasattr(self, 'ssh_hosts'):
            self.ssh_hosts: List[str] = []
        if not hasattr(self, 'recent_urls'):
            self.recent_urls: List[str] = []
        if not hasattr(self, 'max_ssh_hosts'):
            self.max_ssh_hosts = 10
        if not hasattr(self, 'max_recent_urls'):
            self.max_recent_urls = 10
        if not hasattr(self, 'live_process'):
            self.live_process = None
        if not hasattr(self, 'live_output_lines'):
            self.live_output_lines: List[str] = []
        if not hasattr(self, 'live_callback'):
            self.live_callback = None
    
    def get_ssh_hosts(self) -> List[Dict]:
        """
        Get list of SSH hosts from config and history
        
        Returns:
            List of host info dicts with 'host', 'desc' keys
        """
        self.__init_extended_history()
        hosts = []
        
        # Add recent hosts first
        for host in self.ssh_hosts:
            hosts.append({
                'host': host,
                'desc': 'Recent',
                'type': 'recent'
            })
        
        # Parse ~/.ssh/config
        ssh_config_path = os.path.expanduser('~/.ssh/config')
        if os.path.exists(ssh_config_path):
            try:
                with open(ssh_config_path, 'r') as f:
                    current_host = None
                    current_hostname = None
                    current_user = None
                    current_port = None
                    
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        parts = line.split(None, 1)
                        if len(parts) < 2:
                            continue
                        
                        key, value = parts[0].lower(), parts[1]
                        
                        if key == 'host' and value != '*':
                            # Save previous host
                            if current_host:
                                desc_parts = []
                                if current_hostname:
                                    desc_parts.append(current_hostname)
                                if current_user:
                                    desc_parts.append(f"user={current_user}")
                                if current_port:
                                    desc_parts.append(f"port={current_port}")
                                
                                hosts.append({
                                    'host': current_host,
                                    'desc': ', '.join(desc_parts) if desc_parts else 'SSH Config',
                                    'type': 'config',
                                    'hostname': current_hostname,
                                    'user': current_user,
                                    'port': current_port
                                })
                            
                            current_host = value
                            current_hostname = None
                            current_user = None
                            current_port = None
                        
                        elif key == 'hostname':
                            current_hostname = value
                        elif key == 'user':
                            current_user = value
                        elif key == 'port':
                            current_port = value
                    
                    # Don't forget the last host
                    if current_host:
                        desc_parts = []
                        if current_hostname:
                            desc_parts.append(current_hostname)
                        if current_user:
                            desc_parts.append(f"user={current_user}")
                        if current_port:
                            desc_parts.append(f"port={current_port}")
                        
                        hosts.append({
                            'host': current_host,
                            'desc': ', '.join(desc_parts) if desc_parts else 'SSH Config',
                            'type': 'config',
                            'hostname': current_hostname,
                            'user': current_user,
                            'port': current_port
                        })
            except Exception:
                pass
        
        return hosts
    
    def add_ssh_host(self, host: str):
        """
        Add a host to SSH history
        
        Args:
            host: The host string (user@hostname or hostname)
        """
        self.__init_extended_history()
        
        # Remove if already exists
        if host in self.ssh_hosts:
            self.ssh_hosts.remove(host)
        
        # Add to front
        self.ssh_hosts.insert(0, host)
        
        # Trim if needed
        if len(self.ssh_hosts) > self.max_ssh_hosts:
            self.ssh_hosts = self.ssh_hosts[:self.max_ssh_hosts]
    
    def get_ssh_keys(self) -> List[Dict]:
        """
        Get list of SSH identity files
        
        Returns:
            List of key info dicts
        """
        keys = []
        ssh_dir = os.path.expanduser('~/.ssh')
        
        if os.path.exists(ssh_dir):
            try:
                for entry in os.listdir(ssh_dir):
                    path = os.path.join(ssh_dir, entry)
                    if os.path.isfile(path):
                        # Look for private keys (no .pub extension, not config/known_hosts)
                        if (not entry.endswith('.pub') and 
                            entry not in ('config', 'known_hosts', 'authorized_keys') and
                            not entry.startswith('.')):
                            keys.append({
                                'name': entry,
                                'path': path,
                                'desc': 'Private key'
                            })
            except PermissionError:
                pass
        
        return keys
    
    def get_recent_urls(self) -> List[str]:
        """
        Get list of recently used URLs
        
        Returns:
            List of URL strings
        """
        self.__init_extended_history()
        return self.recent_urls.copy()
    
    def add_recent_url(self, url: str):
        """
        Add a URL to recent history
        
        Args:
            url: The URL string
        """
        self.__init_extended_history()
        
        # Remove if already exists
        if url in self.recent_urls:
            self.recent_urls.remove(url)
        
        # Add to front
        self.recent_urls.insert(0, url)
        
        # Trim if needed
        if len(self.recent_urls) > self.max_recent_urls:
            self.recent_urls = self.recent_urls[:self.max_recent_urls]
    
    def get_installed_packages(self) -> List[Dict]:
        """
        Get list of installed apt packages
        
        Returns:
            List of package info dicts
        """
        packages = []
        try:
            result = subprocess.run(
                ['dpkg', '--get-selections'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.strip().split('\n')[:200]:  # Limit to 200
                parts = line.split()
                if len(parts) >= 2 and parts[1] == 'install':
                    packages.append({
                        'name': parts[0],
                        'desc': 'Installed'
                    })
            
            return packages
        except Exception:
            return []
    
    def search_packages(self, query: str) -> List[Dict]:
        """
        Search for apt packages
        
        Args:
            query: Search query
            
        Returns:
            List of package info dicts
        """
        packages = []
        try:
            result = subprocess.run(
                ['apt-cache', 'search', query],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            for line in result.stdout.strip().split('\n')[:50]:  # Limit to 50
                if ' - ' in line:
                    name, desc = line.split(' - ', 1)
                    packages.append({
                        'name': name.strip(),
                        'desc': desc.strip()[:50]  # Truncate description
                    })
            
            return packages
        except Exception:
            return []
    
    def is_live_command(self, command: str) -> bool:
        """
        Check if a command should run in live mode
        
        Args:
            command: The command to check
            
        Returns:
            True if command should run in live mode
        """
        live_patterns = ['htop', 'top', 'tail -f', 'watch ', 'ping ', 'iotop', 'iftop']
        cmd_lower = command.lower()
        
        for pattern in live_patterns:
            if pattern in cmd_lower:
                return True
        
        return False
    
    def execute_live(self, command: str, callback: Callable[[List[str], bool], None]) -> bool:
        """
        Execute a command with live output updates
        
        Args:
            command: The command to execute
            callback: Function called with (lines, is_complete) on each update
            
        Returns:
            True if command started successfully
        """
        self.__init_extended_history()
        
        # Cancel any existing live process
        self.cancel_live()
        
        try:
            self.live_process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=self.cwd,
                preexec_fn=os.setsid,
                bufsize=1,
                universal_newlines=True
            )
            
            self.live_output_lines = []
            self.live_callback = callback
            self.is_running = True
            
            # Start reader thread
            self._live_reader_thread = threading.Thread(
                target=self._read_live_output,
                daemon=True
            )
            self._live_reader_thread.start()
            
            return True
            
        except Exception as e:
            if callback:
                callback([f"Error: {str(e)}"], True)
            return False
    
    def _read_live_output(self):
        """Background thread to read live output"""
        try:
            max_lines = 1000
            
            while self.live_process and self.live_process.poll() is None:
                line = self.live_process.stdout.readline()
                if line:
                    self.live_output_lines.append(line.rstrip())
                    
                    # Trim if too many lines
                    if len(self.live_output_lines) > max_lines:
                        self.live_output_lines = self.live_output_lines[-max_lines:]
                    
                    if self.live_callback:
                        self.live_callback(self.live_output_lines.copy(), False)
            
            # Read any remaining output
            if self.live_process:
                remaining = self.live_process.stdout.read()
                if remaining:
                    for line in remaining.split('\n'):
                        if line:
                            self.live_output_lines.append(line.rstrip())
            
            # Signal completion
            if self.live_callback:
                self.live_callback(self.live_output_lines.copy(), True)
                
        except Exception as e:
            if self.live_callback:
                self.live_callback([f"Error: {str(e)}"], True)
        finally:
            self.is_running = False
    
    def cancel_live(self):
        """Cancel the currently running live command"""
        self.__init_extended_history()
        
        if self.live_process:
            try:
                os.killpg(os.getpgid(self.live_process.pid), signal.SIGKILL)
                self.live_process.wait()
            except Exception:
                pass
            finally:
                self.live_process = None
                self.is_running = False
    
    def get_live_output(self) -> List[str]:
        """
        Get current live output lines
        
        Returns:
            List of output lines
        """
        self.__init_extended_history()
        return self.live_output_lines.copy()
