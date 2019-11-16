import unittest
import sys
import os.path

sys.path.append('../../')

from emmet.html_matcher import balanced_inward, balanced_outward

def inward(src: str, pos: int):
    return [tag.to_json() for tag in balanced_inward(src, pos)]

def outward(src: str, pos: int):
    return [tag.to_json() for tag in balanced_outward(src, pos)]

def read_file(file: str):
    dirname = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(dirname, file), 'r') as f:
        return f.read(None)


class TestHTMLBalancedModels(unittest.TestCase):
    def test_outward(self):
        doc = read_file('sample.html')

        self.assertEqual(outward(doc, 0), [])

        self.assertEqual(outward(doc, 1), [
            { 'name': 'ul', 'open': [0, 4], 'close': [179, 184] }
        ])

        self.assertEqual(outward(doc, 73), [
            { 'name': 'li', 'open': [71, 75], 'close': [147, 152] },
            { 'name': 'ul', 'open': [0, 4], 'close': [179, 184] }
        ])

        self.assertEqual(outward(doc, 114), [
            { 'name': 'br', 'open': [112, 118] },
            { 'name': 'div', 'open': [78, 83], 'close': [121, 127] },
            { 'name': 'li', 'open': [71, 75], 'close': [147, 152] },
            { 'name': 'ul', 'open': [0, 4], 'close': [179, 184] }
        ])

    def test_inward(self):
        doc = read_file('sample.html')

        self.assertEqual(inward(doc, 0), [
            { 'name': 'ul', 'open': [0, 4], 'close': [179, 184] },
            { 'name': 'li', 'open': [6, 10], 'close': [25, 30] },
            { 'name': 'a', 'open': [10, 21], 'close': [21, 25] }
        ])

        self.assertEqual(inward(doc, 1), [
            { 'name': 'ul', 'open': [0, 4], 'close': [179, 184] },
            { 'name': 'li', 'open': [6, 10], 'close': [25, 30] },
            { 'name': 'a', 'open': [10, 21], 'close': [21, 25] }
        ])

        self.assertEqual(inward(doc, 73), [
            { 'name': 'li', 'open': [71, 75], 'close': [147, 152] },
            { 'name': 'div', 'open': [78, 83], 'close': [121, 127] },
            { 'name': 'img', 'open': [87, 108] }
        ])

        self.assertEqual(inward(doc, 114), [
            { 'name': 'br', 'open': [112, 118] }
        ])
