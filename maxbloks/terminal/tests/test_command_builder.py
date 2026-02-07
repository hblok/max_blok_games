import unittest
import os

import maxbloks.terminal.ui.command_builder as command_builder_module
from maxbloks.terminal.ui.command_builder import CommandBuilder


class TestCommandBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = CommandBuilder(0, 0, 1024, 80)

    def test_initialization(self):
        self.assertEqual(self.builder.rect.x, 0)
        self.assertEqual(self.builder.rect.y, 0)
        self.assertEqual(self.builder.rect.width, 1024)
        self.assertEqual(self.builder.rect.height, 80)
        self.assertEqual(len(self.builder.command_parts), 0)
        self.assertEqual(self.builder.cwd, '~')
        self.assertEqual(self.builder.status, 'Ready')
        self.assertEqual(self.builder.status_type, 'normal')
        self.assertEqual(self.builder.selected_chip, -1)
        self.assertFalse(self.builder.chip_mode)

    def test_add_part(self):
        self.builder.add_part('ls')
        self.assertEqual(len(self.builder.command_parts), 1)
        self.assertEqual(self.builder.command_parts[0], 'ls')

    def test_add_multiple_parts(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        self.builder.add_part('/tmp')
        self.assertEqual(len(self.builder.command_parts), 3)

    def test_remove_last(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        result = self.builder.remove_last()
        self.assertTrue(result)
        self.assertEqual(len(self.builder.command_parts), 1)
        self.assertEqual(self.builder.command_parts[0], 'ls')

    def test_remove_last_empty(self):
        result = self.builder.remove_last()
        self.assertFalse(result)
        self.assertEqual(len(self.builder.command_parts), 0)

    def test_remove_at_valid_index(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        self.builder.add_part('/tmp')
        result = self.builder.remove_at(1)
        self.assertTrue(result)
        self.assertEqual(len(self.builder.command_parts), 2)
        self.assertEqual(self.builder.command_parts[1], '/tmp')

    def test_remove_at_invalid_index(self):
        self.builder.add_part('ls')
        result = self.builder.remove_at(5)
        self.assertFalse(result)
        self.assertEqual(len(self.builder.command_parts), 1)

    def test_remove_at_index_zero(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        result = self.builder.remove_at(0)
        self.assertTrue(result)
        self.assertEqual(len(self.builder.command_parts), 1)
        self.assertEqual(self.builder.command_parts[0], '-la')

    def test_remove_at_negative_index(self):
        self.builder.add_part('ls')
        result = self.builder.remove_at(-1)
        self.assertFalse(result)

    def test_remove_selected_chip_not_in_mode(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        result = self.builder.remove_selected_chip()
        self.assertFalse(result)
        self.assertEqual(len(self.builder.command_parts), 2)

    def test_remove_selected_chip_in_mode(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        self.builder.add_part('/tmp')
        self.builder.enter_chip_mode()
        result = self.builder.remove_selected_chip()
        self.assertTrue(result)
        self.assertEqual(len(self.builder.command_parts), 2)
        self.assertEqual(self.builder.command_parts[0], 'ls')

    def test_enter_chip_mode_with_parts(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        self.builder.enter_chip_mode()
        self.assertTrue(self.builder.chip_mode)
        self.assertEqual(self.builder.selected_chip, 1)

    def test_enter_chip_mode_without_parts(self):
        self.builder.enter_chip_mode()
        self.assertFalse(self.builder.chip_mode)
        self.assertEqual(self.builder.selected_chip, -1)

    def test_enter_chip_mode_with_only_command(self):
        self.builder.add_part('ls')
        self.builder.enter_chip_mode()
        self.assertFalse(self.builder.chip_mode)

    def test_exit_chip_mode(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        self.builder.enter_chip_mode()
        self.builder.exit_chip_mode()
        self.assertFalse(self.builder.chip_mode)
        self.assertEqual(self.builder.selected_chip, -1)

    def test_move_chip_selection_forward(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        self.builder.add_part('/tmp')
        self.builder.enter_chip_mode()
        self.builder.move_chip_selection(1)
        self.assertEqual(self.builder.selected_chip, 2)

    def test_move_chip_selection_backward(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        self.builder.add_part('/tmp')
        self.builder.enter_chip_mode()
        self.builder.selected_chip = 2
        self.builder.move_chip_selection(-1)
        self.assertEqual(self.builder.selected_chip, 1)

    def test_move_chip_selection_bounds(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        self.builder.add_part('/tmp')
        self.builder.enter_chip_mode()
        self.builder.move_chip_selection(-1)
        self.assertEqual(self.builder.selected_chip, 1)
        self.builder.move_chip_selection(1)
        self.assertEqual(self.builder.selected_chip, 2)
        self.builder.move_chip_selection(1)
        self.assertEqual(self.builder.selected_chip, 2)

    def test_move_chip_selection_not_in_mode(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        self.builder.move_chip_selection(1)
        self.assertEqual(self.builder.selected_chip, -1)

    def test_clear(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        self.builder.enter_chip_mode()
        self.builder.clear()
        self.assertEqual(len(self.builder.command_parts), 0)
        self.assertEqual(self.builder.selected_chip, -1)
        self.assertFalse(self.builder.chip_mode)

    def test_get_command(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        command = self.builder.get_command()
        self.assertEqual(command, 'ls -la')

    def test_get_command_empty(self):
        command = self.builder.get_command()
        self.assertEqual(command, '')

    def test_get_parts_count(self):
        self.assertEqual(self.builder.get_parts_count(), 0)
        self.builder.add_part('ls')
        self.assertEqual(self.builder.get_parts_count(), 1)
        self.builder.add_part('-la')
        self.assertEqual(self.builder.get_parts_count(), 2)

    def test_set_status(self):
        self.builder.set_status('Running...', 'running')
        self.assertEqual(self.builder.status, 'Running...')
        self.assertEqual(self.builder.status_type, 'running')

    def test_set_cwd_home(self):
        home = os.path.expanduser('~')
        self.builder.set_cwd(home)
        self.assertEqual(self.builder.cwd, '~')

    def test_set_cwd_subdirectory(self):
        home = os.path.expanduser('~')
        self.builder.set_cwd(home + '/Documents')
        self.assertEqual(self.builder.cwd, '~/Documents')

    def test_set_command(self):
        parts = ['ls', '-la', '/tmp']
        self.builder.set_command(parts)
        self.assertEqual(len(self.builder.command_parts), 3)
        self.assertEqual(self.builder.selected_chip, -1)

    def test_set_command_replaces_existing(self):
        self.builder.add_part('old')
        parts = ['new', 'command']
        self.builder.set_command(parts)
        self.assertEqual(len(self.builder.command_parts), 2)
        self.assertEqual(self.builder.command_parts[0], 'new')

    def test_chip_rects_list_exists(self):
        self.builder.add_part('ls')
        self.builder.add_part('-la')
        self.assertIsInstance(self.builder.chip_rects, list)