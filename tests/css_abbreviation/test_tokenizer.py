import unittest
import sys

sys.path.append('../../')

from emmet.css_abbreviation import tokenize
from emmet.scanner import ScannerException

def json_tokens(abbr: str):
    return [token.to_json() for token in tokenize(abbr)]

class TestScanner(unittest.TestCase):
    def test_numeric_values(self):
        self.assertEqual(json_tokens('p10'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': 10, 'unit': '', 'start': 1, 'end': 3 }
        ])

        self.assertEqual(json_tokens('p-10'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': -10, 'unit': '', 'start': 1, 'end': 4 }
        ])

        self.assertEqual(json_tokens('p-10-'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': -10, 'unit': '', 'start': 1, 'end': 4 },
            { 'type': 'Operator', 'operator': '-', 'start': 4, 'end': 5 }
        ])

        self.assertEqual(json_tokens('p-10-20'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': -10, 'unit': '', 'start': 1, 'end': 4 },
            { 'type': 'Operator', 'operator': '-', 'start': 4, 'end': 5 },
            { 'type': 'NumberValue', 'value': 20, 'unit': '', 'start': 5, 'end': 7 }
        ])

        self.assertEqual(json_tokens('p-10--20'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': -10, 'unit': '', 'start': 1, 'end': 4 },
            { 'type': 'Operator', 'operator': '-', 'start': 4, 'end': 5 },
            { 'type': 'NumberValue', 'value': -20, 'unit': '', 'start': 5, 'end': 8 }
        ])

        self.assertEqual(json_tokens('p-10-20--30'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': -10, 'unit': '', 'start': 1, 'end': 4 },
            { 'type': 'Operator', 'operator': '-', 'start': 4, 'end': 5 },
            { 'type': 'NumberValue', 'value': 20, 'unit': '', 'start': 5, 'end': 7 },
            { 'type': 'Operator', 'operator': '-', 'start': 7, 'end': 8 },
            { 'type': 'NumberValue', 'value': -30, 'unit': '', 'start': 8, 'end': 11 }
        ])

        self.assertEqual(json_tokens('p-10p-20--30'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': -10, 'unit': 'p', 'start': 1, 'end': 5 },
            { 'type': 'NumberValue', 'value': -20, 'unit': '', 'start': 5, 'end': 8 },
            { 'type': 'Operator', 'operator': '-', 'start': 8, 'end': 9 },
            { 'type': 'NumberValue', 'value': -30, 'unit': '', 'start': 9, 'end': 12 }
        ])

        self.assertEqual(json_tokens('p-10%-20--30'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': -10, 'unit': '%', 'start': 1, 'end': 5 },
            { 'type': 'NumberValue', 'value': -20, 'unit': '', 'start': 5, 'end': 8 },
            { 'type': 'Operator', 'operator': '-', 'start': 8, 'end': 9 },
            { 'type': 'NumberValue', 'value': -30, 'unit': '', 'start': 9, 'end': 12 }
        ])

    def test_float_values(self):
        self.assertEqual(json_tokens('p.5'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': 0.5, 'unit': '', 'start': 1, 'end': 3 }
        ])

        self.assertEqual(json_tokens('p-.5'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': -0.5, 'unit': '', 'start': 1, 'end': 4 }
        ])

        self.assertEqual(json_tokens('p.1.2.3'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': 0.1, 'unit': '', 'start': 1, 'end': 3 },
            { 'type': 'NumberValue', 'value': 0.2, 'unit': '', 'start': 3, 'end': 5 },
            { 'type': 'NumberValue', 'value': 0.3, 'unit': '', 'start': 5, 'end': 7 }
        ])

        self.assertEqual(json_tokens('p.1-.2.3'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': 0.1, 'unit': '', 'start': 1, 'end': 3 },
            { 'type': 'Operator', 'operator': '-', 'start': 3, 'end': 4 },
            { 'type': 'NumberValue', 'value': 0.2, 'unit': '', 'start': 4, 'end': 6 },
            { 'type': 'NumberValue', 'value': 0.3, 'unit': '', 'start': 6, 'end': 8 }
        ])

        self.assertEqual(json_tokens('p.1--.2.3'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': 0.1, 'unit': '', 'start': 1, 'end': 3 },
            { 'type': 'Operator', 'operator': '-', 'start': 3, 'end': 4 },
            { 'type': 'NumberValue', 'value': -0.2, 'unit': '', 'start': 4, 'end': 7 },
            { 'type': 'NumberValue', 'value': 0.3, 'unit': '', 'start': 7, 'end': 9 }
        ])

        self.assertEqual(json_tokens('10'), [
            { 'type': 'NumberValue', 'value': 10, 'unit': '', 'start': 0, 'end': 2 },
        ])

        self.assertEqual(json_tokens('.1'), [
            { 'type': 'NumberValue', 'value': 0.1, 'unit': '', 'start': 0, 'end': 2 },
        ])

        with self.assertRaises(ScannerException):
            tokenize('.foo')

    def test_color_values(self):
        self.assertEqual(json_tokens('c#'), [
            { 'type': 'Literal', 'value': 'c', 'start': 0, 'end': 1 },
            { 'type': 'ColorValue', 'r': 0, 'g': 0, 'b': 0, 'a': 1, 'raw': '', 'start': 1, 'end': 2 }
        ])

        self.assertEqual(json_tokens('c#1'), [
            { 'type': 'Literal', 'value': 'c', 'start': 0, 'end': 1 },
            { 'type': 'ColorValue', 'r': 17, 'g': 17, 'b': 17, 'a': 1, 'raw': '1', 'start': 1, 'end': 3 }
        ])

        self.assertEqual(json_tokens('c#f'), [
            { 'type': 'Literal', 'value': 'c', 'start': 0, 'end': 1 },
            { 'type': 'ColorValue', 'r': 255, 'g': 255, 'b': 255, 'a': 1, 'raw': 'f', 'start': 1, 'end': 3 }
        ])

        self.assertEqual(json_tokens('c#a#b#c'), [
            { 'type': 'Literal', 'value': 'c', 'start': 0, 'end': 1 },
            { 'type': 'ColorValue', 'r': 170, 'g': 170, 'b': 170, 'a': 1, 'raw': 'a', 'start': 1, 'end': 3 },
            { 'type': 'ColorValue', 'r': 187, 'g': 187, 'b': 187, 'a': 1, 'raw': 'b', 'start': 3, 'end': 5 },
            { 'type': 'ColorValue', 'r': 204, 'g': 204, 'b': 204, 'a': 1, 'raw': 'c', 'start': 5, 'end': 7 }
        ])

        self.assertEqual(json_tokens('c#af'), [
            { 'type': 'Literal', 'value': 'c', 'start': 0, 'end': 1 },
            { 'type': 'ColorValue', 'r': 175, 'g': 175, 'b': 175, 'a': 1, 'raw': 'af', 'start': 1, 'end': 4 }
        ])

        self.assertEqual(json_tokens('c#fc0'), [
            { 'type': 'Literal', 'value': 'c', 'start': 0, 'end': 1 },
            { 'type': 'ColorValue', 'r': 255, 'g': 204, 'b': 0, 'a': 1, 'raw': 'fc0', 'start': 1, 'end': 5 }
        ])

        self.assertEqual(json_tokens('c#11.5'), [
            { 'type': 'Literal', 'value': 'c', 'start': 0, 'end': 1 },
            { 'type': 'ColorValue', 'r': 17, 'g': 17, 'b': 17, 'a': 0.5, 'raw': '11.5', 'start': 1, 'end': 6 }
        ])

        self.assertEqual(json_tokens('c#.99'), [
            { 'type': 'Literal', 'value': 'c', 'start': 0, 'end': 1 },
            { 'type': 'ColorValue', 'r': 0, 'g': 0, 'b': 0, 'a': 0.99, 'raw': '.99', 'start': 1, 'end': 5 }
        ])

        self.assertEqual(json_tokens('c#t'), [
            { 'type': 'Literal', 'value': 'c', 'start': 0, 'end': 1 },
            { 'type': 'ColorValue', 'r': 0, 'g': 0, 'b': 0, 'a': 0, 'raw': 't', 'start': 1, 'end': 3 }
        ])

    def test_keywords(self):
        self.assertEqual(json_tokens('m:a'), [
            { 'type': 'Literal', 'value': 'm', 'start': 0, 'end': 1 },
            { 'type': 'Operator', 'operator': ':', 'start': 1, 'end': 2 },
            { 'type': 'Literal', 'value': 'a', 'start': 2, 'end': 3 }
        ])

        self.assertEqual(json_tokens('m-a'), [
            { 'type': 'Literal', 'value': 'm', 'start': 0, 'end': 1 },
            { 'type': 'Operator', 'operator': '-', 'start': 1, 'end': 2 },
            { 'type': 'Literal', 'value': 'a', 'start': 2, 'end': 3 }
        ])

        self.assertEqual(json_tokens('m-abc'), [
            { 'type': 'Literal', 'value': 'm', 'start': 0, 'end': 1 },
            { 'type': 'Operator', 'operator': '-', 'start': 1, 'end': 2 },
            { 'type': 'Literal', 'value': 'abc', 'start': 2, 'end': 5 }
        ])

        self.assertEqual(json_tokens('m-a0'), [
            { 'type': 'Literal', 'value': 'm', 'start': 0, 'end': 1 },
            { 'type': 'Operator', 'operator': '-', 'start': 1, 'end': 2 },
            { 'type': 'Literal', 'value': 'a', 'start': 2, 'end': 3 },
            { 'type': 'NumberValue', 'value': 0, 'unit': '', 'start': 3, 'end': 4 }
        ])

        self.assertEqual(json_tokens('m-a0-a'), [
            { 'type': 'Literal', 'value': 'm', 'start': 0, 'end': 1 },
            { 'type': 'Operator', 'operator': '-', 'start': 1, 'end': 2 },
            { 'type': 'Literal', 'value': 'a', 'start': 2, 'end': 3 },
            { 'type': 'NumberValue', 'value': 0, 'unit': '', 'start': 3, 'end': 4 },
            { 'type': 'Operator', 'operator': '-', 'start': 4, 'end': 5 },
            { 'type': 'Literal', 'value': 'a', 'start': 5, 'end': 6 }
        ])

    def test_arguments(self):
        self.assertEqual(json_tokens('lg(top, "red, black", rgb(0, 0, 0) 10%)'), [
            { 'type': 'Literal', 'value': 'lg', 'start': 0, 'end': 2 },
            { 'type': 'Bracket', 'open': True, 'start': 2, 'end': 3 },
            { 'type': 'Literal', 'value': 'top', 'start': 3, 'end': 6 },
            { 'type': 'Operator', 'operator': ',', 'start': 6, 'end': 7 },
            { 'type': 'WhiteSpace', 'start': 7, 'end': 8 },
            { 'type': 'StringValue', 'value': 'red, black', 'quote': 'double', 'start': 8, 'end': 20 },
            { 'type': 'Operator', 'operator': ',', 'start': 20, 'end': 21 },
            { 'type': 'WhiteSpace', 'start': 21, 'end': 22 },
            { 'type': 'Literal', 'value': 'rgb', 'start': 22, 'end': 25 },
            { 'type': 'Bracket', 'open': True, 'start': 25, 'end': 26 },
            { 'type': 'NumberValue', 'value': 0, 'unit': '', 'start': 26, 'end': 27 },
            { 'type': 'Operator', 'operator': ',', 'start': 27, 'end': 28 },
            { 'type': 'WhiteSpace', 'start': 28, 'end': 29 },
            { 'type': 'NumberValue', 'value': 0, 'unit': '', 'start': 29, 'end': 30 },
            { 'type': 'Operator', 'operator': ',', 'start': 30, 'end': 31 },
            { 'type': 'WhiteSpace', 'start': 31, 'end': 32 },
            { 'type': 'NumberValue', 'value': 0, 'unit': '', 'start': 32, 'end': 33 },
            { 'type': 'Bracket', 'open': False, 'start': 33, 'end': 34 },
            { 'type': 'WhiteSpace', 'start': 34, 'end': 35 },
            { 'type': 'NumberValue', 'value': 10, 'unit': '%', 'start': 35, 'end': 38 },
            { 'type': 'Bracket', 'open': False, 'start': 38, 'end': 39 }
        ])

    def test_important(self):
        self.assertEqual(json_tokens('!'), [
            { 'type': 'Operator', 'operator': '!', 'start': 0, 'end': 1 }
        ])

        self.assertEqual(json_tokens('p!'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'Operator', 'operator': '!', 'start': 1, 'end': 2 }
        ])

        self.assertEqual(json_tokens('p10!'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': 10, 'unit': '', 'start': 1, 'end': 3 },
            { 'type': 'Operator', 'operator': '!', 'start': 3, 'end': 4 }
        ])

    def test_mixed(self):
        self.assertEqual(json_tokens('bd1-s#fc0'), [
            { 'type': 'Literal', 'value': 'bd', 'start': 0, 'end': 2 },
            { 'type': 'NumberValue', 'value': 1, 'unit': '', 'start': 2, 'end': 3 },
            { 'type': 'Operator', 'operator': '-', 'start': 3, 'end': 4 },
            { 'type': 'Literal', 'value': 's', 'start': 4, 'end': 5 },
            { 'type': 'ColorValue', 'r': 255, 'g': 204, 'b': 0, 'a': 1, 'raw': 'fc0', 'start': 5, 'end': 9 }
        ])

        self.assertEqual(json_tokens('bd#fc0-1'), [
            { 'type': 'Literal', 'value': 'bd', 'start': 0, 'end': 2 },
            { 'type': 'ColorValue', 'r': 255, 'g': 204, 'b': 0, 'a': 1, 'raw': 'fc0', 'start': 2, 'end': 6 },
            { 'type': 'Operator', 'operator': '-', 'start': 6, 'end': 7 },
            { 'type': 'NumberValue', 'value': 1, 'unit': '', 'start': 7, 'end': 8 }
        ])

        self.assertEqual(json_tokens('p0+m0'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': 0, 'unit': '', 'start': 1, 'end': 2 },
            { 'type': 'Operator', 'operator': '+', 'start': 2, 'end': 3 },
            { 'type': 'Literal', 'value': 'm', 'start': 3, 'end': 4 },
            { 'type': 'NumberValue', 'value': 0, 'unit': '', 'start': 4, 'end': 5 }
        ])

        self.assertEqual(json_tokens('p0!+m0!'), [
            { 'type': 'Literal', 'value': 'p', 'start': 0, 'end': 1 },
            { 'type': 'NumberValue', 'value': 0, 'unit': '', 'start': 1, 'end': 2 },
            { 'type': 'Operator', 'operator': '!', 'start': 2, 'end': 3 },
            { 'type': 'Operator', 'operator': '+', 'start': 3, 'end': 4 },
            { 'type': 'Literal', 'value': 'm', 'start': 4, 'end': 5 },
            { 'type': 'NumberValue', 'value': 0, 'unit': '', 'start': 5, 'end': 6 },
            { 'type': 'Operator', 'operator': '!', 'start': 6, 'end': 7 }
        ])

        self.assertEqual(json_tokens("${2:0}%"), [
             { 'type': 'Field', 'index': 2, 'name': '0', 'start': 0, 'end': 6 },
             { 'type': 'Literal', 'value': '%', 'start': 6, 'end': 7 }
         ]);

    def test_embedded_variables(self):
        self.assertEqual(json_tokens('foo$bar'), [
            { 'type': 'Literal', 'value': 'foo', 'start': 0, 'end': 3 },
            { 'type': 'Literal', 'value': '$bar', 'start': 3, 'end': 7 }
        ])

        self.assertEqual(json_tokens('foo$bar-2'), [
            { 'type': 'Literal', 'value': 'foo', 'start': 0, 'end': 3 },
            { 'type': 'Literal', 'value': '$bar-2', 'start': 3, 'end': 9 }
        ])

        self.assertEqual(json_tokens('foo$bar@bam'), [
            { 'type': 'Literal', 'value': 'foo', 'start': 0, 'end': 3 },
            { 'type': 'Literal', 'value': '$bar', 'start': 3, 'end': 7 },
            { 'type': 'Literal', 'value': '@bam', 'start': 7, 'end': 11 }
        ])

        self.assertEqual(json_tokens('@k10'), [
            { 'type': 'Literal', 'value': '@k', 'start': 0, 'end': 2 },
            { 'type': 'NumberValue', 'value': 10, 'unit': '', 'start': 2, 'end': 4 }
        ])
