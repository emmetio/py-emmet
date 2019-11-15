import unittest
import sys

sys.path.append('../')

from emmet import expand_stylesheet, parse_stylesheet_snippets, Config
from emmet.stylesheet.score import calculate_score as score

def field(index: int, placeholder: str, **kwargs):
    if placeholder:
        return '${%d:%s}' % (index, placeholder)
    return '${%s}' % placeholder

default_config = Config({
    'type': 'stylesheet',
    'options': {
        'output.field': field
    },
    'snippets': {
        'mten': 'margin: 10px;',
        'fsz': 'font-size'
    }
})
snippets = parse_stylesheet_snippets(default_config.snippets)

def expand(abbr: str, config=default_config):
    global snippets
    return expand_stylesheet(abbr, config, snippets)


def pick(abbr: str, items: list):
    items = map(lambda item: { 'item': item, 'score': score(abbr, item) }, items)
    items = list(filter(lambda item: item['score'] > 0, items))
    items.sort(key=lambda item: item['score'])

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

    # def test_pick_padding_or_position(self):
    #     items = ['p', 'pb', 'pl', 'pos', 'pa', 'oa', 'soa', 'pr', 'pt']

    #     self.assertEqual(pick('p', items), 'p')
    #     self.assertEqual(pick('poa', items), 'pos')
