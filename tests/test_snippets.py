import unittest
import sys

sys.path.append('../')

from emmet import expand
from emmet.config import markup_snippets, xsl_snippets
from emmet.abbreviation import parse


class TestSnippets(unittest.TestCase):
    def test_html(self):
        for _, v in enumerate(markup_snippets):
            self.assertTrue(parse(v))

        self.assertEqual(expand('fset>input:c'), '<fieldset><input type="checkbox" name="" id=""></fieldset>')

    def test_xsl(self):
        for _, v in enumerate(xsl_snippets):
            self.assertTrue(parse(v))
