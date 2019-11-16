import unittest
import sys

sys.path.append('../../')

from emmet.html_matcher import scan, ElementType, ScannerOptions

def get_tags(code: str, opt={}):
    tags = []
    options = ScannerOptions(opt)
    def scan_callback(name: str, elem_type: ElementType, start: int, end: int):
        tags.append([name, elem_type, start, end])
    scan(code, scan_callback, options.special)
    return tags


class TestHTMLMatchScan(unittest.TestCase):
    def test_open_tag(self):
        self.assertEqual(get_tags('<a>'), [['a', ElementType.Open, 0, 3]])
        self.assertEqual(get_tags('foo<a>'), [['a', ElementType.Open, 3, 6]])
        self.assertEqual(get_tags('<a>foo'), [['a', ElementType.Open, 0, 3]])
        self.assertEqual(get_tags('<foo-bar>'), [['foo-bar', ElementType.Open, 0, 9]])
        self.assertEqual(get_tags('<foo:bar>'), [['foo:bar', ElementType.Open, 0, 9]])
        self.assertEqual(get_tags('<foo_bar>'), [['foo_bar', ElementType.Open, 0, 9]])
        self.assertEqual(get_tags('<=>'), [])
        self.assertEqual(get_tags('<1>'), [])

        # Tag with attributes
        self.assertEqual(get_tags('<a href="">'), [['a', ElementType.Open, 0, 11]])
        self.assertEqual(get_tags('<a foo bar>'), [['a', ElementType.Open, 0, 11]])
        self.assertEqual(get_tags('<a a={test}>'), [['a', ElementType.Open, 0, 12]])
        self.assertEqual(get_tags('<a [ng-for]={test}>'), [['a', ElementType.Open, 0, 19]])
        self.assertEqual(get_tags('<a a=b c {foo}>'), [['a', ElementType.Open, 0, 15]])

    def test_self_closing_tags(self):
        self.assertEqual(get_tags('<a/>foo'), [['a', ElementType.SelfClose, 0, 4]])
        self.assertEqual(get_tags('<a />foo'), [['a', ElementType.SelfClose, 0, 5]])
        self.assertEqual(get_tags('<a a=b c {foo}/>'), [['a', ElementType.SelfClose, 0, 16]])

    def test_close_tag(self):
        self.assertEqual(get_tags('foo</a>'), [['a', ElementType.Close, 3, 7]])
        self.assertEqual(get_tags('</a>foo'), [['a', ElementType.Close, 0, 4]])
        self.assertEqual(get_tags('</a s>'), [])
        self.assertEqual(get_tags('</a >'), [])

    def test_special_tags(self):
        self.assertEqual(get_tags('<a>foo</a><style><b></style><c>bar</c>'), [
            ['a', ElementType.Open, 0, 3],
            ['a', ElementType.Close, 6, 10],
            ['style', ElementType.Open, 10, 17],
            ['style', ElementType.Close, 20, 28],
            ['c', ElementType.Open, 28, 31],
            ['c', ElementType.Close, 34, 38]
        ])

        self.assertEqual(get_tags('<script><a></script><script type="text/x-foo"><b></script><script type="javascript"><c></script>'), [
            ['script', ElementType.Open, 0, 8],
            ['script', ElementType.Close, 11, 20],
            ['script', ElementType.Open, 20, 46],
            ['b', ElementType.Open, 46, 49],
            ['script', ElementType.Close, 49, 58],
            ['script', ElementType.Open, 58, 84],
            ['script', ElementType.Close, 87, 96],
        ])

    def test_cdata(self):
        self.assertEqual(get_tags('<a><![CDATA[<foo /><bar>]]><b>'), [
            ['a', ElementType.Open, 0, 3],
            ['b', ElementType.Open, 27, 30]
        ])

        # Consume unclosed: still a CDATA
        self.assertEqual(get_tags('<a><![CDATA[<foo /><bar><b>'), [
            ['a', ElementType.Open, 0, 3],
        ])

    def test_comments(self):
        self.assertEqual(get_tags('<a><!-- <foo /><bar> --><b>'), [
            ['a', ElementType.Open, 0, 3],
            ['b', ElementType.Open, 24, 27]
        ])

        # Consume unclosed: still a comment
        self.assertEqual(get_tags('<a><!-- <foo /><bar><b>'), [
            ['a', ElementType.Open, 0, 3],
        ])
