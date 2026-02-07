import unittest

import maxbloks.terminal.ui.font_manager as font_manager_module
from maxbloks.terminal.ui.font_manager import FontManager


class TestFontManager(unittest.TestCase):

    def setUp(self):
        FontManager._instance = None
        FontManager._fonts = {}

    def tearDown(self):
        FontManager._instance = None
        FontManager._fonts = {}

    def test_singleton_pattern(self):
        instance1 = FontManager.get_instance()
        instance2 = FontManager.get_instance()
        self.assertIs(instance1, instance2)

    def test_get_instance_creates_instance(self):
        self.assertIsNone(FontManager._instance)
        instance = FontManager.get_instance()
        self.assertIsNotNone(instance)
        self.assertIsNotNone(FontManager._instance)

    def test_initialization(self):
        manager = FontManager()
        self.assertIsNotNone(manager._fonts)

    def test_font_loading(self):
        manager = FontManager()
        self.assertIn('large', manager._fonts)
        self.assertIn('medium', manager._fonts)
        self.assertIn('small', manager._fonts)
        self.assertIn('large_bold', manager._fonts)
        self.assertIn('medium_bold', manager._fonts)

    def test_get_existing_font(self):
        manager = FontManager()
        font = manager.get('large')
        self.assertIsNotNone(font)

    def test_get_nonexistent_font_returns_medium(self):
        manager = FontManager()
        font = manager.get('nonexistent')
        self.assertIsNotNone(font)
        self.assertEqual(font, manager.get('medium'))

    def test_get_small_font(self):
        manager = FontManager()
        font = manager.get('small')
        self.assertIsNotNone(font)

    def test_get_medium_font(self):
        manager = FontManager()
        font = manager.get('medium')
        self.assertIsNotNone(font)

    def test_get_large_font(self):
        manager = FontManager()
        font = manager.get('large')
        self.assertIsNotNone(font)

    def test_get_large_bold_font(self):
        manager = FontManager()
        font = manager.get('large_bold')
        self.assertIsNotNone(font)

    def test_get_medium_bold_font(self):
        manager = FontManager()
        font = manager.get('medium_bold')
        self.assertIsNotNone(font)

    def test_get_instance_after_direct_init(self):
        FontManager()
        instance = FontManager.get_instance()
        self.assertIsNotNone(instance)