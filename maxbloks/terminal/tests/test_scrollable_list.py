import unittest

import maxbloks.terminal.ui.scrollable_list as scrollable_list_module
from maxbloks.terminal.ui.scrollable_list import ScrollableList


class TestScrollableList(unittest.TestCase):

    def setUp(self):
        self.list = ScrollableList(0, 0, 800, 600)

    def test_initialization(self):
        self.assertEqual(self.list.rect.x, 0)
        self.assertEqual(self.list.rect.y, 0)
        self.assertEqual(self.list.rect.width, 800)
        self.assertEqual(self.list.rect.height, 600)
        self.assertEqual(len(self.list.items), 0)
        self.assertEqual(self.list.selected_index, 0)
        self.assertEqual(self.list.scroll_offset, 0)
        self.assertEqual(self.list.target_scroll, 0)

    def test_set_items(self):
        items = [
            {'text': 'item1', 'desc': 'desc1'},
            {'text': 'item2', 'desc': 'desc2'},
        ]
        self.list.set_items(items)
        self.assertEqual(len(self.list.items), 2)
        self.assertEqual(self.list.selected_index, 0)
        self.assertEqual(self.list.scroll_offset, 0)

    def test_set_items_replaces_existing(self):
        self.list.set_items([{'text': 'old'}])
        self.list.set_items([{'text': 'new'}])
        self.assertEqual(len(self.list.items), 1)
        self.assertEqual(self.list.items[0]['text'], 'new')

    def test_set_items_empty(self):
        self.list.set_items([])
        self.assertEqual(len(self.list.items), 0)
        self.assertEqual(self.list.selected_index, 0)

    def test_move_selection_forward(self):
        items = [{'text': f'item{i}'} for i in range(10)]
        self.list.set_items(items)
        self.list.move_selection(1)
        self.assertEqual(self.list.selected_index, 1)
        self.list.move_selection(1)
        self.assertEqual(self.list.selected_index, 2)

    def test_move_selection_backward(self):
        items = [{'text': f'item{i}'} for i in range(10)]
        self.list.set_items(items)
        self.list.selected_index = 3
        self.list.move_selection(-1)
        self.assertEqual(self.list.selected_index, 2)

    def test_move_selection_bounds(self):
        items = [{'text': f'item{i}'} for i in range(5)]
        self.list.set_items(items)
        self.list.move_selection(-1)
        self.assertEqual(self.list.selected_index, 0)
        self.list.selected_index = 4
        self.list.move_selection(1)
        self.assertEqual(self.list.selected_index, 4)

    def test_move_selection_empty_list(self):
        self.list.move_selection(1)
        self.assertEqual(self.list.selected_index, 0)
        self.list.move_selection(-1)
        self.assertEqual(self.list.selected_index, 0)

    def test_page_scroll_forward(self):
        items = [{'text': f'item{i}'} for i in range(50)]
        self.list.set_items(items)
        self.list.page_scroll(1)
        self.assertGreater(self.list.selected_index, 0)

    def test_page_scroll_backward(self):
        items = [{'text': f'item{i}'} for i in range(50)]
        self.list.set_items(items)
        self.list.selected_index = 20
        self.list.page_scroll(-1)
        self.assertLess(self.list.selected_index, 20)

    def test_page_scroll_bounds(self):
        items = [{'text': f'item{i}'} for i in range(10)]
        self.list.set_items(items)
        self.list.page_scroll(1)
        self.assertLessEqual(self.list.selected_index, len(items) - 1)
        self.list.page_scroll(-1)
        self.assertGreaterEqual(self.list.selected_index, 0)

    def test_get_selected(self):
        items = [
            {'text': 'item1', 'desc': 'desc1'},
            {'text': 'item2', 'desc': 'desc2'},
        ]
        self.list.set_items(items)
        selected = self.list.get_selected()
        self.assertEqual(selected['text'], 'item1')

    def test_get_selected_different_index(self):
        items = [{'text': f'item{i}'} for i in range(5)]
        self.list.set_items(items)
        self.list.selected_index = 2
        selected = self.list.get_selected()
        self.assertEqual(selected['text'], 'item2')

    def test_get_selected_empty_list(self):
        selected = self.list.get_selected()
        self.assertIsNone(selected)

    def test_get_selected_invalid_index(self):
        items = [{'text': 'item1'}]
        self.list.set_items(items)
        self.list.selected_index = 10
        selected = self.list.get_selected()
        self.assertIsNone(selected)

    def test_update_smooth_scrolling(self):
        self.list.target_scroll = 5
        self.list.update()
        self.assertGreater(self.list.scroll_offset, 0)
        self.assertLess(self.list.scroll_offset, 5)

    def test_update_convergence(self):
        self.list.target_scroll = 5
        for _ in range(20):
            self.list.update()
        self.assertEqual(self.list.scroll_offset, 5)

    def test_update_no_change(self):
        self.list.target_scroll = 0
        self.list.scroll_offset = 0
        self.list.update()
        self.assertEqual(self.list.scroll_offset, 0)

    def test_target_scroll_adjusts_with_selection(self):
        items = [{'text': f'item{i}'} for i in range(50)]
        self.list.set_items(items)
        self.list.move_selection(50)
        self.assertGreater(self.list.target_scroll, 0)

    def test_items_with_description(self):
        items = [
            {'text': 'item1', 'desc': 'description1'},
            {'text': 'item2', 'desc': 'description2'},
        ]
        self.list.set_items(items)
        self.assertEqual(self.list.items[0]['desc'], 'description1')
        self.assertEqual(self.list.items[1]['desc'], 'description2')

    def test_items_with_type(self):
        items = [
            {'text': 'item1', 'type': 'file'},
            {'text': 'item2', 'type': 'dir'},
        ]
        self.list.set_items(items)
        self.assertEqual(self.list.items[0]['type'], 'file')
        self.assertEqual(self.list.items[1]['type'], 'dir')

    def test_animation_offset_initialization(self):
        self.assertEqual(self.list.animation_offset, 0)