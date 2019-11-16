import unittest
import sys

sys.path.append('../../')

from emmet.html_matcher import attributes

def json_attrs(src: str, name: str=None):
    return [attr.to_json() for attr in attributes(src, name)]

class TestHTMLMatcherAttributes(unittest.TestCase):
    def test_parse_attribute_string(self):
        self.assertEqual(json_attrs('foo bar="baz" *ngIf={a == b} a=b '), [
            {
                'name': 'foo',
                'name_start': 0,
                'name_end': 3
            },
            {
                'name': 'bar',
                'value': '"baz"',
                'name_start': 4,
                'name_end': 7,
                'value_start': 8,
                'value_end': 13
            },
            {
                'name': '*ngIf',
                'value': '{a == b}',
                'name_start': 14,
                'name_end': 19,
                'value_start': 20,
                'value_end': 28
            },
            {
                'name': 'a',
                'value': 'b',
                'name_start': 29,
                'name_end': 30,
                'value_start': 31,
                'value_end': 32
            }
        ])
