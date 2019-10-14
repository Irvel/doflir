from DoflirLexer import DoflirLexer
from DoflirParser import DoflirParser
from DoflirVisitor import DoflirVisitor
# from HtmlChatListener import HtmlChatListener
from DoflirErrorListener import DoflirErrorListener
import antlr4
import unittest
import io


class DoflirSimpleVisitor(DoflirVisitor):
    def visitProgram(self, ctx: DoflirParser.ProgramContext):
        # print(list(ctx.getChildren()))
        stat = ctx.statement()
        print(list(stat)[0])
        print(self.visitChildren(ctx))
        return self.visitChildren(ctx)


class TestDoflirParser(unittest.TestCase):
    def run_parser(self, text):
        lexer = DoflirLexer(antlr4.InputStream(text))
        tokens = antlr4.CommonTokenStream(lexer)
        parser = DoflirParser(tokens)
        visitor = DoflirVisitor()

        parser.removeErrorListeners()
        self.error = io.StringIO()
        error_listener = DoflirErrorListener(self.error)
        parser.addErrorListener(error_listener)
        visitor.visit(tree=parser.program())

        return error_listener

    def test_valid_int_function(self):
        test_string = """
            define test_function -> int(param) {
                return 0;
            }
        """
        err_l = self.run_parser(test_string)
        self.assertEqual(len(err_l.symbol), 0, msg=err_l.output.getvalue())

    def test_valid_void_function(self):
        test_string = """
            define test_function -> void(param) {
                return;
            }
        """
        err_l = self.run_parser(test_string)
        self.assertEqual(len(err_l.symbol), 0, msg=err_l.output.getvalue())

    def test_invalid_ret_function(self):
        test_string = """
            define test_function -> int(param) {

            }
        """
        err_l = self.run_parser(test_string)
        self.assertNotEqual(len(err_l.symbol), 0, msg=err_l.output.getvalue())

    def test_valid_assignment(self):
        test_string = "number = 293;"
        err_l = self.run_parser(test_string)
        self.assertEqual(len(err_l.symbol), 0, msg=err_l.output.getvalue())

        test_string = "number = (true and false) or true;"
        err_l = self.run_parser(test_string)
        self.assertEqual(len(err_l.symbol), 0, msg=err_l.output.getvalue())

    def test_invalid_assignment(self):
        test_string = "number = 293"
        err_l = self.run_parser(test_string)
        self.assertNotEqual(len(err_l.symbol), 0, msg=err_l.output.getvalue())

        test_string = "202 = 293"
        err_l = self.run_parser(test_string)
        self.assertNotEqual(len(err_l.symbol), 0, msg=err_l.output.getvalue())

    def test_valid_vec(self):
        test_string = "nums = [1, 2, 3, 4];"
        err_l = self.run_parser(test_string)
        self.assertEqual(len(err_l.symbol), 0, msg=err_l.output.getvalue())

        test_string = "floats = [.31, 2.2, .23, .34];"
        err_l = self.run_parser(test_string)
        self.assertEqual(len(err_l.symbol), 0, msg=err_l.output.getvalue())

        test_string = 'strings = ["dsaon", "", "2te3", "ttosa"];'
        err_l = self.run_parser(test_string)
        self.assertEqual(len(err_l.symbol), 0, msg=err_l.output.getvalue())

        test_string = "vecs = [[], [], [], [[], [], []]];"
        err_l = self.run_parser(test_string)
        self.assertEqual(len(err_l.symbol), 0, msg=err_l.output.getvalue())

    def test_invalid_vec(self):
        test_string = "nums = [1, 2, 3, 4]"
        err_l = self.run_parser(test_string)
        self.assertNotEqual(len(err_l.symbol), 0, msg=err_l.output.getvalue())

        test_string = "nums = [1, 2, 3, 4)"
        err_l = self.run_parser(test_string)
        self.assertNotEqual(len(err_l.symbol), 0, msg=err_l.output.getvalue())

    def test_valid_prog(self):
        test_string = r"""
            define test_function1 -> int(param) {
                return 3;
            }

            define test_function2 -> float(param1, param2, param3 = 5) {
                res1 = test_function1(302);
                res2 = test_function1(302 * 2002);
                res3 = (test_function1(302) * 203 + 2932 / 293) * .023;
                return res1 * (res2 - res3);
            }

            define test_function3 -> vector() {
                vec = [1, 2, 3, 4];
                vec2 = vec{test_function1};
                return 3;
            }

            test_function2(2, 4);
        """
        err_l = self.run_parser(test_string)
        self.assertEqual(len(err_l.symbol), 0, msg=err_l.output.getvalue())


if __name__ == "__main__":
    unittest.main()
