import unittest
import sys

sys.path.append('../../')

from emmet.css_matcher import split_value

def tokens(value: str):
    return [value[r[0]:r[1]] for r in split_value(value)]


class TestCSSParser(unittest.TestCase):
    def test_split_value(self):
        self.assertEqual(tokens('10px 20px'), ['10px', '20px'])
        self.assertEqual(tokens(' 10px   20px  '), ['10px', '20px'])
        self.assertEqual(tokens('10px, 20px'), ['10px', '20px'])
        self.assertEqual(tokens('20px'), ['20px'])
        self.assertEqual(tokens('no-repeat, 10px - 5'), ['no-repeat', '10px', '5'])
        self.assertEqual(tokens('url("foo bar") no-repeat'), ['url("foo bar")', 'no-repeat'])
        self.assertEqual(tokens('--my-prop'), ['--my-prop'])
        self.assertEqual(tokens('calc(100% - 80px)'), ['calc(100% - 80px)'])
