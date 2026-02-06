import unittest
import tempfile
import os
from pathlib import Path

import maxbloks.terminal.core.command_executor as executor_module
from maxbloks.terminal.core.command_executor import CommandExecutor


class TestCommandExecutor(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.executor = CommandExecutor(timeout=10)

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        self.assertEqual(self.executor.timeout, 10)
        self.assertEqual(self.executor.max_history, 10)
        self.assertEqual(self.executor.max_recent_dirs, 10)
        self.assertFalse(self.executor.is_running)
        self.assertEqual(self.executor.last_return_code, 0)
        self.assertIsNotNone(self.executor.cwd)

    def test_is_dangerous_with_safe_command(self):
        self.assertFalse(self.executor.is_dangerous('ls'))
        self.assertFalse(self.executor.is_dangerous('pwd'))
        self.assertFalse(self.executor.is_dangerous('echo hello'))

    def test_is_dangerous_with_dangerous_command(self):
        self.assertTrue(self.executor.is_dangerous('rm'))
        self.assertTrue(self.executor.is_dangerous('rm -rf /'))
        self.assertTrue(self.executor.is_dangerous('killall'))
        self.assertTrue(self.executor.is_dangerous('reboot'))
        self.assertTrue(self.executor.is_dangerous('shutdown'))

    def test_is_dangerous_with_empty_command(self):
        self.assertFalse(self.executor.is_dangerous(''))
        self.assertFalse(self.executor.is_dangerous('   '))

    def test_is_dangerous_with_dangerous_patterns(self):
        self.assertTrue(self.executor.is_dangerous('rm -rf /'))
        self.assertTrue(self.executor.is_dangerous('rm -rf ~'))
        self.assertTrue(self.executor.is_dangerous('rm -rf *'))
        self.assertTrue(self.executor.is_dangerous('dd if=/dev/zero'))
        self.assertTrue(self.executor.is_dangerous('mkfs /dev/sda1'))

    def test_get_danger_level(self):
        self.assertIn('EXTREME DANGER', self.executor.get_danger_level('rm -rf /'))
        self.assertIn('WARNING', self.executor.get_danger_level('reboot'))
        self.assertIn('CAUTION', self.executor.get_danger_level('rm'))
        self.assertIn('changes', self.executor.get_danger_level('ls'))

    def test_execute_simple_command(self):
        stdout, stderr, return_code = self.executor.execute('echo hello')
        self.assertEqual(return_code, 0)
        self.assertIn('hello', stdout)

    def test_execute_command_with_failure(self):
        stdout, stderr, return_code = self.executor.execute('ls /nonexistent')
        self.assertNotEqual(return_code, 0)
        self.assertTrue(len(stderr) > 0)

    def test_execute_history_command(self):
        stdout, stderr, return_code = self.executor.execute('history')
        self.assertEqual(return_code, 0)
        self.assertIn('No commands', stdout)

    def test_execute_history_after_commands(self):
        self.executor.execute('echo test1')
        self.executor.execute('echo test2')
        stdout, stderr, return_code = self.executor.execute('history')
        self.assertEqual(return_code, 0)
        self.assertIn('test1', stdout)
        self.assertIn('test2', stdout)

    def test_handle_cd_to_home(self):
        stdout, stderr, return_code = self.executor.execute('cd')
        self.assertEqual(return_code, 0)
        self.assertIn('Changed directory', stdout)

    def test_handle_cd_to_temp_dir(self):
        stdout, stderr, return_code = self.executor.execute(f'cd {self.temp_dir}')
        self.assertEqual(return_code, 0)
        self.assertEqual(self.executor.cwd, self.temp_dir)

    def test_handle_cd_to_nonexistent(self):
        stdout, stderr, return_code = self.executor.execute('cd /nonexistent_12345')
        self.assertNotEqual(return_code, 0)
        self.assertIn('No such file', stderr)

    def test_handle_cd_to_file(self):
        test_file = Path(self.temp_dir) / 'test.txt'
        test_file.touch()
        stdout, stderr, return_code = self.executor.execute(f'cd {test_file}')
        self.assertNotEqual(return_code, 0)
        self.assertIn('Not a directory', stderr)

    def test_history_max_size(self):
        for i in range(15):
            self.executor.execute(f'echo test{i}')
        history = self.executor.get_history_commands()
        self.assertLessEqual(len(history), 10)

    def test_add_recent_directory(self):
        self.executor._add_recent_dir('/tmp')
        self.executor._add_recent_dir('/home')
        dirs = self.executor.get_recent_directories()
        self.assertEqual(dirs[0], '/home')
        self.assertEqual(dirs[1], '/tmp')

    def test_recent_dirs_max_size(self):
        for i in range(15):
            self.executor._add_recent_dir(f'/dir{i}')
        dirs = self.executor.get_recent_directories()
        self.assertLessEqual(len(dirs), 10)

    def test_recent_dirs_uniqueness(self):
        self.executor._add_recent_dir('/tmp')
        self.executor._add_recent_dir('/home')
        self.executor._add_recent_dir('/tmp')
        dirs = self.executor.get_recent_directories()
        self.assertEqual(dirs.count('/tmp'), 1)
        self.assertEqual(dirs[0], '/tmp')

    def test_get_files(self):
        Path(self.temp_dir).joinpath('file1.txt').touch()
        Path(self.temp_dir).joinpath('file2.txt').touch()
        self.executor.cwd = self.temp_dir
        files = self.executor.get_files()
        self.assertEqual(len(files), 2)
        self.assertIn('file1.txt', files)
        self.assertIn('file2.txt', files)

    def test_get_files_with_hidden(self):
        Path(self.temp_dir).joinpath('.hidden').touch()
        Path(self.temp_dir).joinpath('visible').touch()
        self.executor.cwd = self.temp_dir
        files = self.executor.get_files(include_hidden=False)
        self.assertNotIn('.hidden', files)
        self.assertIn('visible', files)

    def test_get_directories(self):
        Path(self.temp_dir).joinpath('dir1').mkdir()
        Path(self.temp_dir).joinpath('dir2').mkdir()
        self.executor.cwd = self.temp_dir
        dirs = self.executor.get_directories()
        self.assertIn('..', dirs)
        self.assertIn('dir1', dirs)
        self.assertIn('dir2', dirs)

    def test_get_files_and_dirs(self):
        Path(self.temp_dir).joinpath('file.txt').touch()
        Path(self.temp_dir).joinpath('directory').mkdir()
        self.executor.cwd = self.temp_dir
        items = self.executor.get_files_and_dirs()
        item_names = [item['name'] for item in items]
        self.assertIn('..', item_names)
        self.assertIn('file.txt', item_names)
        self.assertIn('directory', item_names)

    def test_get_processes(self):
        processes = self.executor.get_processes()
        self.assertIsInstance(processes, list)
        if processes:
            self.assertIn('pid', processes[0])
            self.assertIn('cpu', processes[0])
            self.assertIn('mem', processes[0])
            self.assertIn('command', processes[0])

    def test_get_process_names(self):
        names = self.executor.get_process_names()
        self.assertIsInstance(names, list)
        self.assertGreater(len(names), 0)

    def test_get_history_commands(self):
        self.executor.execute('echo test')
        commands = self.executor.get_history_commands()
        self.assertIn('echo test', commands)

    def test_get_recent_directories(self):
        dirs = self.executor.get_recent_directories()
        self.assertIsInstance(dirs, list)
        self.assertGreater(len(dirs), 0)

    def test_add_ssh_host(self):
        self.executor.add_ssh_host('user@example.com')
        self.executor.add_ssh_host('root@server')
        hosts = self.executor.get_ssh_hosts()
        self.assertEqual(len(hosts), 2)

    def test_ssh_hosts_max_size(self):
        for i in range(15):
            self.executor.add_ssh_host(f'user{i}@example.com')
        hosts = self.executor.get_ssh_hosts()
        self.assertLessEqual(len(hosts), 10)

    def test_ssh_hosts_uniqueness(self):
        self.executor.add_ssh_host('user@example.com')
        self.executor.add_ssh_host('root@server')
        self.executor.add_ssh_host('user@example.com')
        hosts = self.executor.get_ssh_hosts()
        recent_hosts = [h for h in hosts if h.get('type') == 'recent']
        self.assertEqual(len(recent_hosts), 2)

    def test_get_ssh_keys(self):
        ssh_dir = Path.home() / '.ssh'
        if ssh_dir.exists():
            keys = self.executor.get_ssh_keys()
            self.assertIsInstance(keys, list)

    def test_add_recent_url(self):
        self.executor.add_recent_url('https://example.com')
        self.executor.add_recent_url('https://test.com')
        urls = self.executor.get_recent_urls()
        self.assertEqual(len(urls), 2)

    def test_recent_urls_max_size(self):
        for i in range(15):
            self.executor.add_recent_url(f'https://example{i}.com')
        urls = self.executor.get_recent_urls()
        self.assertLessEqual(len(urls), 10)

    def test_recent_urls_uniqueness(self):
        self.executor.add_recent_url('https://example.com')
        self.executor.add_recent_url('https://test.com')
        self.executor.add_recent_url('https://example.com')
        urls = self.executor.get_recent_urls()
        self.assertEqual(urls.count('https://example.com'), 1)
        self.assertEqual(urls[0], 'https://example.com')

    def test_search_packages(self):
        packages = self.executor.search_packages('python')
        self.assertIsInstance(packages, list)

    def test_is_live_command(self):
        self.assertTrue(self.executor.is_live_command('htop'))
        self.assertTrue(self.executor.is_live_command('top'))
        self.assertTrue(self.executor.is_live_command('tail -f'))
        self.assertTrue(self.executor.is_live_command('ping localhost'))
        self.assertTrue(self.executor.is_live_command('watch ls'))
        self.assertFalse(self.executor.is_live_command('ls'))
        self.assertFalse(self.executor.is_live_command('echo'))

    def test_cancel(self):
        self.executor.cancel()
        self.assertFalse(self.executor.is_running)

    def test_execute_updates_last_output(self):
        self.executor.execute('echo test')
        self.assertIn('test', self.executor.last_output)

    def test_execute_updates_last_error(self):
        self.executor.execute('ls /nonexistent')
        self.assertGreater(len(self.executor.last_error), 0)

    def test_execute_updates_return_code(self):
        self.executor.execute('echo test')
        self.assertEqual(self.executor.last_return_code, 0)

    def test_extended_history_initialization(self):
        self.executor.get_ssh_hosts()
        self.assertIsNotNone(self.executor.ssh_hosts)
        self.assertIsNotNone(self.executor.recent_urls)
        self.assertIsNotNone(self.executor.max_ssh_hosts)
        self.assertIsNotNone(self.executor.max_recent_urls)

    def test_get_live_output(self):
        lines = self.executor.get_live_output()
        self.assertIsInstance(lines, list)

    def test_get_cwd(self):
        cwd = self.executor.get_cwd()
        self.assertIsInstance(cwd, str)
        self.assertTrue(os.path.exists(cwd))