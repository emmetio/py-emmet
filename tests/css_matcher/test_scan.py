import unittest
import sys

sys.path.append('../../')

from emmet.css_matcher import scan

def tokens(source: str):
    result = []
    scan(source, lambda token_type, start, end, delimiter: result.append([source[start:end], token_type, start, end, delimiter]))
    return result


class TestCSSScanner(unittest.TestCase):
    def test_selectors(self):
        self.assertEqual(tokens('a {}'), [
            ['a', 'selector', 0, 1, 2],
            ['}', 'blockEnd', 3, 4, 3]
        ])
        self.assertEqual(tokens('a { foo: bar; }'), [
            ['a', 'selector', 0, 1, 2],
            ['foo', 'propertyName', 4, 7, 7],
            ['bar', 'propertyValue', 9, 12, 12],
            ['}', 'blockEnd', 14, 15, 14]
        ])
        self.assertEqual(tokens('a { b{} }'), [
            ['a', 'selector', 0, 1, 2],
            ['b', 'selector', 4, 5, 5],
            ['}', 'blockEnd', 6, 7, 6],
            ['}', 'blockEnd', 8, 9, 8]
        ])

        self.assertEqual(tokens('a {:;}'), [
            ['a', 'selector', 0, 1, 2],
            ['}', 'blockEnd', 5, 6, 5]
        ])

        self.assertEqual(tokens('a + b.class[attr="}"] { }'), [
            ['a + b.class[attr="}"]', 'selector', 0, 21, 22],
            ['}', 'blockEnd', 24, 25, 24]
        ])

        self.assertEqual(tokens('a /* b */ { foo: bar; }'), [
            ['a', 'selector', 0, 1, 10],
            ['foo', 'propertyName', 12, 15, 15],
            ['bar', 'propertyValue', 17, 20, 20],
            ['}', 'blockEnd', 22, 23, 22]
        ])

    def test_property(self):
        self.assertEqual(tokens('a'), [
            ['a', 'propertyName', 0, 1, -1]
        ])

        self.assertEqual(tokens('a:b'), [
            ['a', 'propertyName', 0, 1, 1],
            ['b', 'propertyValue', 2, 3, -1]
        ])

        self.assertEqual(tokens('a:b;;'), [
            ['a', 'propertyName', 0, 1, 1],
            ['b', 'propertyValue', 2, 3, 3]
        ])

        self.assertEqual(tokens('a { b: c; d: e; }'), [
            ['a', 'selector', 0, 1, 2],
            ['b', 'propertyName', 4, 5, 5],
            ['c', 'propertyValue', 7, 8, 8],
            ['d', 'propertyName', 10, 11, 11],
            ['e', 'propertyValue', 13, 14, 14],
            ['}', 'blockEnd', 16, 17, 16]
        ])

        self.assertEqual(tokens('a { foo: bar "baz}" ; }'), [
            ['a', 'selector', 0, 1, 2],
            ['foo', 'propertyName', 4, 7, 7],
            ['bar "baz}"', 'propertyValue', 9, 19, 20],
            ['}', 'blockEnd', 22, 23, 22]
        ])

        self.assertEqual(tokens('@media (min-width: 900px) {}'), [
            ['@media (min-width: 900px)', 'selector', 0, 25, 26],
            ['}', 'blockEnd', 27, 28, 27]
        ])

    def test_pseudo_selectors(self):
        self.assertEqual(tokens('\na:hover { foo: bar "baz}" ; }'), [
            ['a:hover', 'selector', 1, 8, 9],
            ['foo', 'propertyName', 11, 14, 14],
            ['bar "baz}"', 'propertyValue', 16, 26, 27],
            ['}', 'blockEnd', 29, 30, 29]
        ])

        self.assertEqual(tokens('a:hover b[title=""] { padding: 10px; }'), [
            ['a:hover b[title=""]', 'selector', 0, 19, 20],
            ['padding', 'propertyName', 22, 29, 29],
            ['10px', 'propertyValue', 31, 35, 35],
            ['}', 'blockEnd', 37, 38, 37]
        ])

        self.assertEqual(tokens('a::before {}'), [
            ['a::before', 'selector', 0, 9, 10],
            ['}', 'blockEnd', 11, 12, 11]
        ])

        self.assertEqual(tokens('a { &::before {  } }'), [
            ['a', 'selector', 0, 1, 2],
            ['&::before', 'selector', 4, 13, 14],
            ['}', 'blockEnd', 17, 18, 17],
            ['}', 'blockEnd', 19, 20, 19]
        ])
