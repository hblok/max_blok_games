import unittest

from unittest.mock import MagicMock

from maxbloks.terminal.ui.virtual_keyboard import (
    VirtualKeyboard,
    KeyboardMode,
    InputType
)
from maxbloks.terminal.ui.font_manager import FontManager


class TestVirtualKeyboard(unittest.TestCase):

    def setUp(self):
        self.colors = {
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
        self.keyboard = VirtualKeyboard(1024, 768, self.colors, None)

    def test_initialization(self):
        self.assertFalse(self.keyboard.visible)
        self.assertEqual(self.keyboard.mode, KeyboardMode.LOWERCASE)
        self.assertEqual(self.keyboard.selected_row, 0)
        self.assertEqual(self.keyboard.selected_col, 0)
        self.assertEqual(self.keyboard.input_text, '')
        self.assertEqual(self.keyboard.cursor_pos, 0)
        self.assertEqual(self.keyboard.max_length, 256)
        self.assertEqual(self.keyboard.input_type, InputType.TEXT)

    def test_show(self):
        callback_called = []
        
        def callback(result):
            callback_called.append(result)
        
        self.keyboard.show('Enter text:', callback)
        self.assertTrue(self.keyboard.visible)
        self.assertEqual(self.keyboard.prompt, 'Enter text:')
        self.assertIsNotNone(self.keyboard.callback)
        self.assertEqual(self.keyboard.input_text, '')
        self.assertEqual(self.keyboard.cursor_pos, 0)

    def test_show_with_initial_text(self):
        callback_called = []
        
        def callback(result):
            callback_called.append(result)
        
        self.keyboard.show('Enter text:', callback, initial_text='hello')
        self.assertEqual(self.keyboard.input_text, 'hello')
        self.assertEqual(self.keyboard.cursor_pos, 5)

    def test_hide(self):
        self.keyboard.show('Test:', lambda x: None)
        self.keyboard.hide()
        self.assertFalse(self.keyboard.visible)
        self.assertIsNone(self.keyboard.callback)

    def test_show_with_numeric_type(self):
        self.keyboard.show('Enter:', lambda x: None, input_type=InputType.NUMERIC)
        self.assertEqual(self.keyboard.mode, KeyboardMode.NUMBERS)

    def test_show_with_port_type(self):
        self.keyboard.show('Enter:', lambda x: None, input_type=InputType.PORT)
        self.assertEqual(self.keyboard.mode, KeyboardMode.NUMBERS)

    def test_show_with_text_type(self):
        self.keyboard.show('Enter:', lambda x: None, input_type=InputType.TEXT)
        self.assertEqual(self.keyboard.mode, KeyboardMode.LOWERCASE)

    def test_show_with_max_length(self):
        self.keyboard.show('Enter:', lambda x: None, max_length=100)
        self.assertEqual(self.keyboard.max_length, 100)

    def test_handle_input_up(self):
        self.keyboard.show('Test:', lambda x: None)
        self.keyboard.selected_row = 2
        self.keyboard.handle_input('UP')
        self.assertEqual(self.keyboard.selected_row, 1)

    def test_handle_input_down(self):
        self.keyboard.show('Test:', lambda x: None)
        self.keyboard.selected_row = 2
        self.keyboard.handle_input('DOWN')
        self.assertEqual(self.keyboard.selected_row, 3)

    def test_handle_input_left(self):
        self.keyboard.show('Test:', lambda x: None)
        self.keyboard.selected_col = 3
        self.keyboard.handle_input('LEFT')
        self.assertEqual(self.keyboard.selected_col, 2)

    def test_handle_input_right(self):
        self.keyboard.show('Test:', lambda x: None)
        self.keyboard.selected_col = 3
        self.keyboard.handle_input('RIGHT')
        self.assertGreater(self.keyboard.selected_col, 3)

    def test_handle_input_bounds(self):
        self.keyboard.show('Test:', lambda x: None)
        self.keyboard.handle_input('UP')
        self.assertEqual(self.keyboard.selected_row, 0)
        self.keyboard.selected_row = 4
        self.keyboard.handle_input('DOWN')
        self.assertEqual(self.keyboard.selected_row, 4)

    def test_handle_input_a_presses_key(self):
        self.keyboard.show('Test:', lambda x: None)
        self.keyboard.selected_row = 0
        self.keyboard.selected_col = 0
        initial_len = len(self.keyboard.input_text)
        self.keyboard.handle_input('A')
        self.assertEqual(len(self.keyboard.input_text), initial_len + 1)

    def test_handle_input_b_backspace(self):
        self.keyboard.show('Test:', lambda x: None, initial_text='hello')
        self.keyboard.cursor_pos = 5
        self.keyboard.handle_input('B')
        self.assertEqual(self.keyboard.input_text, 'hell')
        self.assertEqual(self.keyboard.cursor_pos, 4)

    def test_handle_input_b_backspace_empty(self):
        self.keyboard.show('Test:', lambda x: None)
        self.keyboard.cursor_pos = 0
        self.keyboard.handle_input('B')
        self.assertEqual(self.keyboard.input_text, '')
        self.assertEqual(self.keyboard.cursor_pos, 0)

    def test_handle_input_x_confirm_valid(self):
        callback_called = []
        
        def callback(result):
            callback_called.append(result)
        
        self.keyboard.show('Enter:', callback, initial_text='test')
        result = self.keyboard.handle_input('X')
        self.assertFalse(result)
        self.assertEqual(callback_called, ['test'])

    def test_handle_input_x_confirm_invalid(self):
        callback_called = []
        
        def callback(result):
            callback_called.append(result)
        
        self.keyboard.show('Enter:', callback)
        result = self.keyboard.handle_input('X')
        self.assertTrue(result)
        self.assertEqual(len(callback_called), 0)

    def test_handle_input_y_toggle_mode(self):
        self.keyboard.show('Test:', lambda x: None)
        initial_mode = self.keyboard.mode
        self.keyboard.handle_input('Y')
        self.assertNotEqual(self.keyboard.mode, initial_mode)

    def test_handle_input_start_cancel(self):
        callback_called = []
        
        def callback(result):
            callback_called.append(result)
        
        self.keyboard.show('Enter:', callback)
        result = self.keyboard.handle_input('START')
        self.assertFalse(result)
        self.assertEqual(callback_called, [None])

    def test_handle_input_l_move_cursor_left(self):
        self.keyboard.show('Test:', lambda x: None, initial_text='hello')
        self.keyboard.cursor_pos = 5
        self.keyboard.handle_input('L')
        self.assertEqual(self.keyboard.cursor_pos, 4)

    def test_handle_input_r_move_cursor_right(self):
        self.keyboard.show('Test:', lambda x: None, initial_text='hello')
        self.keyboard.cursor_pos = 0
        self.keyboard.handle_input('R')
        self.assertEqual(self.keyboard.cursor_pos, 1)

    def test_handle_input_when_not_visible(self):
        result = self.keyboard.handle_input('A')
        self.assertFalse(result)

    def test_validate_char_text_type(self):
        self.keyboard.input_type = InputType.TEXT
        self.assertTrue(self.keyboard._validate_char('a'))
        self.assertTrue(self.keyboard._validate_char('1'))
        self.assertTrue(self.keyboard._validate_char('@'))

    def test_validate_char_numeric_type(self):
        self.keyboard.input_type = InputType.NUMERIC
        self.assertTrue(self.keyboard._validate_char('5'))
        self.assertFalse(self.keyboard._validate_char('a'))
        self.assertFalse(self.keyboard._validate_char('@'))

    def test_validate_char_port_type(self):
        self.keyboard.input_type = InputType.PORT
        self.assertTrue(self.keyboard._validate_char('8'))
        self.assertFalse(self.keyboard._validate_char('a'))

    def test_validate_char_url_type(self):
        self.keyboard.input_type = InputType.URL
        self.assertTrue(self.keyboard._validate_char('h'))
        self.assertTrue(self.keyboard._validate_char('/'))
        self.assertTrue(self.keyboard._validate_char(':'))
        self.assertFalse(self.keyboard._validate_char(' '))

    def test_validate_char_ssh_host_type(self):
        self.keyboard.input_type = InputType.SSH_HOST
        self.assertTrue(self.keyboard._validate_char('u'))
        self.assertTrue(self.keyboard._validate_char('@'))
        self.assertTrue(self.keyboard._validate_char('.'))
        self.assertFalse(self.keyboard._validate_char('/'))

    def test_validate_char_filename_type(self):
        self.keyboard.input_type = InputType.FILENAME
        self.assertTrue(self.keyboard._validate_char('f'))
        self.assertTrue(self.keyboard._validate_char('.'))
        self.assertTrue(self.keyboard._validate_char('_'))
        self.assertFalse(self.keyboard._validate_char('/'))

    def test_validate_input_empty(self):
        self.keyboard.input_type = InputType.TEXT
        is_valid, error = self.keyboard._validate_input()
        self.assertFalse(is_valid)
        self.assertIn('empty', error.lower())

    def test_validate_input_valid_port(self):
        self.keyboard.input_type = InputType.PORT
        self.keyboard.input_text = '8080'
        is_valid, error = self.keyboard._validate_input()
        self.assertTrue(is_valid)
        self.assertEqual(error, '')

    def test_validate_input_invalid_port_too_low(self):
        self.keyboard.input_type = InputType.PORT
        self.keyboard.input_text = '0'
        is_valid, error = self.keyboard._validate_input()
        self.assertFalse(is_valid)
        self.assertIn('1-65535', error)

    def test_validate_input_invalid_port_too_high(self):
        self.keyboard.input_type = InputType.PORT
        self.keyboard.input_text = '99999'
        is_valid, error = self.keyboard._validate_input()
        self.assertFalse(is_valid)
        self.assertIn('1-65535', error)

    def test_validate_input_valid_url(self):
        self.keyboard.input_type = InputType.URL
        self.keyboard.input_text = 'https://example.com'
        is_valid, error = self.keyboard._validate_input()
        self.assertTrue(is_valid)

    def test_validate_input_invalid_url(self):
        self.keyboard.input_type = InputType.URL
        self.keyboard.input_text = 'not a url'
        is_valid, error = self.keyboard._validate_input()
        self.assertFalse(is_valid)

    def test_validate_input_valid_ssh_host(self):
        self.keyboard.input_type = InputType.SSH_HOST
        self.keyboard.input_text = 'user@example.com'
        is_valid, error = self.keyboard._validate_input()
        self.assertTrue(is_valid)

    def test_validate_input_invalid_ssh_host_no_user(self):
        self.keyboard.input_type = InputType.SSH_HOST
        self.keyboard.input_text = '@example.com'
        is_valid, error = self.keyboard._validate_input()
        self.assertFalse(is_valid)
        self.assertIn('user@hostname', error)

    def test_validate_input_invalid_ssh_host_no_host(self):
        self.keyboard.input_type = InputType.SSH_HOST
        self.keyboard.input_text = 'user@'
        is_valid, error = self.keyboard._validate_input()
        self.assertFalse(is_valid)
        self.assertIn('user@hostname', error)

    def test_cycle_mode(self):
        initial_mode = self.keyboard.mode
        self.keyboard._cycle_mode()
        self.assertNotEqual(self.keyboard.mode, initial_mode)
        self.assertIn(self.keyboard.mode, KeyboardMode)

    def test_multiple_cycles(self):
        modes_seen = []
        for _ in range(10):
            self.keyboard._cycle_mode()
            if self.keyboard.mode not in modes_seen:
                modes_seen.append(self.keyboard.mode)
        self.assertEqual(len(modes_seen), 4)

    def test_update_toggles_cursor_visibility(self):
        self.keyboard.show('Test:', lambda x: None)
        initial_visible = self.keyboard.cursor_visible
        for _ in range(35):
            self.keyboard.update()
        self.assertNotEqual(self.keyboard.cursor_visible, initial_visible)

    def test_get_current_layout(self):
        layout = self.keyboard._get_current_layout()
        self.assertIsInstance(layout, list)
        self.assertEqual(len(layout), 5)

    def test_get_key_at_valid(self):
        key = self.keyboard._get_key_at(0, 0)
        self.assertIsNotNone(key)

    def test_get_key_at_invalid(self):
        key = self.keyboard._get_key_at(10, 10)
        self.assertIsNone(key)

    def test_get_key_width_special_keys(self):
        self.assertEqual(self.keyboard._get_key_width('SPACE'), 4)
        self.assertEqual(self.keyboard._get_key_width('BACK'), 2)
        self.assertEqual(self.keyboard._get_key_width('MODE'), 2)
        self.assertEqual(self.keyboard._get_key_width('OK'), 2)

    def test_get_key_width_regular(self):
        self.assertEqual(self.keyboard._get_key_width('a'), 1)
        self.assertEqual(self.keyboard._get_key_width('1'), 1)

    def test_keyboard_mode_enum(self):
        self.assertEqual(KeyboardMode.LOWERCASE.value, 1)
        self.assertEqual(KeyboardMode.UPPERCASE.value, 2)
        self.assertEqual(KeyboardMode.NUMBERS.value, 3)
        self.assertEqual(KeyboardMode.SYMBOLS.value, 4)

    def test_input_type_enum(self):
        self.assertEqual(InputType.TEXT.value, 1)
        self.assertEqual(InputType.NUMERIC.value, 2)
        self.assertEqual(InputType.PORT.value, 3)
        self.assertEqual(InputType.URL.value, 4)
        self.assertEqual(InputType.SSH_HOST.value, 5)
        self.assertEqual(InputType.FILENAME.value, 6)