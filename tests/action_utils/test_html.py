import unittest
import sys
import os.path

sys.path.append('../../')

from emmet.action_utils import select_item_html, get_open_tag


def read_file(file: str):
    dirname = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(dirname, file), 'r') as f:
        return f.read(None)


sample = read_file('sample.html')

class TestHTMLActionUtils(unittest.TestCase):
    def test_select_next_item(self):
        # `<li class="item item_1">`: select tag name, full attribute, attribute
        # value and class names
        self.assertEqual(select_item_html(sample, 9).to_json(), {
            'start': 9,
            'end': 33,
            'ranges': [
                (10, 12),
                (13, 32),
                (20, 31),
                (20, 24),
                (25, 31)
            ]
        })

        # <a href="/sample"  title={expr}>
        self.assertEqual(select_item_html(sample, 33).to_json(), {
            'start': 42,
            'end': 74,
            'ranges': [
                (43, 44),
                (45, 59),
                (51, 58),
                (61, 73),
                (68, 72)
            ]
        })

    def test_select_previous_item(self):
        # <a href="/sample"  title={expr}>
        self.assertEqual(select_item_html(sample, 80, True).to_json(), {
            'start': 42,
            'end': 74,
            'ranges': [
                (43, 44),
                (45, 59),
                (51, 58),
                (61, 73),
                (68, 72)
            ]
        })

        # <li class="item item_1">
        self.assertEqual(select_item_html(sample, 42, True).to_json(), {
            'start': 9,
            'end': 33,
            'ranges': [
                (10, 12),
                (13, 32),
                (20, 31),
                (20, 24),
                (25, 31)
            ]
        })

    def test_get_open_tag(self):
        self.assertEqual(get_open_tag(sample, 60).to_json(), {
            'name': 'a',
            'type': 1,
            'start': 42,
            'end': 74,
            'attributes': [{
                'name': 'href',
                'name_start': 45,
                'name_end': 49,
                'value': '"/sample"',
                'value_start': 50,
                'value_end': 59
            }, {
                'name': 'title',
                'name_start': 61,
                'name_end': 66,
                'value': '{expr}',
                'value_start': 67,
                'value_end': 73
            }]
        })

        self.assertEqual(get_open_tag(sample, 15).to_json(), {
            'name': 'li',
            'type': 1,
            'start': 9,
            'end': 33,
            'attributes': [{
                'name': 'class',
                'name_start': 13,
                'name_end': 18,
                'value': '"item item_1"',
                'value_start': 19,
                'value_end': 32
            }]
        })

        self.assertEqual(get_open_tag(sample, 74), None)
