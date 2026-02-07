import unittest

import maxbloks.terminal.ui.output_display as output_display_module
from maxbloks.terminal.ui.output_display import OutputDisplay


class TestOutputDisplay(unittest.TestCase):

    def setUp(self):
        self.display = OutputDisplay(0, 0, 1024, 200)

    def test_initialization(self):
        self.assertEqual(self.display.rect.x, 0)
        self.assertEqual(self.display.rect.y, 0)
        self.assertEqual(self.display.rect.width, 1024)
        self.assertEqual(self.display.rect.height, 200)
        self.assertEqual(len(self.display.lines), 0)
        self.assertEqual(self.display.scroll_offset, 0)
        self.assertFalse(self.display.expanded)
        self.assertFalse(self.display.live_mode)
        self.assertTrue(self.display.auto_scroll)

    def test_set_output_stdout_only(self):
        self.display.set_output('line1\nline2\nline3', '', 0)
        self.assertEqual(len(self.display.lines), 4)
        self.assertIn('line1', self.display.lines[0][0])
        self.assertIn('✓ Command completed successfully', self.display.lines[3][0])

    def test_set_output_stderr_only(self):
        self.display.set_output('', 'error1\nerror2', 1)
        self.assertEqual(len(self.display.lines), 3)
        self.assertEqual(self.display.lines[0][1], 'error')
        self.assertIn('✗ Command exited with code 1', self.display.lines[2][0])

    def test_set_output_both(self):
        self.display.set_output('stdout line', 'stderr line', 1)
        self.assertEqual(len(self.display.lines), 3)

    def test_set_output_success(self):
        self.display.set_output('test', '', 0)
        self.assertIn('✓ Command completed successfully', 
                     [line[0] for line in self.display.lines])

    def test_set_output_failure(self):
        self.display.set_output('test', 'error', 1)
        self.assertIn('✗ Command exited with code 1', 
                     [line[0] for line in self.display.lines])

    def test_set_output_timeout(self):
        self.display.set_output('test', 'error', -1)
        self.assertIn('✗ Command failed or timed out', 
                     [line[0] for line in self.display.lines])

    def test_set_live_output_incomplete(self):
        self.display.set_live_output(['line1', 'line2', 'line3'], False)
        self.assertEqual(len(self.display.lines), 3)
        self.assertTrue(self.display.live_mode)

    def test_set_live_output_complete(self):
        self.display.set_live_output(['line1', 'line2'], True)
        self.assertEqual(len(self.display.lines), 3)
        self.assertFalse(self.display.live_mode)
        self.assertIn('✓ Live command completed', self.display.lines[2][0])

    def test_set_live_output_empty(self):
        self.display.set_live_output([], False)
        self.assertEqual(len(self.display.lines), 0)

    def test_set_message(self):
        self.display.set_message('Test message', 'warning')
        self.assertEqual(len(self.display.lines), 1)
        self.assertEqual(self.display.lines[0][0], 'Test message')
        self.assertEqual(self.display.lines[0][1], 'warning')

    def test_set_message_default_type(self):
        self.display.set_message('Test')
        self.assertEqual(self.display.lines[0][1], 'output')

    def test_clear(self):
        self.display.set_output('test', '', 0)
        self.display.clear()
        self.assertEqual(len(self.display.lines), 0)
        self.assertEqual(self.display.scroll_offset, 0)
        self.assertFalse(self.display.live_mode)

    def test_scroll_can_be_called(self):
        self.display.set_output('\n'.join(['line' + str(i) for i in range(50)]), '', 0)
        self.display.scroll(-1)
        self.display.scroll(1)
        self.display.scroll(-5)
        self.display.scroll(5)
        self.assertGreaterEqual(self.display.scroll_offset, 0)
        
    def test_scroll_down(self):
        self.display.set_output('\n'.join(['line' + str(i) for i in range(50)]), '', 0)
        self.display.scroll(-10)
        initial_offset = self.display.scroll_offset
        self.display.scroll(1)
        self.assertNotEqual(self.display.scroll_offset, initial_offset)

    def test_scroll_bounds(self):
        self.display.set_output('\n'.join(['line' + str(i) for i in range(50)]), '', 0)
        self.display.scroll(-100)
        self.assertGreaterEqual(self.display.scroll_offset, 0)
        self.display.scroll(100)
        self.assertGreaterEqual(self.display.scroll_offset, 0)

    def test_toggle_expanded(self):
        self.assertFalse(self.display.expanded)
        self.display.toggle_expanded()
        self.assertTrue(self.display.expanded)
        self.display.toggle_expanded()
        self.assertFalse(self.display.expanded)

    def test_start_live_mode(self):
        self.display.start_live_mode()
        self.assertTrue(self.display.live_mode)
        self.assertTrue(self.display.auto_scroll)
        self.assertEqual(len(self.display.lines), 0)
        self.assertEqual(self.display.scroll_offset, 0)

    def test_stop_live_mode(self):
        self.display.start_live_mode()
        self.display.stop_live_mode()
        self.assertFalse(self.display.live_mode)

    def test_scroll_auto_scroll_behavior(self):
        self.display.set_output('\n'.join(['line' + str(i) for i in range(50)]), '', 0)
        self.assertTrue(self.display.auto_scroll)
        self.display.scroll(-1)
        self.assertFalse(self.display.auto_scroll)
        self.display.scroll(1)
        self.assertFalse(self.display.auto_scroll)