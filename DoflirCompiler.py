from DoflirCustomVisitor import DoflirCustomVisitor
from DoflirErrorListener import DoflirErrorListener
from DoflirLexer import DoflirLexer
from DoflirParser import DoflirParser

import antlr4
import argparse
import logging
import io
import pickle


def read_input():
    parser = argparse.ArgumentParser(description="Doflir Compiler")
    parser.add_argument("in_file",
                        type=str, help="Filename of Doflir program to compile")
    args = parser.parse_args()
    print(f"Compiling {args.in_file}...\n")
    input_file = open(args.in_file, "r")
    return args.in_file, input_file.read()


def make_obj_filename(in_filename):
    chunks = in_filename.split(".")[:-1]
    chunks.append(".obj")
    return "".join(chunks)


def write_bytecode(bytecode, filename):
    with open(filename, "wb") as f:
        pickle.dump(bytecode, f, pickle.HIGHEST_PROTOCOL)


def main():
    in_filename, input_code = read_input()
    bytecode = doflir_compile(input_code)
    out_filename = make_obj_filename(in_filename)
    write_bytecode(bytecode, out_filename)
    print("\n" + input_code)
    print(f'Saved bytecode to "{out_filename}"!')


def doflir_compile(input_code):
    lexer = DoflirLexer(antlr4.InputStream(input_code))
    tokens = antlr4.CommonTokenStream(lexer)
    parser = DoflirParser(tokens)
    visitor = DoflirCustomVisitor()

    # parser.removeErrorListeners()
    # self.error = io.StringIO()
    error_listener = DoflirErrorListener(io.StringIO())
    parser.addErrorListener(error_listener)
    return visitor.visit(tree=parser.program())


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
