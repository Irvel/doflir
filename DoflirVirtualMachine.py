from collections import deque
from SemanticCube import Ops
from VariablesTable import Variable
from VariablesTable import Params
from VariablesTable import QuadJump
from VariablesTable import Constant
from VariablesTable import Param
from VariablesTable import Pointer

import argparse
import logging
import operator
import pickle

logger = logging.getLogger("doflir_vm_logger")


class DoflirVirtualMachine(object):
    """docstring for DoflirVirtualMachine"""
    def __init__(self, bytecode):
        self.quads = bytecode.quads
        # We initialize the variables table with our constants
        self.fun_dir = bytecode.fun_dir
        self.ip = 0
        self.context_stack = deque()
        self.context_stack.append(bytecode.const_table)

    @property
    def current_quad(self):
        if self.ip < len(self.quads):
            return self.quads[self.ip]
        else:
            return None

    @property
    def current_context(self):
        return self.context_stack[-1]

    def run(self):
        while self.current_quad is not None:
            self.run_quad(self.current_quad)
            self.ip += 1

    def get_val(self, operand):
        if isinstance(operand, Constant):
            return operand.value
        elif isinstance(operand, Pointer):
            pass
        else:
            return self.current_context[operand.address]

    def set_value(self, value, destination):
        if isinstance(destination, Pointer):
            pass
        else:
            logger.debug(
                f"{self.ip:<3} Put {value:<2} into  ({destination.address})"
            )
            self.current_context[destination.address] = value

    def run_quad(self, quad):
        op_method = getattr(self, enum_to_name(quad.op))
        op_method(quad)

    def run_bin_op(self, bin_op, quad):
        left_val, right_val = (self.get_val(quad.left),
                               self.get_val(quad.right))
        res_val = bin_op(left_val, right_val)
        logger.debug(
            f"{self.ip:<3} Do  {left_val:<2} ({bin_op.__name__:3})  "
            f"{right_val:<5} → {res_val}"
        )
        self.set_value(value=res_val, destination=quad.res)

    def plus(self, quad):
        self.run_bin_op(bin_op=operator.add, quad=quad)

    def minus(self, quad):
        self.run_bin_op(bin_op=operator.sub, quad=quad)

    def mult(self, quad):
        self.run_bin_op(bin_op=operator.mul, quad=quad)

    def div(self, quad):
        self.run_bin_op(bin_op=operator.truediv, quad=quad)

    def int_div(self, quad):
        self.run_bin_op(bin_op=operator.floordiv, quad=quad)

    def pow(self, quad):
        self.run_bin_op(bin_op=operator.pow, quad=quad)

    def gt(self, quad):
        self.run_bin_op(bin_op=operator.gt, quad=quad)

    def gt_eq(self, quad):
        self.run_bin_op(bin_op=operator.gt_eq, quad=quad)

    def lt(self, quad):
        self.run_bin_op(bin_op=operator.lt, quad=quad)

    def lt_eq(self, quad):
        self.run_bin_op(bin_op=operator.lt_eq, quad=quad)

    def eq(self, quad):
        self.run_bin_op(bin_op=operator.eq, quad=quad)

    def not_eq(self, quad):
        self.run_bin_op(bin_op=operator.ne, quad=quad)

    def goto(self, quad):
        # IP is always incremented after running a quad, so we sub 1
        self.ip = quad.res.value - 1

    def gotof(self, quad):
        if not self.get_val(quad.left):
            self.goto(quad)

    def assign(self, quad):
        self.set_value(value=self.get_val(quad.left), destination=quad.res)

    def print(self, quad):
        print(self.get_val(quad.res))


def enum_to_name(enum):
    return enum.name.lower()


def setup_logging(debug):
    if debug:
        logger.setLevel(logging.DEBUG)
    FORMAT = "%(levelname)s: %(message)s"
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(console)


def main():
    parser = argparse.ArgumentParser(description="Doflir VM")
    parser.add_argument("in_file",
                        type=str, help="Filename of Doflir obj to run")
    parser.add_argument("--debug", type=bool, default=False, required=False,
                        help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(args.debug)
    bytecode = read_bytecode(filename=args.in_file)
    run_program(bytecode)


def read_bytecode(filename):
    with open(filename, "rb") as f:
        bytecode = pickle.load(f)
    return bytecode


def run_program(bytecode):
    doflir_vm = DoflirVirtualMachine(bytecode)
    doflir_vm.run()


if __name__ == "__main__":
    main()
