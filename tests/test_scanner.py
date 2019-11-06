import unittest
import sys

sys.path.append('../')

from emmet.scanner import Scanner, ScannerException
from emmet.scanner_utils import eat_pair, eat_quoted

class TestScanner(unittest.TestCase):
    def test_basics(self):
        data = 'hello'
        s = Scanner(data)

        self.assertEqual(s.string, data)
        self.assertEqual(s.start, 0)
        self.assertEqual(s.pos, 0)

        self.assertEqual(s.peek(), data[0])
        self.assertEqual(s.start, 0)
        self.assertEqual(s.pos, 0)

        self.assertEqual(s.next(), data[0])
        self.assertEqual(s.next(), data[1])
        self.assertEqual(s.start, 0)
        self.assertEqual(s.pos, 2)

        self.assertEqual(s.next(), data[2])
        self.assertEqual(s.start, 0)
        self.assertEqual(s.pos, 3)

        self.assertEqual(s.current(), data[0:3])

    def test_limit_range(self):
        outer = Scanner('foo bar baz')
        inner = outer.limit(4, 7)

        self.assertTrue(outer != inner)

        outer_value = ''
        inner_value = ''

        while not outer.eof():
            outer_value += outer.next()

        while not inner.eof():
            inner_value += inner.next()

        self.assertEqual(outer_value, 'foo bar baz')
        self.assertEqual(inner_value, 'bar')

    def test_eat(self):
        scanner = Scanner('[foo] (bar (baz) bam)')

        self.assertTrue(eat_pair(scanner, '[', ']'))
        self.assertEqual(scanner.start, 0)
        self.assertEqual(scanner.pos, 5)
        self.assertEqual(scanner.current(), '[foo]')

        # No pair here
        self.assertFalse(eat_pair(scanner, '(', ')', { 'throws': True }))
        scanner.eat_while(' ')

        self.assertTrue(eat_pair(scanner, '(', ')', { 'throws': True }))
        self.assertEqual(scanner.start, 6)
        self.assertEqual(scanner.pos, 21)
        self.assertEqual(scanner.current(), '(bar (baz) bam)')

    def test_eat_with_quotes(self):
        scanner = Scanner('[foo "bar]" ]')
        self.assertTrue(eat_pair(scanner, '[', ']'))
        self.assertEqual(scanner.start, 0)
        self.assertEqual(scanner.pos, 13)
        self.assertEqual(scanner.current(), '[foo "bar]" ]')

    def test_eat_quoted(self):
        data = '"foo"   \'bar\''
        scanner = Scanner(data)

        self.assertTrue(eat_quoted(scanner))
        self.assertEqual(scanner.start, 0)
        self.assertEqual(scanner.pos, 5)
        self.assertEqual(scanner.current(), '"foo"')

        # no double-quoted value ahead
        self.assertFalse(eat_quoted(scanner, { 'throws': True }))

        # eat space
        self.assertTrue(scanner.eat_while(' '))
        self.assertEqual(scanner.pos, 8)

        self.assertTrue(eat_quoted(scanner))
        self.assertEqual(scanner.start, 8)
        self.assertEqual(scanner.pos, 13)
        self.assertEqual(scanner.current(), '\'bar\'')
        self.assertTrue(scanner.eof())

    def test_eat_invalid(self):
        scanner = Scanner('[foo')
        self.assertFalse(eat_pair(scanner, '[', ']'))
        self.assertEqual(scanner.start, 0)
        self.assertEqual(scanner.pos, 0)

        with self.assertRaises(ScannerException):
            eat_pair(scanner, '[', ']', { 'throws': True })

    def test_invalid_strings(self):
        scanner = Scanner('"foo')
        self.assertFalse(eat_quoted(scanner))
        self.assertEqual(scanner.pos, 0)

        with self.assertRaises(ScannerException):
            eat_quoted(scanner, { 'throws': True })

    def test_handle_escapes(self):
        scanner = Scanner('"foo\\"bar" baz')
        self.assertTrue(eat_quoted(scanner))
        self.assertEqual(scanner.start, 0)
        self.assertEqual(scanner.pos, 10)
        self.assertEqual(scanner.current(), '"foo\\"bar"')

if __name__ == '__main__':
    unittest.main()
