import unittest
import sys

sys.path.append('../')

from emmet import expand

def field(index: int, placeholder: str, **kwargs):
    if placeholder:
        return '${%d:%s}' % (index, placeholder)
    return '${%d}' % index


class TestExpandMarkup(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(expand('input[value="text$"]*2'), '<input type="text" value="text1"><input type="text" value="text2">')
        self.assertEqual(expand('ul>.item$*2'), '<ul>\n\t<li class="item1"></li>\n\t<li class="item2"></li>\n</ul>')

        # insert text into abbreviation
        self.assertEqual(expand('ul>.item$*', { 'text': ['foo', 'bar'] }), '<ul>\n\t<li class="item1">foo</li>\n\t<li class="item2">bar</li>\n</ul>')

        # Wrap with Abbreviation, skip empty lines
        self.assertEqual(
            expand('ul>.item$*', {'text': ['foo', '', 'bar', '', '']}),
            '<ul>\n\t<li class="item1">foo</li>\n\t<li class="item2">bar</li>\n</ul>'
        )

        # insert TextMate-style fields/tabstops in output
        self.assertEqual(expand('ul>.item$*2', {
            'options': {
                'output.field': field
            }
        }), '<ul>\n\t<li class="item1">${1}</li>\n\t<li class="item2">${2}</li>\n</ul>')

        # https://github.com/emmetio/emmet/issues/725
        self.assertEqual(expand('textarea'), '<textarea name="" id=""></textarea>')

    def test_abbreviations(self):
        snippets = {
            'test': 'test[!foo bar. baz={}]'
        }
        opt = { 'snippets': snippets }
        reverse = {
            'options': { 'output.reverseAttributes': True },
            'snippets': snippets
        }

        self.assertEqual(expand('a.test'), '<a href="" class="test"></a>')
        self.assertEqual(expand('a.test', reverse), '<a class="test" href=""></a>')

        self.assertEqual(expand('test', opt), '<test bar="bar" baz={}></test>')
        self.assertEqual(expand('test[foo]', opt), '<test bar="bar" baz={}></test>')
        self.assertEqual(expand('test[baz=a foo=1]', opt), '<test foo="1" bar="bar" baz={a}></test>')

        # Apply attributes in reverse order
        self.assertEqual(expand('test', reverse), '<test bar="bar" baz={}></test>')
        self.assertEqual(expand('test[foo]', reverse), '<test bar="bar" baz={}></test>')
        self.assertEqual(expand('test[baz=a foo=1]', reverse), '<test baz={a} foo="1" bar="bar"></test>')

    def test_expressions(self):
        self.assertEqual(expand('span{{foo}}'), '<span>{foo}</span>')
        self.assertEqual(expand('span{foo}'), '<span>foo</span>')
        self.assertEqual(expand('span[foo={bar}]'), '<span foo={bar}></span>')
        self.assertEqual(expand('span[foo={{bar}}]'), '<span foo={{bar}}></span>')

    def test_numbering(self):
        self.assertEqual(expand('ul>li.item$@-*5'), '<ul>\n\t<li class="item5"></li>\n\t<li class="item4"></li>\n\t<li class="item3"></li>\n\t<li class="item2"></li>\n\t<li class="item1"></li>\n</ul>')

    def test_syntax(self):
        self.assertEqual(expand('ul>.item$*2', { 'syntax': 'html' }), '<ul>\n\t<li class="item1"></li>\n\t<li class="item2"></li>\n</ul>')
        self.assertEqual(expand('ul>.item$*2', { 'syntax': 'slim' }), 'ul\n\tli.item1 \n\tli.item2 ')
        self.assertEqual(expand('xsl:variable[name=a select=b]>div', { 'syntax': 'xsl' }), '<xsl:variable name="a">\n\t<div></div>\n</xsl:variable>')

    def test_custom_profile(self):
        self.assertEqual(expand('img'), '<img src="" alt="">')
        self.assertEqual(expand('img', { 'options': { 'output.selfClosingStyle': 'xhtml' } }), '<img src="" alt="" />')

    def test_custom_variables(self):
        variables = { 'charset': 'ru-RU' }
        self.assertEqual(expand('[charset=${charset}]{${charset}}'), '<div charset="UTF-8">UTF-8</div>')
        self.assertEqual(expand('[charset=${charset}]{${charset}}', { 'variables': variables }), '<div charset="ru-RU">ru-RU</div>')

    def test_custom_snippets(self):
        snippets = {
            'link': 'link[foo=bar href]/',
            'foo': '.foo[bar=baz]',
            'repeat': 'div>ul>li{Hello World}*3'
        }

        self.assertEqual(expand('foo', { 'snippets': snippets }), '<div class="foo" bar="baz"></div>')

        # `link:css` depends on `link` snippet so changing it will result in
        # altered `link:css` result
        self.assertEqual(expand('link:css'), '<link rel="stylesheet" href="style.css">')
        self.assertEqual(expand('link:css', { 'snippets': snippets }), '<link foo="bar" href="style.css">')

        # https://github.com/emmetio/emmet/issues/468
        self.assertEqual(expand('repeat', { 'snippets': snippets }), '<div>\n\t<ul>\n\t\t<li>Hello World</li>\n\t\t<li>Hello World</li>\n\t\t<li>Hello World</li>\n\t</ul>\n</div>')

    def formatter_options(self):
        self.assertEqual(expand('ul>.item$*2'), '<ul>\n\t<li class="item1"></li>\n\t<li class="item2"></li>\n</ul>')
        self.assertEqual(expand('ul>.item$*2', { 'options': { 'comment.enabled': True } }),
            '<ul>\n\t<li class="item1"></li>\n\t<!-- /.item1 -->\n\t<li class="item2"></li>\n\t<!-- /.item2 -->\n</ul>')

        self.assertEqual(expand('div>p'), '<div>\n\t<p></p>\n</div>')
        self.assertEqual(expand('div>p', { 'options': { 'output.formatLeafNode': True } }), '<div>\n\t<p>\n\t\t\n\t</p>\n</div>')

    def test_jsx(self):
        config = { 'syntax': 'jsx' }
        self.assertEqual(expand('div#foo.bar', config), '<div id="foo" className="bar"></div>')
        self.assertEqual(expand('label[for=a]', config), '<label htmlFor="a"></label>')
        self.assertEqual(expand('Foo.Bar', config), '<Foo.Bar></Foo.Bar>')
        self.assertEqual(expand('div.{theme.style}', config), '<div className={theme.style}></div>')

    def test_override_attributes(self):
        config = { 'syntax': 'jsx' }
        self.assertEqual(expand('.bar', config), '<div className="bar"></div>');
        self.assertEqual(expand('..bar', config), '<div styleName={styles.bar}></div>')
        self.assertEqual(expand('..foo-bar', config), '<div styleName={styles[\'foo-bar\']}></div>')

        self.assertEqual(expand('.foo', { 'syntax': 'vue' }), '<div class="foo"></div>')
        self.assertEqual(expand('..foo', { 'syntax': 'vue' }), '<div :class="foo"></div>')

    def test_wrap_with_abbreviation(self):
        self.assertEqual(
            expand('img[src="$#"]*', {'text': ['foo.jpg', 'bar.jpg']}),
            '<img src="foo.jpg" alt=""><img src="bar.jpg" alt="">')
        self.assertEqual(expand('div>ul', { 'text': ['<div>line1</div>\n<div>line2</div>'] }),
            '<div>\n\t<ul>\n\t\t<div>line1</div>\n\t\t<div>line2</div>\n\t</ul>\n</div>')

        self.assertEqual(expand('a', {'text': 'foo'}), '<a href="">foo</a>')
        self.assertEqual(expand('a', {'text': 'emmet//io'}), '<a href="">emmet//io</a>')
        self.assertEqual(expand('a', {'text': 'http://emmet.io'}), '<a href="http://emmet.io">http://emmet.io</a>')
        self.assertEqual(expand('a', {'text': '//emmet.io'}), '<a href="//emmet.io">//emmet.io</a>')
        self.assertEqual(expand('a', {'text': 'www.emmet.io'}), '<a href="http://www.emmet.io">www.emmet.io</a>')
        self.assertEqual(expand('a', {'text': 'emmet.io'}), '<a href="">emmet.io</a>')
        self.assertEqual(expand('a', {'text': 'info@emmet.io'}), '<a href="mailto:info@emmet.io">info@emmet.io</a>')
        self.assertEqual(expand('a', {'text': 'uSeR@myLongDomainName.com'}), '<a href="mailto:uSeR@myLongDomainName.com">uSeR@myLongDomainName.com</a>')

        self.assertEqual(expand('p', {'text': 'foo\nbar'}), '<p>\n\tfoo\n\tbar\n</p>')
        self.assertEqual(expand('p', {'text': '<div>foo</div>'}), '<p>\n\t<div>foo</div>\n</p>')

        self.assertEqual(expand('a', { 'text': 'https://www.google.it' }), '<a href="https://www.google.it">https://www.google.it</a>')
        self.assertEqual(expand('a', { 'text': 'www.google.it' }), '<a href="http://www.google.it">www.google.it</a>')
        self.assertEqual(expand('a', { 'text': 'google.it' }), '<a href="">google.it</a>')
        self.assertEqual(expand('a', { 'text': 'test here' }), '<a href="">test here</a>')
        self.assertEqual(expand('a', { 'text': 'test@domain.com' }), '<a href="mailto:test@domain.com">test@domain.com</a>')
        self.assertEqual(expand('a', { 'text': 'test here test@domain.com' }), '<a href="">test here test@domain.com</a>')
        self.assertEqual(expand('a', { 'text': 'test here www.domain.com' }), '<a href="">test here www.domain.com</a>')

        self.assertEqual(expand('a[href=]', { 'text': 'https://www.google.it' }), '<a href="https://www.google.it">https://www.google.it</a>')
        self.assertEqual(expand('a[href=]', { 'text': 'www.google.it' }), '<a href="http://www.google.it">www.google.it</a>')
        self.assertEqual(expand('a[href=]', { 'text': 'google.it' }), '<a href="">google.it</a>')
        self.assertEqual(expand('a[href=]', { 'text': 'test here' }), '<a href="">test here</a>')
        self.assertEqual(expand('a[href=]', { 'text': 'test@domain.com' }), '<a href="mailto:test@domain.com">test@domain.com</a>')
        self.assertEqual(expand('a[href=]', { 'text': 'test here test@domain.com' }), '<a href="">test here test@domain.com</a>')
        self.assertEqual(expand('a[href=]', { 'text': 'test here www.domain.com' }), '<a href="">test here www.domain.com</a>')
        self.assertEqual(expand('a[class=here]', { 'text': 'test@domain.com' }), '<a href="mailto:test@domain.com" class="here">test@domain.com</a>')
        self.assertEqual(expand('a.here', { 'text': 'www.domain.com' }), '<a href="http://www.domain.com" class="here">www.domain.com</a>')
        self.assertEqual(expand('a[class=here]', { 'text': 'test here test@domain.com' }), '<a href="" class="here">test here test@domain.com</a>')
        self.assertEqual(expand('a.here', { 'text': 'test here www.domain.com' }), '<a href="" class="here">test here www.domain.com</a>')

        self.assertEqual(expand('a[href="www.google.it"]', { 'text': 'test' }), '<a href="www.google.it">test</a>')
        self.assertEqual(expand('a[href="www.example.com"]', { 'text': 'www.google.it' }), '<a href="www.example.com">www.google.it</a>')

    def test_class_names(self):
        self.assertEqual(expand('div.foo/'), '<div class="foo">')
        self.assertEqual(expand('div.foo1/2'), '<div class="foo1/2"></div>')
        self.assertEqual(expand('div.foo.1/2'), '<div class="foo 1/2"></div>')


class TestExpandPug(unittest.TestCase):
    def test_basics(self):
        self.assertEqual(expand('!', { 'syntax': 'pug' }),
            'doctype html\nhtml(lang="en")\n\thead\n\t\tmeta(charset="UTF-8")\n\t\tmeta(name="viewport", content="width=device-width, initial-scale=1.0")\n\t\ttitle Document\n\tbody ')
