import unittest
import sys

sys.path.append('../../')

from emmet.css_abbreviation import parse
from .ast import stringify

def expand(abbr: str):
    return ''.join(map(stringify, parse(abbr)))


class TestCSSParser(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(expand('p10!'), 'p: 10 !important;')
        self.assertEqual(expand('p-10-20'), 'p: -10 20;')
        self.assertEqual(expand('p-10%-20--30'), 'p: -10% -20 -30;')
        self.assertEqual(expand('p.5'), 'p: 0.5;')
        self.assertEqual(expand('p-.5'), 'p: -0.5;')
        self.assertEqual(expand('p.1.2.3'), 'p: 0.1 0.2 0.3;')
        self.assertEqual(expand('p.1-.2.3'), 'p: 0.1 0.2 0.3;')
        self.assertEqual(expand('10'), '?: 10;')
        self.assertEqual(expand('.1'), '?: 0.1;')

    def test_color(self):
        self.assertEqual(expand('c#'), 'c: #000000;')
        self.assertEqual(expand('c#1'), 'c: #111111;')
        self.assertEqual(expand('c#f'), 'c: #ffffff;')
        self.assertEqual(expand('c#a#b#c'), 'c: #aaaaaa #bbbbbb #cccccc;')
        self.assertEqual(expand('c#af'), 'c: #afafaf;')
        self.assertEqual(expand('c#fc0'), 'c: #ffcc00;')
        self.assertEqual(expand('c#11.5'), 'c: rgba(17, 17, 17, 0.5);')
        self.assertEqual(expand('c#.99'), 'c: rgba(0, 0, 0, 0.99);')
        self.assertEqual(expand('c#t'), 'c: transparent;')

    def test_keywords(self):
        self.assertEqual(expand('m:a'), 'm: a;')
        self.assertEqual(expand('m-a'), 'm: a;')
        self.assertEqual(expand('m-abc'), 'm: abc;')
        self.assertEqual(expand('m-a0'), 'm: a 0;')
        self.assertEqual(expand('m-a0-a'), 'm: a 0 a;')

    def test_functions(self):
        self.assertEqual(expand('bg-lg(top,   "red, black",rgb(0, 0, 0) 10%)'), 'bg: lg(top, "red, black", rgb(0, 0, 0) 10%);')
        self.assertEqual(expand('lg(top,   "red, black",rgb(0, 0, 0) 10%)'), '?: lg(top, "red, black", rgb(0, 0, 0) 10%);')

    def test_mixed(self):
        self.assertEqual(expand('bd1-s#fc0'), 'bd: 1 s #ffcc00;')
        self.assertEqual(expand('bd#fc0-1'), 'bd: #ffcc00 1;')
        self.assertEqual(expand('p0+m0'), 'p: 0;m: 0;')
        self.assertEqual(expand('p0!+m0!'), 'p: 0 !important;m: 0 !important;')

    def test_embedded_variables(self):
        self.assertEqual(expand('foo$bar'), 'foo: $bar;')
        self.assertEqual(expand('foo$bar-2'), 'foo: $bar-2;')
        self.assertEqual(expand('foo$bar@bam'), 'foo: $bar @bam;')

    def test_parse_value(self):
        opt = { 'value': True }
        prop = parse('${1:foo} ${2:bar}, baz', opt)[0]
        self.assertEqual(prop.name, None)
        self.assertEqual(len(prop.value), 2)
        self.assertEqual(len(prop.value[0].value), 2)
        self.assertEqual(prop.value[0].value[0].type, 'Field')

        prop = parse('scale3d(${1:x}, ${2:y}, ${3:z})', opt)[0]
        fn = prop.value[0].value[0]
        self.assertEqual(len(prop.value), 1)
        self.assertEqual(len(prop.value[0].value), 1)
        self.assertEqual(fn.type, 'FunctionCall')
        self.assertEqual(fn.name, 'scale3d')
