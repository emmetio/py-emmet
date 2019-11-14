import unittest
import sys

sys.path.append('../')

from emmet.config import markup_snippets, xsl_snippets
from emmet.abbreviation import parse


class TestSnippets(unittest.TestCase):
    def test_html(self):
        for _, v in enumerate(markup_snippets):
            self.assertTrue(parse(v))

    def test_xsl(self):
        for _, v in enumerate(xsl_snippets):
            self.assertTrue(parse(v))
