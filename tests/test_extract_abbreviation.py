import unittest
import sys

sys.path.append('../')

from emmet.extract_abbreviation import extract_abbreviation, is_at_html_tag, ExtractedAbbreviation
from emmet.extract_abbreviation.reader import BackwardScanner
from emmet.extract_abbreviation.is_html import consume_quoted

def extract(abbr: str, options={}):
    caret_pos = abbr.find('|')
    if caret_pos != -1:
        abbr = abbr[0:caret_pos] + abbr[caret_pos + 1:]
    else:
        caret_pos = None

    return extract_abbreviation(abbr, caret_pos, options)


def result(abbreviation: str, location: int, start=None):
    if start is None: start = location
    return ExtractedAbbreviation(abbreviation, location, start, location + len(abbreviation))


class TestExtractAbbreviation(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(extract('.bar'), result('.bar', 0))
        self.assertEqual(extract('.foo .bar'), result('.bar', 5))
        self.assertEqual(extract('.foo @bar'), result('@bar', 5))
        self.assertEqual(extract('.foo img/'), result('img/', 5))
        self.assertEqual(extract('текстdiv'), result('div', 5))
        self.assertEqual(extract('foo div[foo="текст" bar=текст2]'), result('div[foo="текст" bar=текст2]', 4))

        # https://github.com/emmetio/emmet/issues/577
        self.assertEqual(
            extract('table>(tr.prefix-intro>td*1)+(tr.prefix-pro-con>th*1+td*3)+(tr.prefix-key-specs>th[colspan=2]*1+td[colspan=2]*3)+(tr.prefix-key-find-online>th[colspan=2]*1+td*2)'),
            result('table>(tr.prefix-intro>td*1)+(tr.prefix-pro-con>th*1+td*3)+(tr.prefix-key-specs>th[colspan=2]*1+td[colspan=2]*3)+(tr.prefix-key-find-online>th[colspan=2]*1+td*2)', 0))

    def test_abbreviation_with_operators(self):
        self.assertEqual(extract('a foo+bar.baz'), result('foo+bar.baz', 2))
        self.assertEqual(extract('a foo>bar+baz*3'), result('foo>bar+baz*3', 2))

    def test_abbreviation_with_attributes(self):
        self.assertEqual(extract('a foo[bar|]'), result('foo[bar]', 2))
        self.assertEqual(extract('a foo[bar="baz" a b]'), result('foo[bar="baz" a b]', 2))
        self.assertEqual(extract('foo bar[a|] baz'), result('bar[a]', 4))

    def test_tag(self):
        self.assertEqual(extract('<foo>bar[a b="c"]>baz'), result('bar[a b="c"]>baz', 5))
        self.assertEqual(extract('foo>bar'), result('foo>bar', 0))
        self.assertEqual(extract('<foo>bar'), result('bar', 5))
        self.assertEqual(extract('<foo>bar[a="d" b="c"]>baz'), result('bar[a="d" b="c"]>baz', 5))

    def test_stylesheet_abbreviation(self):
        self.assertEqual(extract('foo{bar|}'), result('foo{bar}', 0))
        self.assertEqual(extract('foo{bar|}', { 'type': 'stylesheet' }), result('bar', 4))

    def test_prefixed_extract(self):
        self.assertEqual(extract('<foo>bar[a b="c"]>baz'), result('bar[a b="c"]>baz', 5))
        self.assertEqual(extract('<foo>bar[a b="c"]>baz', { 'prefix': '<' }), result('foo>bar[a b="c"]>baz', 1, 0))
        self.assertEqual(extract('<foo>bar[a b="<"]>baz', { 'prefix': '<' }), result('foo>bar[a b="<"]>baz', 1, 0))
        self.assertEqual(extract('<foo>bar{<}>baz', { 'prefix': '<' }), result('foo>bar{<}>baz', 1, 0))

        # Multiple prefix characters
        self.assertEqual(extract('foo>>>bar[a b="c"]>baz', { 'prefix': '>>>' }), result('bar[a b="c"]>baz', 6, 3))

        # Absent prefix
        self.assertEqual(extract('<foo>bar[a b="c"]>baz', {'prefix': '&&'}), None)

    def test_brackets_inside_curly_braces(self):
        self.assertEqual(extract('foo div{[}+a{}'), result('div{[}+a{}', 4))
        self.assertEqual(extract('div{}}'), None)
        self.assertEqual(extract('div{{}'), result('{}', 4))

    def test_html(self):
        html = lambda s: is_at_html_tag(BackwardScanner(s))

        # simple tag
        self.assertTrue(html('<div>'))
        self.assertTrue(html('<div/>'))
        self.assertTrue(html('<div />'))
        self.assertTrue(html('</div>'))

        # tag with attributes
        self.assertTrue(html('<div foo="bar">'))
        self.assertTrue(html('<div foo=bar>'))
        self.assertTrue(html('<div foo>'))
        self.assertTrue(html('<div a="b" c=d>'))
        self.assertTrue(html('<div a=b c=d>'))
        self.assertTrue(html('<div a=^b$ c=d>'))
        self.assertTrue(html('<div a=b c=^%d]$>'))
        self.assertTrue(html('<div title=привет>'))
        self.assertTrue(html('<div title=привет123>'))
        self.assertTrue(html('<foo-bar>'))

        # invalid tags
        self.assertFalse(html('div>'))
        self.assertFalse(html('<div'))
        self.assertFalse(html('<div привет>'))
        self.assertFalse(html('<div =bar>'))
        self.assertFalse(html('<div foo=>'))
        self.assertFalse(html('[a=b c=d]>'))
        self.assertFalse(html('div[a=b c=d]>'))

    def test_consume_quotes(self):
        s = BackwardScanner(' "foo"')
        self.assertTrue(consume_quoted(s))
        self.assertEqual(s.pos, 1)

        s = BackwardScanner('"foo"')
        self.assertTrue(consume_quoted(s))
        self.assertEqual(s.pos, 0)

        s = BackwardScanner('""')
        self.assertTrue(consume_quoted(s))
        self.assertEqual(s.pos, 0)

        s = BackwardScanner('"a\\\"b"')
        self.assertTrue(consume_quoted(s))
        self.assertEqual(s.pos, 0)

        # don’t eat anything
        s = BackwardScanner('foo')
        self.assertFalse(consume_quoted(s))
        self.assertEqual(s.pos, 3)
