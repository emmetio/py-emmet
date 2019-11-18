import unittest
import sys
import os.path

sys.path.append('../../')

from emmet.action_utils import select_item_css, get_css_section, CSSProperty


def read_file(file: str):
    dirname = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(dirname, file), 'r') as f:
        return f.read(None)


sample = read_file('sample.scss')


class TestCSSActionUtils(unittest.TestCase):
    def test_select_next_item(self):
        self.assertEqual(select_item_css(sample, 0).to_json(), {
            'start': 0,
            'end': 2,
            'ranges': [(0, 2)]
        })

        # `flex: 1 1;`: parse value tokens as well
        self.assertEqual(select_item_css(sample, 2).to_json(), {
            'start': 9,
            'end': 19,
            'ranges': [(9, 19), (15, 18), (15, 16), (17, 18)]
        })

        # `> li` nested selector
        self.assertEqual(select_item_css(sample, 143).to_json(), {
            'start': 148,
            'end': 152,
            'ranges': [(148, 152)]
        })

        # `slot[name="controls"]:empty` top-level selector
        self.assertEqual(select_item_css(sample, 385).to_json(), {
            'start': 387,
            'end': 414,
            'ranges': [(387, 414)]
        })

    def test_select_previous_item(self):
        # list-style-type: none;
        self.assertEqual(select_item_css(sample, 70, True).to_json(), {
            'start': 43,
            'end': 65,
            'ranges': [(43, 65), (60, 64)]
        })

        # border-top: 2px solid transparent;
        self.assertEqual(select_item_css(sample, 206, True).to_json(), {
            'start': 163,
            'end': 197,
            'ranges': [
                (163, 197),
                (175, 196),
                (175, 178),
                (179, 184),
                (185, 196)
            ]
        })

        # > li
        self.assertEqual(select_item_css(sample, 163, True).to_json(), {
            'start': 148,
            'end': 152,
            'ranges': [(148, 152)]
        })

    def test_get_section(self):
        self.assertEqual(get_css_section(sample, 260).to_json(), {
            'start': 257,
            'end': 377,
            'body_start': 269,
            'body_end': 376
        }, '&.selected')

        self.assertEqual(get_css_section(sample, 207).to_json(), {
            'start': 148,
            'end': 383,
            'body_start': 154,
            'body_end': 382
        }, '> li')

    def test_get_section_with_props(self):
        def value(key: str, prop: CSSProperty):
            rng = None

            if key == 'before':
                rng = (prop.before, prop.name[0])
            elif key == 'after':
                rng = (prop.value[1], prop.after)
            elif key == 'name':
                rng = prop.name
            elif key == 'value':
                rng = prop.value


            if rng:
                return substr(rng)

        def substr(rng: tuple):
            return sample[rng[0]:rng[1]]

        section = get_css_section(sample, 207, True)
        prop = section.properties
        self.assertEqual(len(prop), 3)

        self.assertEqual(value('name', prop[0]), 'border-top')
        self.assertEqual(value('value', prop[0]), '2px solid transparent')
        self.assertEqual(value('before', prop[0]), '\n        ')
        self.assertEqual(value('after', prop[0]), ';')
        self.assertEqual([substr(t) for t in prop[0].value_tokens], ['2px', 'solid', 'transparent'])

        self.assertEqual(value('name', prop[1]), 'color')
        self.assertEqual(value('value', prop[1]), '$ok-gray')
        self.assertEqual(value('before', prop[1]), '\n        ')
        self.assertEqual(value('after', prop[1]), ';')
        self.assertEqual([substr(t) for t in prop[1].value_tokens], ['$ok-gray'])

        self.assertEqual(value('name', prop[2]), 'cursor')
        self.assertEqual(value('value', prop[2]), 'pointer')
        self.assertEqual(value('before', prop[2]), '\n        ')
        self.assertEqual(value('after', prop[2]), ';')
        self.assertEqual([substr(t) for t in prop[2].value_tokens], ['pointer'])

        section = get_css_section(sample, 450, True)
        prop = section.properties
        self.assertEqual(len(prop), 2)

        self.assertEqual(value('name', prop[0]), 'padding')
        self.assertEqual(value('value', prop[0]), '10px')
        self.assertEqual(value('before', prop[0]), '\n    ')
        self.assertEqual(value('after', prop[0]), ';')

        self.assertEqual(value('name', prop[1]), 'color')
        self.assertEqual(value('value', prop[1]), '#000')
        self.assertEqual(value('before', prop[1]), '\n    ')
        self.assertEqual(value('after', prop[1]), ';')

