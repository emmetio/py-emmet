import unittest
import sys
import re

sys.path.append('../')

from emmet import expand

def word_count(text: str):
    return len(text.split(' '))


class TestLoremIpsum(unittest.TestCase):
    def test_single(self):
        output = expand('lorem')
        self.assertTrue(re.match(r'^Lorem,?\sipsum', output))
        self.assertTrue(word_count(output) > 20)

        output = expand('lorem5')
        self.assertTrue(re.match(r'^Lorem,?\sipsum', output))
        self.assertEqual(word_count(output), 5)

        output = expand('lorem5-10')
        self.assertTrue(re.match(r'^Lorem,?\sipsum', output))
        self.assertTrue(5 <= word_count(output) <= 10)

        output = expand('loremru4')
        self.assertTrue(re.match(r'^Далеко-далеко,?\sза,?\sсловесными', output))
        self.assertEqual(word_count(output), 4)

        output = expand('p>lorem')
        self.assertTrue(re.match(r'^<p>Lorem,?\sipsum', output))

        # https://github.com/emmetio/expand-abbreviation/issues/24
        output = expand('(p)lorem2')
        self.assertTrue(re.match(r'^<p><\/p>\nLorem,?\sipsum', output))

        output = expand('p(lorem10)')
        self.assertTrue(re.match(r'^<p><\/p>\nLorem,?\sipsum', output))

    def test_multiple(self):
        output = expand('lorem6*3')
        lines = output.splitlines()
        self.assertTrue(re.match(r'^Lorem,?\sipsum', output))
        self.assertEqual(len(lines), 3)

        output = expand('lorem6*2')
        lines = output.splitlines()
        self.assertTrue(re.match(r'^Lorem,?\sipsum', output))
        self.assertEqual(len(lines), 2)

        output = expand('p*3>lorem')
        lines = output.splitlines()
        self.assertTrue(re.match(r'^<p>Lorem,?\sipsum', lines[0]))
        self.assertFalse(re.match(r'^<p>Lorem,?\sipsum', lines[1]))

        output = expand('ul>lorem5*3', { 'options': { 'output.indent': '' } })
        lines = output.splitlines()
        self.assertEqual(len(lines), 5)
        self.assertTrue(re.match(r'^^<li>Lorem,?\sipsum', lines[1]))
        self.assertFalse(re.match(r'^^<li>Lorem,?\sipsum', lines[2]))
