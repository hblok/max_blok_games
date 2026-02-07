import unittest

import maxbloks.terminal.ui.button_hints as button_hints_module
from maxbloks.terminal.ui.button_hints import ButtonHints


class TestButtonHints(unittest.TestCase):

    def setUp(self):
        self.hints = ButtonHints(0, 0, 1024, 60)

    def test_initialization(self):
        self.assertEqual(self.hints.rect.x, 0)
        self.assertEqual(self.hints.rect.y, 0)
        self.assertEqual(self.hints.rect.width, 1024)
        self.assertEqual(self.hints.rect.height, 60)
        self.assertEqual(len(self.hints.hints), 0)

    def test_set_hints(self):
        test_hints = [('A', 'Select'), ('B', 'Back')]
        self.hints.set_hints(test_hints)
        self.assertEqual(len(self.hints.hints), 2)
        self.assertEqual(self.hints.hints[0], ('A', 'Select'))
        self.assertEqual(self.hints.hints[1], ('B', 'Back'))

    def test_set_hints_empty(self):
        self.hints.set_hints([])
        self.assertEqual(len(self.hints.hints), 0)

    def test_set_hints_single(self):
        test_hints = [('START', 'Exit')]
        self.hints.set_hints(test_hints)
        self.assertEqual(len(self.hints.hints), 1)

    def test_set_hints_replaces_previous(self):
        self.hints.set_hints([('A', 'Select')])
        self.hints.set_hints([('B', 'Back')])
        self.assertEqual(len(self.hints.hints), 1)
        self.assertEqual(self.hints.hints[0], ('B', 'Back'))

    def test_set_hints_with_many_items(self):
        test_hints = [
            ('A', 'Select'),
            ('B', 'Back'),
            ('X', 'Execute'),
            ('Y', 'Clear'),
            ('START', 'Exit'),
            ('SELECT', 'Output'),
        ]
        self.hints.set_hints(test_hints)
        self.assertEqual(len(self.hints.hints), 6)

    def test_set_hints_with_unicode(self):
        test_hints = [('↑↓', 'Navigate'), ('←→', 'Page')]
        self.hints.set_hints(test_hints)
        self.assertEqual(len(self.hints.hints), 2)