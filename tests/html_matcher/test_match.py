import unittest
import sys

sys.path.append('../../')

from emmet.html_matcher import match

html = """<ul>
    <li><a href="">text <img src="foo.png"><link rel="sample"> <b></b></a></li>
    <li><a href="">text <b></b></a></li>
</ul>"""

xml = """<ul>
    <li><a href="">text
        <img src="foo.png">
            <link rel="sample" />
        </img>
        <b></b>
    </a></li>
    <li><a href="">text <b></b></a></li>
</ul>"""

def attrs(tag):
    return [attr.to_json() for attr in tag.attributes]

class TestHTMLMatch(unittest.TestCase):
    def test_html(self):
        tag = match(html, 12)
        self.assertEqual(tag.name, 'li')
        self.assertEqual(tag.attributes, [])
        self.assertEqual(tag.open, (9, 13))
        self.assertEqual(tag.close, (79, 84))

        # Match `<img>` tag. Since in HTML mode, it should be handled as self-closed
        tag = match(html, 37)
        self.assertEqual(tag.name, 'img')
        self.assertEqual(attrs(tag), [{
            'name': 'src',
            'value': '"foo.png"',
            'name_start': 34,
            'name_end': 37,
            'value_start': 38,
            'value_end': 47
        }])
        self.assertEqual(tag.open, (29, 48))
        self.assertEqual(tag.close, None)

        tag = match(html, 116)
        self.assertEqual(tag.name, 'a')
        self.assertEqual(attrs(tag), [{
            'name': 'href',
            'value': '""',
            'name_start': 96,
            'name_end': 100,
            'value_start': 101,
            'value_end': 103
        }])
        self.assertEqual(tag.open, (93, 104))
        self.assertEqual(tag.close, (116, 120))

    def test_xml(self):
        # Should match <img> tag, since we’re in XML mode, matcher should look
        # for closing `</img>` tag
        tag = match(xml, 42, { 'xml': True })
        self.assertEqual(tag.name, 'img')
        self.assertEqual(attrs(tag), [{
            'name': 'src',
            'value': '"foo.png"',
            'name_start': 42,
            'name_end': 45,
            'value_start': 46,
            'value_end': 55
        }])
        self.assertEqual(tag.open, (37, 56))
        self.assertEqual(tag.close, (99, 105))

        tag = match(xml, 70, { 'xml': True })
        self.assertEqual(tag.name, 'link')
        self.assertEqual(attrs(tag), [{
            'name': 'rel',
            'value': '"sample"',
            'name_start': 75,
            'name_end': 78,
            'value_start': 79,
            'value_end': 87
        }])
        self.assertEqual(tag.open, (69, 90))
        self.assertEqual(tag.close, None)
