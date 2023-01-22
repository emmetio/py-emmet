import unittest
import sys

sys.path.append('../')

from emmet import expand_stylesheet, parse_stylesheet_snippets, Config
from emmet.stylesheet import CSSAbbreviationScope
from emmet.stylesheet.score import calculate_score as score

def field(index: int, placeholder: str, **kwargs):
    if placeholder:
        return '${%d:%s}' % (index, placeholder)
    return '${%d}' % index

default_config = Config({
    'type': 'stylesheet',
    'options': {
        'output.field': field
    },
    'snippets': {
        'mten': 'margin: 10px;',
        'fsz': 'font-size',
        'gt': 'grid-template: repeat(2,auto) / repeat(auto-fit, minmax(250px, 1fr))',
        'bxsh': 'box-shadow: var(--bxsh-${1})'
    },
    'cache': {}
})

def expand(abbr: str, config=default_config):
    return expand_stylesheet(abbr, config)


def pick(abbr: str, items: list):
    items = map(lambda item: { 'item': item, 'score': score(abbr, item, True) }, items)
    items = list(filter(lambda item: item['score'] > 0, items))
    items.sort(key=lambda item: item['score'], reverse=True)

    if items:
        return items[0]['item']


class TestStylesheetScoring(unittest.TestCase):
    def test_compare_scores(self):
        self.assertEqual(score('aaa', 'aaa'), 1)
        self.assertEqual(score('baa', 'aaa'), 0)

        self.assertFalse(score('b', 'aaa'))
        self.assertTrue(score('a', 'aaa'))
        self.assertTrue(score('a', 'abc'))
        self.assertTrue(score('ac', 'abc'))
        self.assertTrue(score('a', 'aaa') < score('aa', 'aaa'))
        self.assertTrue(score('ab', 'abc') > score('ab', 'acb'))

        # acronym bonus
        self.assertTrue(score('ab', 'a-b') > score('ab', 'acb'))

    def test_pick_padding_or_position(self):
        items = ['p', 'pb', 'pl', 'pos', 'pa', 'oa', 'soa', 'pr', 'pt']

        self.assertEqual(pick('p', items), 'p')
        self.assertEqual(pick('poa', items), 'pos')


class TestStylesheetAbbreviations(unittest.TestCase):
    def test_keyword(self):
        self.assertEqual(expand('bd1-s'), 'border: 1px solid;')
        self.assertEqual(expand('dib'), 'display: inline-block;')
        self.assertEqual(expand('bxsz'), 'box-sizing: ${1:border-box};')
        self.assertEqual(expand('bxz'), 'box-sizing: ${1:border-box};')
        self.assertEqual(expand('bxzc'), 'box-sizing: content-box;')
        self.assertEqual(expand('fl'), 'float: ${1:left};')
        self.assertEqual(expand('fll'), 'float: left;')

        self.assertEqual(expand('pos'), 'position: ${1:relative};')
        self.assertEqual(expand('poa'), 'position: absolute;')
        self.assertEqual(expand('por'), 'position: relative;')
        self.assertEqual(expand('pof'), 'position: fixed;')
        self.assertEqual(expand('pos-a'), 'position: absolute;')

        self.assertEqual(expand('m'), 'margin: ${0};')
        self.assertEqual(expand('m0'), 'margin: 0;')

        # use `auto` as global keyword
        self.assertEqual(expand('m0-a'), 'margin: 0 auto;')
        self.assertEqual(expand('m-a'), 'margin: auto;')

        self.assertEqual(expand('bg'), 'background: ${1:#000};')

        self.assertEqual(expand('bd'), 'border: ${1:1px} ${2:solid} ${3:#000};')
        self.assertEqual(expand('bd0-s#fc0'), 'border: 0 solid #fc0;')
        self.assertEqual(expand('bd0-dd#fc0'), 'border: 0 dot-dash #fc0;')
        self.assertEqual(expand('bd0-h#fc0'), 'border: 0 hidden #fc0;')

        self.assertEqual(expand('trf-trs'), 'transform: translate(${1:x}, ${2:y});')

        # https://github.com/emmetio/emmet/issues/647
        self.assertEqual(expand('gtc'), 'grid-template-columns: repeat(${0});')
        self.assertEqual(expand('gtr'), 'grid-template-rows: repeat(${0});')

        self.assertEqual(expand('lis:n'), 'list-style: none;')
        self.assertEqual(expand('list:n'), 'list-style-type: none;')
        self.assertEqual(expand('bdt:n'), 'border-top: none;')
        self.assertEqual(expand('bgi:n'), 'background-image: none;')
        self.assertEqual(expand('q:n'), 'quotes: none;')

        # Custom properties
        # https://github.com/emmetio/emmet/issues/692
        self.assertEqual(expand('bxsh'), 'box-shadow: var(--bxsh-${1});')

    def test_numeric(self):
        self.assertEqual(expand('p0'), 'padding: 0;', 'No unit for 0')
        self.assertEqual(expand('p10'), 'padding: 10px;', '`px` unit for integers')
        self.assertEqual(expand('p.4'), 'padding: 0.4em;', '`em` for floats')
        self.assertEqual(expand('fz10'), 'font-size: 10px;', '`px` for integers')
        self.assertEqual(expand('fz1.'), 'font-size: 1em;', '`em` for explicit float')
        self.assertEqual(expand('p10p'), 'padding: 10%;', 'unit alias')
        self.assertEqual(expand('z10'), 'z-index: 10;', 'Unitless property')
        self.assertEqual(expand('p10r'), 'padding: 10rem;', 'unit alias')
        self.assertEqual(expand('mten'), 'margin: 10px;', 'Ignore terminating `;` in snippet')

        # https://github.com/microsoft/vscode/issues/59951
        self.assertEqual(expand('fz'), 'font-size: ${0};')
        self.assertEqual(expand('fz12'), 'font-size: 12px;')
        self.assertEqual(expand('fsz'), 'font-size: ${0};')
        self.assertEqual(expand('fsz12'), 'font-size: 12px;')
        self.assertEqual(expand('fs'), 'font-style: ${1:italic};')

        # https://github.com/emmetio/emmet/issues/558
        self.assertEqual(expand('us'), 'user-select: none;')

        # https://github.com/emmetio/emmet/issues/558
        self.assertEqual(expand('us'), 'user-select: none;');

        # https://github.com/microsoft/vscode/issues/105697
        self.assertEqual(expand('opa1'), 'opacity: 1;', 'Unitless property');
        self.assertEqual(expand('opa.1'), 'opacity: 0.1;', 'Unitless property');
        self.assertEqual(expand('opa.a'), 'opacity: .a;', 'Unitless property');

    def test_numeric_with_format(self):
        config = Config({
            'type': 'stylesheet',
            'options': {
                'stylesheet.intUnit': 'pt',
                'stylesheet.floatUnit': 'vh',
                'stylesheet.unitAliases': {
                    'e': 'em',
                    'p': '%',
                    'x': 'ex',
                    'r': ' / @rem'
                }
            }
        })
        self.assertEqual(expand('p0', config), 'padding: 0;', 'No unit for 0')
        self.assertEqual(expand('p10', config), 'padding: 10pt;', '`pt` unit for integers')
        self.assertEqual(expand('p.4', config), 'padding: 0.4vh;', '`vh` for floats')
        self.assertEqual(expand('p10p', config), 'padding: 10%;', 'unit alias')
        self.assertEqual(expand('z10', config), 'z-index: 10;', 'Unitless property')
        self.assertEqual(expand('p10r', config), 'padding: 10 / @rem;', 'unit alias')

    def test_important(self):
        self.assertEqual(expand('!'), '!important')
        self.assertEqual(expand('p!'), 'padding: ${0} !important;')
        self.assertEqual(expand('p0!'), 'padding: 0 !important;')

    def test_color(self):
        self.assertEqual(expand('c'), 'color: ${1:#000};')
        self.assertEqual(expand('c#'), 'color: #000;')
        self.assertEqual(expand('c#f.5'), 'color: rgba(255, 255, 255, 0.5);')
        self.assertEqual(expand('c#f.5!'), 'color: rgba(255, 255, 255, 0.5) !important;')
        self.assertEqual(expand('bgc'), 'background-color: #${1:fff};')
        self.assertEqual(expand('bgc#f0'), 'background-color: #f0f0f0;')
        self.assertEqual(expand('bgc#f1'), 'background-color: #f1f1f1;')

    def test_snippets(self):
        self.assertEqual(expand('@k'), '@keyframes ${1:identifier} {\n\t${2}\n}')
        self.assertEqual(expand('@'), '@media ${1:screen} {\n\t${0}\n}')

        # Insert value into snippet fields
        self.assertEqual(expand('@k-name'), '@keyframes name {\n\t${2}\n}')
        self.assertEqual(expand('@k-name10'), '@keyframes name {\n\t10\n}')
        self.assertEqual(expand('gt'), 'grid-template: repeat(2, auto) / repeat(auto-fit, minmax(250px, 1fr));')

    def test_multiple_properties(self):
        self.assertEqual(expand('p10+m10-20'), 'padding: 10px;\nmargin: 10px 20px;')
        self.assertEqual(expand('p+bd'), 'padding: ${0};\nborder: ${1:1px} ${2:solid} ${3:#000};')

    def test_functions(self):
        self.assertEqual(expand('trf-s(2)'), 'transform: scale(2, ${2:y});')
        self.assertEqual(expand('trf-s(2, 3)'), 'transform: scale(2, 3);')

    def test_case_insensitive_match(self):
        self.assertEqual(expand('trf:rx'), 'transform: rotateX(${1:angle});')

    def test_gradient_resolver(self):
        self.assertEqual(expand('lg'), 'background-image: linear-gradient(${0});')
        self.assertEqual(expand('lg(to right, #0, #f00.5)'), 'background-image: linear-gradient(to right, #000, rgba(255, 0, 0, 0.5));')

    # This example is useless: it’s unexpected to receive `align-self: unset`
    # for `auto` snippet
    # def test_min_score(self):
    #     self.assertEqual(expand('auto', Config({
    #         'type': 'stylesheet',
    #         'options': { 'stylesheet.fuzzySearchMinScore': 0 }
    #     })), 'align-self: unset;')
    #     self.assertEqual(expand('auto', Config({
    #         'type': 'stylesheet',
    #         'options': { 'stylesheet.fuzzySearchMinScore': 0.3 }
    #     })), 'auto: ;')

    def test_css_in_js(self):
        config = Config({
            'type': 'stylesheet',
            'options': {
                'stylesheet.json': True,
                'stylesheet.between': ': '
            }
        })

        self.assertEqual(expand('p10+mt10-20', config), 'padding: 10,\nmarginTop: \'10px 20px\',')
        self.assertEqual(expand('bgc', config), 'backgroundColor: \'#fff\',')

    def test_resolve_context_value(self):
        config = Config({
            'type': 'stylesheet',
            'context': { 'name': 'align-content' }
        })

        self.assertEqual(expand('s', config), 'start')
        self.assertEqual(expand('a', config), 'auto')

    def test_limit_snippets_by_scope(self):
        section_scope = Config({
            'type': 'stylesheet',
            'context': { 'name': CSSAbbreviationScope.Section },
            'snippets': {
                'mten': 'margin: 10px;',
                'fsz': 'font-size',
                'myCenterAwesome': 'body {\n\tdisplay: grid;\n}'
            }
        })
        property_scope = Config({
            'type': 'stylesheet',
            'context': { 'name': CSSAbbreviationScope.Property },
            'snippets': {
                'mten': 'margin: 10px;',
                'fsz': 'font-size',
                'myCenterAwesome': 'body {\n\tdisplay: grid;\n}'
            }
        })

        self.assertEqual(expand('m', section_scope), 'body {\n\tdisplay: grid;\n}')
        self.assertEqual(expand('b', section_scope), '')
        self.assertEqual(expand('m', property_scope), 'margin: ;')
