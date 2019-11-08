from DoflirCustomVisitor import DoflirCustomVisitor
from DoflirErrorListener import DoflirErrorListener
from DoflirLexer import DoflirLexer
from DoflirParser import DoflirParser

import antlr4
import argparse
import logging
import io


def read_input():
    parser = argparse.ArgumentParser(description="Doflir Compiler")
    parser.add_argument("in_file",
                        type=str, help="Filename of Doflir program to compile")
    args = parser.parse_args()
    print(f"Compiling {args.in_file}...\n")
    input_file = open(args.in_file, "r")
    return input_file.read()


def main():
    input_code = read_input()
    doflir_compile(input_code)
    print("\n" + input_code)


def doflir_compile(input_code):
    lexer = DoflirLexer(antlr4.InputStream(input_code))
    tokens = antlr4.CommonTokenStream(lexer)
    parser = DoflirParser(tokens)
    visitor = DoflirCustomVisitor()

    # parser.removeErrorListeners()
    # self.error = io.StringIO()
    error_listener = DoflirErrorListener(io.StringIO())
    parser.addErrorListener(error_listener)
    visitor.visit(tree=parser.program())


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
