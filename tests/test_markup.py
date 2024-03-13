import unittest
import sys

sys.path.append('../')

from emmet.config import Config
from emmet.markup import parse
from .stringify import stringify_node

default_config = Config()
bem = Config({ 'options': { 'bem.enabled': True }, 'cache': {} })

def expand(abbr: str, config=default_config):
    return stringify_node(parse(abbr, config))


class TestMarkupAbbreviation(unittest.TestCase):
    def test_implicit_tags(self):
        self.assertEqual(expand('.'), '<div class=""></div>')
        self.assertEqual(expand('.foo>.bar'), '<div class="foo"><div class="bar"></div></div>')
        self.assertEqual(expand('p.foo>.bar'), '<p class="foo"><span class="bar"></span></p>')
        self.assertEqual(expand('ul>.item*2'), '<ul><li*2@0 class="item"></li><li*2@1 class="item"></li></ul>')
        self.assertEqual(expand('table>.row>.cell'), '<table><tr class="row"><td class="cell"></td></tr></table>')
        self.assertEqual(expand('{test}'), 'test')
        self.assertEqual(expand('.{test}'), '<div class="">test</div>')
        self.assertEqual(expand('ul>.item$*2'), '<ul><li*2@0 class="item1"></li><li*2@1 class="item2"></li></ul>')

    def test_xsl(self):
        config = Config({ 'syntax': 'xsl' })
        self.assertEqual(expand('xsl:variable[select]', config), '<xsl:variable select=""></xsl:variable>')
        self.assertEqual(expand('xsl:with-param[select]', config), '<xsl:with-param select=""></xsl:with-param>')
        self.assertEqual(expand('xsl:variable[select]>div', config), '<xsl:variable><div></div></xsl:variable>')
        self.assertEqual(expand('xsl:with-param[select]{foo}', config), '<xsl:with-param>foo</xsl:with-param>')

class TestLabelPreprocessor(unittest.TestCase):
    def test_label(self):
        self.assertEqual(expand('label>input'), '<label><input type="${1:text}" /></label>')
        self.assertEqual(expand('label>inp'), '<label><input type="${1:text}" name="${1}" /></label>')
        self.assertEqual(expand('label>span>input'), '<label><span><input type="${1:text}" /></span></label>')
        self.assertEqual(expand('label+inp'), '<label for=""></label><input type="${1:text}" name="${1}" id="${1}" />')

class TestBEMTransform(unittest.TestCase):
    def test_modifiers(self):
        self.assertEqual(expand('div.b_m', bem), '<div class="b b_m"></div>')
        self.assertEqual(expand('div.b._m', bem), '<div class="b b_m"></div>')
        self.assertEqual(expand('div.b_m1._m2', bem), '<div class="b b_m1 b_m2"></div>')
        self.assertEqual(expand('div.b>div._m', bem), '<div class="b"><div class="b b_m"></div></div>')
        self.assertEqual(expand('div.b>div._m1>div._m2', bem), '<div class="b"><div class="b b_m1"><div class="b b_m2"></div></div></div>')

        # classnames with -
        self.assertEqual(expand('div.b>div._m1-m2', bem), '<div class="b"><div class="b b_m1-m2"></div></div>')

    def test_elements(self):
        self.assertEqual(expand('div.b>div.-e', bem), '<div class="b"><div class="b__e"></div></div>')
        self.assertEqual(expand('div.b>div.---e', bem), '<div class="b"><div class="b__e"></div></div>')
        self.assertEqual(expand('div.b>div.-e>div.-e', bem), '<div class="b"><div class="b__e"><div class="b__e"></div></div></div>')
        self.assertEqual(expand('div', bem), '<div></div>', 'Fixes bug with empty class')

        # get block name from proper ancestor
        self.assertEqual(expand('div.b1>div.b2_m1>div.-e1+div.---e2_m2', bem),
            '<div class="b1"><div class="b2 b2_m1"><div class="b2__e1"></div><div class="b1__e2 b1__e2_m2"></div></div></div>')

        # class names with -
        self.assertEqual(expand('div.b>div.-m1-m2', bem), '<div class="b"><div class="b__m1-m2"></div></div>')

        # class names with _
        self.assertEqual(expand('div.b_m_o', bem), '<div class="b b_m_o"></div>')

    def test_customize_modifier(self):
        conf = Config({
            'options': {
                'bem.enabled': True,
                'bem.element': '-',
                'bem.modifier': '__'
            }
        })
        self.assertEqual(expand('div.b_m', conf), '<div class="b b__m"></div>')
        self.assertEqual(expand('div.b._m', conf), '<div class="b b__m"></div>')

    def test_multiple_classes(self):
        self.assertEqual(expand('div.b_m.c', bem), '<div class="b b_m c"></div>')
        self.assertEqual(expand('div.b>div._m.c', bem), '<div class="b"><div class="b b_m c"></div></div>')
        self.assertEqual(expand('div.b>div.-m.c', bem), '<div class="b"><div class="b__m c"></div></div>')

    def test_parent_context(self):
        conf = Config({
            'context': { 'name': 'div', 'attributes': { 'class': 'bl' } },
            'options': { 'bem.enabled': True }
        })
        self.assertEqual(expand('.-e_m', conf), '<div class="bl__e bl__e_m"></div>')
