import unittest

import maxbloks.terminal.ui.confirm_dialog as confirm_dialog_module
from maxbloks.terminal.ui.confirm_dialog import ConfirmDialog


class TestConfirmDialog(unittest.TestCase):

    def setUp(self):
        self.dialog = ConfirmDialog(1024, 768)

    def test_initialization(self):
        self.assertEqual(self.dialog.width, 500)
        self.assertEqual(self.dialog.height, 200)
        self.assertFalse(self.dialog.visible)
        self.assertEqual(self.dialog.command, '')
        self.assertEqual(self.dialog.warning, '')
        self.assertEqual(self.dialog.selected_option, 0)
        self.assertIsNone(self.dialog.callback)

    def test_show(self):
        callback_called = []
        
        def callback(confirmed):
            callback_called.append(confirmed)
        
        self.dialog.show('rm -rf /', 'This will delete all files', callback)
        self.assertTrue(self.dialog.visible)
        self.assertEqual(self.dialog.command, 'rm -rf /')
        self.assertEqual(self.dialog.warning, 'This will delete all files')
        self.assertEqual(self.dialog.selected_option, 0)
        self.assertIsNotNone(self.dialog.callback)

    def test_hide(self):
        self.dialog.show('test', 'warning', lambda x: None)
        self.dialog.hide()
        self.assertFalse(self.dialog.visible)
        self.assertIsNone(self.dialog.callback)

    def test_move_selection_forward(self):
        self.dialog.show('test', 'warning', lambda x: None)
        self.dialog.move_selection(1)
        self.assertEqual(self.dialog.selected_option, 1)

    def test_move_selection_backward(self):
        self.dialog.selected_option = 1
        self.dialog.move_selection(-1)
        self.assertEqual(self.dialog.selected_option, 0)

    def test_move_selection_wraps_forward(self):
        self.dialog.selected_option = 1
        self.dialog.move_selection(1)
        self.assertEqual(self.dialog.selected_option, 0)

    def test_move_selection_wraps_backward(self):
        self.dialog.move_selection(-1)
        self.assertEqual(self.dialog.selected_option, 1)

    def test_confirm_with_selected_option_0(self):
        callback_called = []
        
        def callback(confirmed):
            callback_called.append(confirmed)
        
        self.dialog.show('test', 'warning', callback)
        self.dialog.selected_option = 0
        self.dialog.confirm()
        self.assertFalse(self.dialog.visible)
        self.assertEqual(callback_called, [False])

    def test_confirm_with_selected_option_1(self):
        callback_called = []
        
        def callback(confirmed):
            callback_called.append(confirmed)
        
        self.dialog.show('test', 'warning', callback)
        self.dialog.selected_option = 1
        self.dialog.confirm()
        self.assertFalse(self.dialog.visible)
        self.assertEqual(callback_called, [True])

    def test_cancel(self):
        callback_called = []
        
        def callback(confirmed):
            callback_called.append(confirmed)
        
        self.dialog.show('test', 'warning', callback)
        self.dialog.cancel()
        self.assertFalse(self.dialog.visible)
        self.assertEqual(callback_called, [False])

    def test_confirm_without_callback(self):
        self.dialog.callback = None
        self.dialog.selected_option = 1
        self.dialog.confirm()
        self.assertFalse(self.dialog.visible)

    def test_cancel_without_callback(self):
        self.dialog.callback = None
        self.dialog.cancel()
        self.assertFalse(self.dialog.visible)

    def test_multiple_moves(self):
        self.dialog.move_selection(1)
        self.assertEqual(self.dialog.selected_option, 1)
        self.dialog.move_selection(1)
        self.assertEqual(self.dialog.selected_option, 0)
        self.dialog.move_selection(-1)
        self.assertEqual(self.dialog.selected_option, 1)