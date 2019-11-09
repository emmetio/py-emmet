import unittest
import sys

sys.path.append('../../')
from . import stringify_node
from emmet.abbreviation import parse as parser

def parse(abbr: str, options={}):
    return stringify_node(parser(abbr, options))


class TestAbbreviationConverter(unittest.TestCase):
    def test_basics(self):
        self.assertEqual(parse('ul>li.item$*3'), '<ul><li*3@0 class="item1"></li><li*3@1 class="item2"></li><li*3@2 class="item3"></li></ul>')
        self.assertEqual(parse('ul>li.item$*', { 'text': ['foo$', 'bar$'] }), '<ul><li*2@0 class="item1">foo$</li><li*2@1 class="item2">bar$</li></ul>')
        self.assertEqual(parse('ul>li[class=$#]{item $}*', { 'text': ['foo$', 'bar$'] }), '<ul><li*2@0 class="foo$">item 1</li><li*2@1 class="bar$">item 2</li></ul>')
        self.assertEqual(parse('ul>li.item$*'), '<ul><li*1@0 class="item1"></li></ul>')
        self.assertEqual(parse('ul>li.item$*', { 'text': ['foo.bar', 'hello.world'] }), '<ul><li*2@0 class="item1">foo.bar</li><li*2@1 class="item2">hello.world</li></ul>')

        self.assertEqual(parse('p{hi}', { 'text': ['hello'] }), '<p>hihello</p>')
        self.assertEqual(parse('p*{hi}', { 'text': ['1', '2'] }), '<p*2@0>hi1</p><p*2@1>hi2</p>')
        self.assertEqual(parse('div>p+p{hi}', { 'text': ['hello'] }), '<div><p></p><p>hihello</p></div>')

        self.assertEqual(parse('html[lang=${lang}]'), '<html lang="lang"></html>')
        self.assertEqual(parse('div{[}+a{}'), '<div>[</div><a></a>')

    def test_unroll(self):
        self.assertEqual(parse('a>(b>c)+d'), '<a><b><c></c></b><d></d></a>')
        self.assertEqual(parse('(a>b)+(c>d)'), '<a><b></b></a><c><d></d></c>')
        self.assertEqual(parse('a>((b>c)(d>e))f'), '<a><b><c></c></b><d><e></e></d><f></f></a>')
        self.assertEqual(parse('a>((((b>c))))+d'), '<a><b><c></c></b><d></d></a>')
        self.assertEqual(parse('a>(((b>c))*4)+d'), '<a><b*4@0><c></c></b><b*4@1><c></c></b><b*4@2><c></c></b><b*4@3><c></c></b><d></d></a>')
        self.assertEqual(parse('(div>dl>(dt+dd)*2)'), '<div><dl><dt*2@0></dt><dd*2@0></dd><dt*2@1></dt><dd*2@1></dd></dl></div>')

        self.assertEqual(parse('a*2>b*3'), '<a*2@0><b*3@0></b><b*3@1></b><b*3@2></b></a><a*2@1><b*3@0></b><b*3@1></b><b*3@2></b></a>')
        self.assertEqual(parse('a>(b+c)*2'), '<a><b*2@0></b><c*2@0></c><b*2@1></b><c*2@1></c></a>')
        self.assertEqual(parse('a>(b+c)*2+(d+e)*2'), '<a><b*2@0></b><c*2@0></c><b*2@1></b><c*2@1></c><d*2@0></d><e*2@0></e><d*2@1></d><e*2@1></e></a>')

        # Should move `<div>` as sibling of `{foo}`
        self.assertEqual(parse('p>{foo}>div'), '<p><?>foo</?><div></div></p>')
        self.assertEqual(parse('p>{foo ${0}}>div'), '<p><?>foo ${0}<div></div></?></p>')

    def test_limit_unroll(self):
        # Limit amount of repeated elements
        self.assertEqual(parse('a*10', { 'max_repeat': 5 }), '<a*10@0></a><a*10@1></a><a*10@2></a><a*10@3></a><a*10@4></a>')
        self.assertEqual(parse('a*10'), '<a*10@0></a><a*10@1></a><a*10@2></a><a*10@3></a><a*10@4></a><a*10@5></a><a*10@6></a><a*10@7></a><a*10@8></a><a*10@9></a>')
        self.assertEqual(parse('a*3>b*3', { 'max_repeat': 5 }), '<a*3@0><b*3@0></b><b*3@1></b><b*3@2></b></a><a*3@1><b*3@0></b></a>')

    def test_parent_repeater(self):
        self.assertEqual(parse('a$*2>b$*3/'), '<a1*2@0><b1*3@0 /><b2*3@1 /><b3*3@2 /></a1><a2*2@1><b1*3@0 /><b2*3@1 /><b3*3@2 /></a2>')
        self.assertEqual(parse('a$*2>b$@^*3/'), '<a1*2@0><b1*3@0 /><b2*3@1 /><b3*3@2 /></a1><a2*2@1><b4*3@0 /><b5*3@1 /><b6*3@2 /></a2>')
