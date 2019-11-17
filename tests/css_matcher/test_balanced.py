import unittest
import sys
import os.path

sys.path.append('../../')

from emmet.css_matcher import balanced_inward as inward, balanced_outward as outward

def read_file(file: str):
    dirname = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(dirname, file), 'r') as f:
        return f.read(None)

code = read_file('sample.scss')

class TestCSSBalancedModels(unittest.TestCase):
    def test_outward(self):
        self.assertEqual(outward(code, 140), [
            (145, 149),
            (137, 150),
            (110, 182),
            (75, 192),
            (61, 198),
            (43, 281),
            (0, 283)
        ])

        self.assertEqual(outward(code, 77), [
            (110, 182),
            (75, 192),
            (61, 198),
            (43, 281),
            (0, 283)
        ])

        self.assertEqual(outward(code, 277), [
            (273, 281),
            (43, 281),
            (0, 283)
        ])

    def test_inward(self):
        self.assertEqual(inward(code, 62), [
            (61, 198),
            (75, 192),
            (110, 182),
            (110, 124),
            (119, 123)
        ])

        self.assertEqual(inward(code, 46), [
            (43, 56),
            (51, 55)
        ])

        self.assertEqual(inward(code, 206), [
            (204, 267),
            (218, 261),
            (218, 236),
            (231, 235)
        ])

        self.assertEqual(inward(code, 333), [
            (330, 336),
            (334, 335)
        ])
