import unittest
import sys

sys.path.append('../')

from emmet.markup import parse, html, haml, pug, slim
from emmet.config import Config


def tabstops(index: int, placeholder: str, **kwargs):
    if placeholder:
        return '${%d:%s}' % (index, placeholder)
    return '${%d}' % index


default_config = Config()
field = Config({
    'options': {
        'output.field': tabstops
    }
})

def create_profile(options: dict):
    return Config({'options': options})


def output_html(abbr: str, config=default_config):
    return html(parse(abbr, config), config)


class TestHTMLFormat(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(output_html('div>p'), '<div>\n\t<p></p>\n</div>')
        self.assertEqual(output_html('div>p*3'), '<div>\n\t<p></p>\n\t<p></p>\n\t<p></p>\n</div>')
        self.assertEqual(output_html('div#a>p.b*2>span'), '<div id="a">\n\t<p class="b"><span></span></p>\n\t<p class="b"><span></span></p>\n</div>')
        self.assertEqual(output_html('div>div>div'), '<div>\n\t<div>\n\t\t<div></div>\n\t</div>\n</div>')
        self.assertEqual(output_html('table>tr*2>td{item}*2'),
            '<table>\n\t<tr>\n\t\t<td>item</td>\n\t\t<td>item</td>\n\t</tr>\n\t<tr>\n\t\t<td>item</td>\n\t\t<td>item</td>\n\t</tr>\n</table>')

    def test_inline_elements(self):
        profile = create_profile({ 'output.inlineBreak': 3 })
        break_inline = create_profile({ 'output.inlineBreak': 1 })
        keep_inline = create_profile({ 'output.inlineBreak': 0 })
        xhtml = create_profile({ 'output.selfClosingStyle': 'xhtml' })

        self.assertEqual(output_html('div>a>b*3', xhtml), '<div>\n\t<a href="">\n\t\t<b></b>\n\t\t<b></b>\n\t\t<b></b>\n\t</a>\n</div>')

        self.assertEqual(output_html('p>i', profile), '<p><i></i></p>')
        self.assertEqual(output_html('p>i*2', profile), '<p><i></i><i></i></p>')
        self.assertEqual(output_html('p>i*2', break_inline), '<p>\n\t<i></i>\n\t<i></i>\n</p>')
        self.assertEqual(output_html('p>i*3', profile), '<p>\n\t<i></i>\n\t<i></i>\n\t<i></i>\n</p>')
        self.assertEqual(output_html('p>i*3', keep_inline), '<p><i></i><i></i><i></i></p>')

        self.assertEqual(output_html('i*2', profile), '<i></i><i></i>')
        self.assertEqual(output_html('i*3', profile), '<i></i>\n<i></i>\n<i></i>')
        self.assertEqual(output_html('i{a}+i{b}', profile), '<i>a</i><i>b</i>')

        self.assertEqual(output_html('img[src]/+p', xhtml), '<img src="" alt="" />\n<p></p>')
        self.assertEqual(output_html('div>img[src]/+p', xhtml), '<div>\n\t<img src="" alt="" />\n\t<p></p>\n</div>')
        self.assertEqual(output_html('div>p+img[src]/', xhtml), '<div>\n\t<p></p>\n\t<img src="" alt="" />\n</div>')
        self.assertEqual(output_html('div>p+img[src]/+p', xhtml), '<div>\n\t<p></p>\n\t<img src="" alt="" />\n\t<p></p>\n</div>')
        self.assertEqual(output_html('div>p+img[src]/*2+p', xhtml), '<div>\n\t<p></p>\n\t<img src="" alt="" /><img src="" alt="" />\n\t<p></p>\n</div>')
        self.assertEqual(output_html('div>p+img[src]/*3+p', xhtml), '<div>\n\t<p></p>\n\t<img src="" alt="" />\n\t<img src="" alt="" />\n\t<img src="" alt="" />\n\t<p></p>\n</div>')


    def test_generate_fields(self):
        self.assertEqual(output_html('a[href]', field), '<a href="${1}">${2}</a>')
        self.assertEqual(output_html('a[href]*2', field), '<a href="${1}">${2}</a><a href="${3}">${4}</a>')
        self.assertEqual(output_html('{${0} ${1:foo} ${2:bar}}*2', field), '${1} ${2:foo} ${3:bar}\n${4} ${5:foo} ${6:bar}')
        self.assertEqual(output_html('{${0} ${1:foo} ${2:bar}}*2'), ' foo bar\n foo bar')
        self.assertEqual(output_html('ul>li*2', field), '<ul>\n\t<li>${1}</li>\n\t<li>${2}</li>\n</ul>')
        self.assertEqual(output_html('div>img[src]/', field), '<div><img src="${1}" alt="${2}"></div>')


    def test_mixed_content(self):
        self.assertEqual(output_html('div{foo}'), '<div>foo</div>')
        self.assertEqual(output_html('div>{foo}'), '<div>foo</div>')
        self.assertEqual(output_html('div>{foo}+{bar}'), '<div>\n\tfoo\n\tbar\n</div>')
        self.assertEqual(output_html('div>{foo}+{bar}+p'), '<div>\n\tfoo\n\tbar\n\t<p></p>\n</div>')
        self.assertEqual(output_html('div>{foo}+{bar}+p+{foo}+{bar}+p'), '<div>\n\tfoo\n\tbar\n\t<p></p>\n\tfoo\n\tbar\n\t<p></p>\n</div>')
        self.assertEqual(output_html('div>{foo}+p+{bar}'), '<div>\n\tfoo\n\t<p></p>\n\tbar\n</div>')
        self.assertEqual(output_html('div>{foo}>p'), '<div>\n\tfoo\n\t<p></p>\n</div>')

        self.assertEqual(output_html('div>{<!-- ${0} -->}'), '<div><!--  --></div>')
        self.assertEqual(output_html('div>{<!-- ${0} -->}+p'), '<div>\n\t<!--  -->\n\t<p></p>\n</div>')
        self.assertEqual(output_html('div>p+{<!-- ${0} -->}'), '<div>\n\t<p></p>\n\t<!--  -->\n</div>')
        self.assertEqual(output_html('div>{<!-- ${0} -->}>p'), '<div>\n\t<!-- <p></p> -->\n</div>')
        self.assertEqual(output_html('div>{<!-- ${0} -->}*2>p'), '<div>\n\t<!-- <p></p> -->\n\t<!-- <p></p> -->\n</div>')

        self.assertEqual(output_html('div>{<!-- ${0} -->}>p*2'), '<div>\n\t<!-- \n\t<p></p>\n\t<p></p>\n\t-->\n</div>')
        self.assertEqual(output_html('div>{<!-- ${0} -->}*2>p*2'), '<div>\n\t<!-- \n\t<p></p>\n\t<p></p>\n\t-->\n\t<!-- \n\t<p></p>\n\t<p></p>\n\t-->\n</div>')

        self.assertEqual(output_html('div>{<!-- ${0} -->}>b'), '<div>\n\t<!-- <b></b> -->\n</div>')
        self.assertEqual(output_html('div>{<!-- ${0} -->}>b*2'), '<div>\n\t<!-- <b></b><b></b> -->\n</div>')
        self.assertEqual(output_html('div>{<!-- ${0} -->}>b*3'), '<div>\n\t<!-- \n\t<b></b>\n\t<b></b>\n\t<b></b>\n\t-->\n</div>')

        self.assertEqual(output_html('div>{<!-- ${0} -->}', field), '<div><!-- ${1} --></div>')
        self.assertEqual(output_html('div>{<!-- ${0} -->}>b', field), '<div>\n\t<!-- <b>${1}</b> -->\n</div>')

    def test_self_closing(self):
        xml_style = create_profile({ 'output.selfClosingStyle': 'xml' })
        html_style = create_profile({ 'output.selfClosingStyle': 'html' })
        xhtml_style = create_profile({ 'output.selfClosingStyle': 'xhtml' })

        self.assertEqual(output_html('img[src]/', html_style), '<img src="" alt="">')
        self.assertEqual(output_html('img[src]/', xhtml_style), '<img src="" alt="" />')
        self.assertEqual(output_html('img[src]/', xml_style), '<img src="" alt=""/>')
        self.assertEqual(output_html('div>img[src]/', xhtml_style), '<div><img src="" alt="" /></div>')


    def test_boolean_attributes(self):
        compact = create_profile({'output.compactBoolean': True})
        no_compact = create_profile({'output.compactBoolean': False})

        self.assertEqual(output_html('p[b.]', no_compact), '<p b="b"></p>')
        self.assertEqual(output_html('p[b.]', compact), '<p b></p>')
        self.assertEqual(output_html('p[contenteditable]', compact), '<p contenteditable></p>')
        self.assertEqual(output_html('p[contenteditable]', no_compact), '<p contenteditable="contenteditable"></p>')
        self.assertEqual(output_html('p[contenteditable=foo]', compact), '<p contenteditable="foo"></p>')


    def test_no_formatting(self):
        profile = create_profile({ 'output.format': False })
        self.assertEqual(output_html('div>p', profile), '<div><p></p></div>')
        self.assertEqual(output_html('div>{foo}+p+{bar}', profile), '<div>foo<p></p>bar</div>')
        self.assertEqual(output_html('div>{foo}>p', profile), '<div>foo<p></p></div>')
        self.assertEqual(output_html('div>{<!-- ${0} -->}>p', profile), '<div><!-- <p></p> --></div>')

    def test_format_specific_nodes(self):
        self.assertEqual(output_html('{<!DOCTYPE html>}+html>(head>meta[charset=${charset}]/+title{${1:Document}})+body', field),
                '<!DOCTYPE html>\n<html>\n<head>\n\t<meta charset="UTF-8">\n\t<title>${2:Document}</title>\n</head>\n<body>\n\t${3}\n</body>\n</html>')

    def test_comment(self):
        opt = Config({ 'options': { 'comment.enabled': True } })

        self.assertEqual(output_html('ul>li.item', opt), '<ul>\n\t<li class="item"></li>\n\t<!-- /.item -->\n</ul>')
        self.assertEqual(output_html('div>ul>li.item#foo', opt), '<div>\n\t<ul>\n\t\t<li class="item" id="foo"></li>\n\t\t<!-- /#foo.item -->\n\t</ul>\n</div>')

        opt.options['comment.after'] = ' { [%ID] }'
        self.assertEqual(output_html('div>ul>li.item#foo', opt), '<div>\n\t<ul>\n\t\t<li class="item" id="foo"></li> { %foo }\n\t</ul>\n</div>')


def output_haml(abbr: str, config=default_config):
    return haml(parse(abbr, config), config)

class TestHAMLFormat(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(output_haml('div#header>ul.nav>li[title=test].nav-item*2'),
            '#header\n\t%ul.nav\n\t\t%li.nav-item(title="test") \n\t\t%li.nav-item(title="test") ')

        # https://github.com/emmetio/emmet/issues/446
        self.assertEqual(output_haml('li>a'), '%li\n\t%a(href="") ')

        self.assertEqual(output_haml('div#foo[data-n1=v1 title=test data-n2=v2].bar'),
            '#foo.bar(data-n1="v1" title="test" data-n2="v2") ')

        profile = create_profile({ 'output.compactBoolean': True })
        self.assertEqual(output_haml('input[disabled. foo title=test]/', profile), '%input(type="text" disabled foo="" title="test")/')

        profile = create_profile({ 'output.compactBoolean': False })
        self.assertEqual(output_haml('input[disabled. foo title=test]/', profile), '%input(type="text" disabled=true foo="" title="test")/')

    def test_nodes_with_text(self):
        self.assertEqual(output_haml('{Text 1}'), 'Text 1')
        self.assertEqual(output_haml('span{Text 1}'), '%span Text 1')
        self.assertEqual(output_haml('span{Text 1}>b{Text 2}'), '%span Text 1\n\t%b Text 2')
        self.assertEqual(output_haml('span{Text 1\nText 2}>b{Text 3}'), '%span\n\tText 1 |\n\tText 2 |\n\t%b Text 3')
        self.assertEqual(output_haml('div>span{Text 1\nText 2\nText 123}>b{Text 3}'), '%div\n\t%span\n\t\tText 1   |\n\t\tText 2   |\n\t\tText 123 |\n\t\t%b Text 3')

    def test_generate_fields(self):
        self.assertEqual(output_haml('a[href]', field), '%a(href="${1}") ${2}')
        self.assertEqual(output_haml('a[href]*2', field), '%a(href="${1}") ${2}\n%a(href="${3}") ${4}')
        self.assertEqual(output_haml('{${0} ${1:foo} ${2:bar}}*2', field), '${1} ${2:foo} ${3:bar}${4} ${5:foo} ${6:bar}')
        self.assertEqual(output_haml('{${0} ${1:foo} ${2:bar}}*2'), ' foo bar foo bar')
        self.assertEqual(output_haml('ul>li*2', field), '%ul\n\t%li ${1}\n\t%li ${2}')
        self.assertEqual(output_haml('div>img[src]/', field), '%div\n\t%img(src="${1}" alt="${2}")/')

def output_pug(abbr: str, config=default_config):
    return pug(parse(abbr, config), config)

class TestPUGFormat(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(output_pug('div#header>ul.nav>li[title=test].nav-item*2'),
            '#header\n\tul.nav\n\t\tli.nav-item(title="test") \n\t\tli.nav-item(title="test") ')

        self.assertEqual(output_pug('div#foo[data-n1=v1 title=test data-n2=v2].bar'),
            '#foo.bar(data-n1="v1", title="test", data-n2="v2") ')

        self.assertEqual(output_pug('input[disabled. foo title=test]'), 'input(type="text", disabled, foo="", title="test")')
        # Use closing slash for XML output format
        self.assertEqual(output_pug('input[disabled. foo title=test]', create_profile({ 'output.selfClosingStyle': 'xml' })), 'input(type="text", disabled, foo="", title="test")/');


    def test_nodes_with_test(self):
        self.assertEqual(output_pug('{Text 1}'), 'Text 1')
        self.assertEqual(output_pug('span{Text 1}'), 'span Text 1')
        self.assertEqual(output_pug('span{Text 1}>b{Text 2}'), 'span Text 1\n\tb Text 2')
        self.assertEqual(output_pug('span{Text 1\nText 2}>b{Text 3}'), 'span\n\t| Text 1\n\t| Text 2\n\tb Text 3')
        self.assertEqual(output_pug('div>span{Text 1\nText 2}>b{Text 3}'), 'div\n\tspan\n\t\t| Text 1\n\t\t| Text 2\n\t\tb Text 3')

    def test_generate_fields(self):
        self.assertEqual(output_pug('a[href]', field), 'a(href="${1}") ${2}')
        self.assertEqual(output_pug('a[href]*2', field), 'a(href="${1}") ${2}\na(href="${3}") ${4}')
        self.assertEqual(output_pug('{${0} ${1:foo} ${2:bar}}*2', field), '${1} ${2:foo} ${3:bar}${4} ${5:foo} ${6:bar}')
        self.assertEqual(output_pug('{${0} ${1:foo} ${2:bar}}*2'), ' foo bar foo bar')
        self.assertEqual(output_pug('ul>li*2', field), 'ul\n\tli ${1}\n\tli ${2}')
        self.assertEqual(output_pug('div>img[src]/', field), 'div\n\timg(src="${1}", alt="${2}")')


def output_slim(abbr: str, config=default_config):
    return slim(parse(abbr, config), config)

class TestSlimFormat(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(output_slim('div#header>ul.nav>li[title=test].nav-item*2'),
                '#header\n\tul.nav\n\t\tli.nav-item title="test" \n\t\tli.nav-item title="test" ')

        self.assertEqual(output_slim('div#foo[data-n1=v1 title=test data-n2=v2].bar'),
            '#foo.bar data-n1="v1" title="test" data-n2="v2" ')

    def test_nodes_with_text(self):
        self.assertEqual(output_slim('{Text 1}'), 'Text 1')
        self.assertEqual(output_slim('span{Text 1}'), 'span Text 1')
        self.assertEqual(output_slim('span{Text 1}>b{Text 2}'), 'span Text 1\n\tb Text 2')
        self.assertEqual(output_slim('span{Text 1\nText 2}>b{Text 3}'), 'span\n\t| Text 1\n\t| Text 2\n\tb Text 3')
        self.assertEqual(output_slim('div>span{Text 1\nText 2}>b{Text 3}'), 'div\n\tspan\n\t\t| Text 1\n\t\t| Text 2\n\t\tb Text 3')

    def test_generate_fields(self):
        self.assertEqual(output_slim('a[href]', field), 'a href="${1}" ${2}')
        self.assertEqual(output_slim('a[href]*2', field), 'a href="${1}" ${2}\na href="${3}" ${4}')
        self.assertEqual(output_slim('{${0} ${1:foo} ${2:bar}}*2', field), '${1} ${2:foo} ${3:bar}${4} ${5:foo} ${6:bar}')
        self.assertEqual(output_slim('{${0} ${1:foo} ${2:bar}}*2'), ' foo bar foo bar')
        self.assertEqual(output_slim('ul>li*2', field), 'ul\n\tli ${1}\n\tli ${2}')
        self.assertEqual(output_slim('div>img[src]/', field), 'div\n\timg src="${1}" alt="${2}"/')
