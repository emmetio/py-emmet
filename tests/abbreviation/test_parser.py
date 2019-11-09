import unittest
import sys

sys.path.append('../../')

from emmet.abbreviation.parser import parse as parser, TokenScannerException
from emmet.abbreviation.tokenizer import tokenize
from .ast import stringify

def parse(abbr: str, options={}):
    return parser(tokenize(abbr), options)

def string(abbr: str, options={}):
    return stringify(parse(abbr, options))

class TestAbbreviationParser(unittest.TestCase):
    def test_basic_abbreviations(self):
        self.assertEqual(string('p'), '<p></p>')
        self.assertEqual(string('p{text}'), '<p>text</p>')
        self.assertEqual(string('h$'), '<h$></h$>')
        self.assertEqual(string('.nav'), '<? class=nav></?>')
        self.assertEqual(string('div.width1\\/2'), '<div class=width1/2></div>')
        self.assertEqual(string('#sample*3'), '<?*3 id=sample></?>')

        # https://github.com/emmetio/emmet/issues/562
        self.assertEqual(string('li[repeat.for="todo of todoList"]'), '<li repeat.for="todo of todoList"></li>', 'Dots in attribute names')

        self.assertEqual(string('a>b'), '<a><b></b></a>')
        self.assertEqual(string('a+b'), '<a></a><b></b>')
        self.assertEqual(string('a+b>c+d'), '<a></a><b><c></c><d></d></b>')
        self.assertEqual(string('a>b>c+e'), '<a><b><c></c><e></e></b></a>')
        self.assertEqual(string('a>b>c^d'), '<a><b><c></c></b><d></d></a>')
        self.assertEqual(string('a>b>c^^^^d'), '<a><b><c></c></b></a><d></d>')

        self.assertEqual(string('ul.nav[title="foo"]'), '<ul class=nav title="foo"></ul>')

    def test_groups(self):
        self.assertEqual(string('a>(b>c)+d'), '<a>(<b><c></c></b>)<d></d></a>')
        self.assertEqual(string('(a>b)+(c>d)'), '(<a><b></b></a>)(<c><d></d></c>)')
        self.assertEqual(string('a>((b>c)(d>e))f'), '<a>((<b><c></c></b>)(<d><e></e></d>))<f></f></a>')
        self.assertEqual(string('a>((((b>c))))+d'), '<a>((((<b><c></c></b>))))<d></d></a>')
        self.assertEqual(string('a>(((b>c))*4)+d'), '<a>(((<b><c></c></b>))*4)<d></d></a>')
        self.assertEqual(string('(div>dl>(dt+dd)*2)'), '(<div><dl>(<dt></dt><dd></dd>)*2</dl></div>)')
        self.assertEqual(string('a>()'), '<a>()</a>')

    def test_attributes(self):
        self.assertEqual(string('[].foo'), '<? class=foo></?>')
        self.assertEqual(string('[a]'), '<? a></?>')
        self.assertEqual(string('[a b c [d]]'), '<? a b c [d]></?>')
        self.assertEqual(string('[a=b]'), '<? a=b></?>')
        self.assertEqual(string('[a=b c= d=e]'), '<? a=b c d=e></?>')
        self.assertEqual(string('[a=b.c d=тест]'), '<? a=b.c d=тест></?>')
        self.assertEqual(string('[[a]=b (c)=d]'), '<? [a]=b (c)=d></?>')

        # Quoted attribute values
        self.assertEqual(string('[a="b"]'), '<? a="b"></?>')
        self.assertEqual(string('[a="b" c=\'d\' e=""]'), '<? a="b" c=\'d\' e=""></?>')
        self.assertEqual(string('[[a]="b" (c)=\'d\']'), '<? [a]="b" (c)=\'d\'></?>')

        # Mixed quoted
        self.assertEqual(string('[a="foo\'bar" b=\'foo"bar\' c="foo\\\"bar"]'), '<? a="foo\'bar" b=\'foo"bar\' c="foo"bar"></?>')

        # Boolean & implied attributes
        self.assertEqual(string('[a. b.]'), '<? a. b.></?>')
        self.assertEqual(string('[!a !b.]'), '<? !a !b.></?>')

        # Default values
        self.assertEqual(string('["a.b"]'), '<? ?="a.b"></?>')
        self.assertEqual(string('[\'a.b\' "c=d" foo=bar "./test.html"]'), '<? ?=\'a.b\' ?="c=d" foo=bar ?="./test.html"></?>')

        # Expressions as values
        self.assertEqual(string('[foo={1 + 2} bar={fn(1, "foo")}]'), '<? foo={1 + 2} bar={fn(1, "foo")}></?>')

        # Tabstops as unquoted values
        self.assertEqual(string('[name=${1} value=${2:test}]'), '<? name=${1} value=${2:test}></?>')

    def test_marformed_attributes(self):
        self.assertEqual(string('[a'), '<? a></?>')
        self.assertEqual(string('[a={foo]'), '<? a={foo]></?>')

        with self.assertRaises(TokenScannerException):
            string('[a="foo]')

        with self.assertRaises(TokenScannerException):
            string('[a=b=c]')

    def test_elements(self):
        self.assertEqual(string('div'), '<div></div>')
        self.assertEqual(string('div.foo'), '<div class=foo></div>')
        self.assertEqual(string('div#foo'), '<div id=foo></div>')
        self.assertEqual(string('div#foo.bar'), '<div id=foo class=bar></div>')
        self.assertEqual(string('div.foo#bar'), '<div class=foo id=bar></div>')
        self.assertEqual(string('div.foo.bar.baz'), '<div class=foo class=bar class=baz></div>')
        self.assertEqual(string('.foo'), '<? class=foo></?>')
        self.assertEqual(string('#foo'), '<? id=foo></?>')
        self.assertEqual(string('.foo_bar'), '<? class=foo_bar></?>')
        self.assertEqual(string('#foo.bar'), '<? id=foo class=bar></?>')

        # Attribute shorthands
        self.assertEqual(string('.'), '<? class></?>')
        self.assertEqual(string('#'), '<? id></?>')
        self.assertEqual(string('#.'), '<? id class></?>')
        self.assertEqual(string('.#.'), '<? class id class></?>')
        self.assertEqual(string('.a..'), '<? class=a class class></?>')

        # Elements with attributes
        self.assertEqual(string('div[foo=bar]'), '<div foo=bar></div>')
        self.assertEqual(string('div.a[b=c]'), '<div class=a b=c></div>')
        self.assertEqual(string('div[b=c].a'), '<div b=c class=a></div>')
        self.assertEqual(string('div[a=b][c="d"]'), '<div a=b c="d"></div>')
        self.assertEqual(string('[b=c]'), '<? b=c></?>')
        self.assertEqual(string('.a[b=c]'), '<? class=a b=c></?>')
        self.assertEqual(string('[b=c].a#d'), '<? b=c class=a id=d></?>')
        self.assertEqual(string('[b=c]a'), '<? b=c></?><a></a>', 'Do not consume node name after attribute set')

        # Element with text
        self.assertEqual(string('div{foo}'), '<div>foo</div>')
        self.assertEqual(string('{foo}'), '<?>foo</?>')

        # Mixed
        self.assertEqual(string('div.foo{bar}'), '<div class=foo>bar</div>')
        self.assertEqual(string('.foo{bar}#baz'), '<? class=foo id=baz>bar</?>')
        self.assertEqual(string('.foo[b=c]{bar}'), '<? class=foo b=c>bar</?>')

        # Repeated element
        self.assertEqual(string('div.foo*3'), '<div*3 class=foo></div>')
        self.assertEqual(string('.foo*'), '<?* class=foo></?>')
        self.assertEqual(string('.a[b=c]*10'), '<?*10 class=a b=c></?>')
        self.assertEqual(string('.a*10[b=c]'), '<?*10 class=a b=c></?>')
        self.assertEqual(string('.a*10{text}'), '<?*10 class=a>text</?>')

        # Self-closing element
        self.assertEqual(string('div/'), '<div />')
        self.assertEqual(string('.foo/'), '<? class=foo />')
        self.assertEqual(string('.foo[bar]/'), '<? class=foo bar />')
        self.assertEqual(string('.foo/*3'), '<?*3 class=foo />')
        self.assertEqual(string('.foo*3/'), '<?*3 class=foo />')

        with self.assertRaises(TokenScannerException):
            string('/')

    def test_JSX(self):
        opt = { 'jsx': True }
        self.assertEqual(string('foo.bar', opt), '<foo class=bar></foo>')
        self.assertEqual(string('Foo.bar', opt), '<Foo class=bar></Foo>')
        self.assertEqual(string('Foo.Bar', opt), '<Foo.Bar></Foo.Bar>')
        self.assertEqual(string('Foo.', opt), '<Foo class></Foo>')
        self.assertEqual(string('Foo.Bar.baz', opt), '<Foo.Bar class=baz></Foo.Bar>')
        self.assertEqual(string('Foo.Bar.Baz', opt), '<Foo.Bar.Baz></Foo.Bar.Baz>')

        self.assertEqual(string('.{theme.class}', opt), '<? class=theme.class></?>')
        self.assertEqual(string('#{id}', opt), '<? id=id></?>')
        self.assertEqual(string('Foo.{theme.class}', opt), '<Foo class=theme.class></Foo>')
