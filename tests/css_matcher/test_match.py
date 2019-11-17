import unittest
import sys
import os.path

sys.path.append('../../')

from emmet.css_matcher import match

def read_file(file: str):
    dirname = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(dirname, file), 'r') as f:
        return f.read(None)

code = read_file('sample.scss')

class TestCSSMatch(unittest.TestCase):
    def test_match_selector(self):
        self.assertEqual(match(code, 63).to_json(), {
            'type': 'selector',
            'start': 61,
            'end': 198,
            'body_start': 66,
            'body_end': 197
        })

        self.assertEqual(match(code, 208).to_json(), {
            'type': 'selector',
            'start': 204,
            'end': 267,
            'body_start': 209,
            'body_end': 266
        })

    def test_property(self):
        self.assertEqual(match(code, 140).to_json(), {
            'type': 'property',
            'start': 137,
            'end': 150,
            'body_start': 145,
            'body_end': 149
        })
