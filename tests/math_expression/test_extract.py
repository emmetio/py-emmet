import unittest
import sys

sys.path.append('../../')

from emmet.math_expression import extract

class TestMathExtract(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(extract('1'), (0, 1))
        self.assertEqual(extract('10'), (0, 2))
        self.assertEqual(extract('123'), (0, 3))
        self.assertEqual(extract('0.1'), (0, 3))
        self.assertEqual(extract('.1'), (0, 2))
        self.assertEqual(extract('.123'), (0, 4))

        # mixed content
        self.assertEqual(extract('foo123'), (3, 6))
        self.assertEqual(extract('.1.2.3'), (3, 6))
        self.assertEqual(extract('1.2.3'), (2, 5))
        self.assertEqual(extract('foo2 * (3 + 1)'), (3, 14))
        self.assertEqual(extract('bar.(2 * (3 + 1))'), (4, 17))
        self.assertEqual(extract('test: 1+2'), (6, 9))

    def test_look_ahead(self):
        self.assertEqual(extract('foo2 * (3 + 1)', 13), (3, 14))
        self.assertEqual(extract('bar.(2 * (3 + 1))', 15), (4, 17))
        self.assertEqual(extract('bar.(2 * (3 + 1) )', 15), (4, 18))
