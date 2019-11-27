from DoflirCustomVisitor import DoflirCustomVisitor
from DoflirErrorListener import DoflirErrorListener
from DoflirLexer import DoflirLexer
from DoflirParser import DoflirParser

import antlr4
import argparse
import logging
import io
import pickle


def parse_arguments():
    """Read arguments passed by the user."""
    parser = argparse.ArgumentParser(description="Doflir Compiler")
    parser.add_argument("in_file",
                        type=str, help="Filename of Doflir program to compile")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    return args.in_file, args.debug


def read_input(filename):
    """Return the input program from storage."""
    with open(filename, "r") as input_file:
        in_code = input_file.read()
    return in_code


def make_obj_filename(in_filename):
    """Set a .obj extension to the input filename for the bytecode output."""
    chunks = in_filename.split(".")[:-1]
    chunks.append(".obj")
    return "".join(chunks)


def write_bytecode(bytecode, filename):
    """Write the bytecode output from the compilation."""
    with open(filename, "wb") as f:
        pickle.dump(bytecode, f, pickle.HIGHEST_PROTOCOL)


def make_obj_code(in_filename, debug=False):
    """Driver for compilation given an input filename to be read."""
    input_code = read_input(in_filename)
    in_filename = str(in_filename)
    bytecode = doflir_compile(in_filename, input_code, debug)
    out_filename = make_obj_filename(in_filename)
    write_bytecode(bytecode, out_filename)
    if debug:
        print("\n" + input_code)
    print(f'Saved bytecode to "{out_filename}"!')


def console_run():
    """Driver for running compilation from the console."""
    in_filename, debug = parse_arguments()
    make_obj_code(in_filename, debug)


def doflir_compile(in_filename, input_code, debug):
    """Main entry point for the compilation process of a Doflir program."""
    lexer = DoflirLexer(antlr4.InputStream(input_code))
    tokens = antlr4.CommonTokenStream(lexer)
    parser = DoflirParser(tokens)
    visitor = DoflirCustomVisitor(str(in_filename), input_code, debug)

    error_listener = DoflirErrorListener(io.StringIO())
    parser.addErrorListener(error_listener)
    return visitor.visit(tree=parser.program())


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    console_run()
