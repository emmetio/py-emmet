import unittest
import sys

sys.path.append('../')
from emmet.output_stream import OutputStream, tag_name, attr_name, self_close, is_inline
from emmet.config import Config

class TestOutputStream(unittest.TestCase):
    def test_stream(self):
        conf = Config({'options': {'output.baseIndent': '>>'}})
        out = OutputStream(conf.options)

        out.push('aaa')
        self.assertEqual(out.value, 'aaa')
        self.assertEqual(out.line, 0)
        self.assertEqual(out.column, 3)
        self.assertEqual(out.offset, 3)

        out.push_string('bbb')
        self.assertEqual(out.value, 'aaabbb')
        self.assertEqual(out.line, 0)
        self.assertEqual(out.column, 6)
        self.assertEqual(out.offset, 6)

        # Add text with newlines
        out.push_string('ccc\nddd')
        self.assertEqual(out.value, 'aaabbbccc\n>>ddd')
        self.assertEqual(out.line, 1)
        self.assertEqual(out.column, 5)
        self.assertEqual(out.offset, 15)

        # Add newline with indent
        out.level += 1
        out.push_newline(True)
        self.assertEqual(out.value, 'aaabbbccc\n>>ddd\n>>\t')
        self.assertEqual(out.line, 2)
        self.assertEqual(out.column, 3)
        self.assertEqual(out.offset, 19)

    def test_profile_tag_name(self):
        as_is = Config({ 'options': { 'output.tagCase': '' } })
        upper = Config({ 'options': { 'output.tagCase': 'upper' } })
        lower = Config({ 'options': { 'output.tagCase': 'lower' } })

        self.assertEqual(tag_name('Foo', as_is), 'Foo')
        self.assertEqual(tag_name('bAr', as_is), 'bAr')

        self.assertEqual(tag_name('Foo', upper), 'FOO')
        self.assertEqual(tag_name('bAr', upper), 'BAR')

        self.assertEqual(tag_name('Foo', lower), 'foo')
        self.assertEqual(tag_name('bAr', lower), 'bar')

    def test_attribute_name(self):
        as_is = Config({ 'options': { 'output.attributeCase': '' } })
        upper = Config({ 'options': { 'output.attributeCase': 'upper' } })
        lower = Config({ 'options': { 'output.attributeCase': 'lower' } })

        self.assertEqual(attr_name('Foo', as_is), 'Foo')
        self.assertEqual(attr_name('bAr', as_is), 'bAr')

        self.assertEqual(attr_name('Foo', upper), 'FOO')
        self.assertEqual(attr_name('bAr', upper), 'BAR')

        self.assertEqual(attr_name('Foo', lower), 'foo')
        self.assertEqual(attr_name('bAr', lower), 'bar')

    def test_self_close(self):
        html = Config({ 'options': { 'output.selfClosingStyle': 'html' } })
        xhtml = Config({ 'options': { 'output.selfClosingStyle': 'xhtml' } })
        xml = Config({ 'options': { 'output.selfClosingStyle': 'xml' } })

        self.assertEqual(self_close(html), '')
        self.assertEqual(self_close(xhtml), ' /')
        self.assertEqual(self_close(xml), '/')

    def test_inline_elements(self):
        config = Config()
        self.assertEqual(is_inline('a', config), True)
        self.assertEqual(is_inline('b', config), True)
        self.assertEqual(is_inline('c', config), False)
