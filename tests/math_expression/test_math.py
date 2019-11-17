import unittest
import sys

sys.path.append('../../')

from emmet.math_expression import evaluate, MathExpressionException

class TestMathEvaluate(unittest.TestCase):
    def test_eval_basic_math(self):
        self.assertEqual(evaluate('1+2'), 3)
        self.assertEqual(evaluate('1 + 2'), 3)
        self.assertEqual(evaluate('2 * 3'), 6)
        self.assertEqual(evaluate('2 * 3 + 1'), 7)
        self.assertEqual(evaluate('-2 * 3 + 1'), -5)
        self.assertEqual(evaluate('2 * -3 + 1'), -5)
        self.assertEqual(evaluate('5 / 2'), 2.5)
        self.assertEqual(evaluate('5 \\ 2'), 2)

    def test_eval_parenthesis_math(self):
        self.assertEqual(evaluate('2 * (3 + 1)'), 8)
        self.assertEqual(evaluate('(3 * (1+2)) * 2'), 18)
        self.assertEqual(evaluate('3 * -(1 + 2)'), -9)
        self.assertEqual(evaluate('(1 + 2) * 3'), 9)

    def test_parse_errors(self):
        with self.assertRaisesRegex(MathExpressionException, 'Unknown character'):
            evaluate('a+b')

        with self.assertRaisesRegex(MathExpressionException, 'Unknown character'):
            evaluate('1/b')

        with self.assertRaisesRegex(MathExpressionException, 'Unmatched'):
            evaluate('(1 + 3')
