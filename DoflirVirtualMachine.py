from collections import deque
from SemanticCube import Ops
from VariablesTable import Variable
from VariablesTable import Params
from VariablesTable import QuadJump
from VariablesTable import Constant
from VariablesTable import Param
from VariablesTable import Pointer
from VariablesTable import VarTypes

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
        self.temp_context = None
        self.pending_params_stack = deque()
        self.pending_return_jump = deque()
        self.pending_return_val = deque()

    @property
    def current_quad(self):
        if self.ip < len(self.quads):
            return self.quads[self.ip]
        else:
            return None

    @property
    def current_context(self):
        return self.context_stack[-1]

    @property
    def global_context(self):
        return self.context_stack[0]

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
            if operand.address in self.current_context:
                return self.current_context[operand.address]
            elif operand.address in self.global_context:
                return self.global_context[operand.address]

    def set_value(self, value, destination, global_ctx=False, temp_ctx=False):
        if isinstance(destination, Pointer):
            pass
        else:
            logger.debug(
                f"{self.ip:<3} Put {value:<3} into  ({destination.address})"
            )
            if global_ctx:
                self.global_context[destination.address] = value
            elif temp_ctx:
                self.temp_context[destination.address] = value
            else:
                self.current_context[destination.address] = value

    def run_quad(self, quad):
        op_method = getattr(self, enum_to_name(quad.op))
        op_method(quad)

    def run_bin_op(self, bin_op, quad):
        left_val, right_val = (self.get_val(quad.left),
                               self.get_val(quad.right))
        res_val = bin_op(left_val, right_val)
        logger.debug(
            f"{self.ip:<3} Do  {left_val:<3} ({bin_op.__name__:3})  "
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

    def and_(self, quad):
        self.run_bin_op(bin_op=operator.and_, quad=quad)

    def or_(self, quad):
        self.run_bin_op(bin_op=operator.or_, quad=quad)

    def gt(self, quad):
        self.run_bin_op(bin_op=operator.gt, quad=quad)

    def gt_eq(self, quad):
        self.run_bin_op(bin_op=operator.ge, quad=quad)

    def lt(self, quad):
        self.run_bin_op(bin_op=operator.lt, quad=quad)

    def lt_eq(self, quad):
        self.run_bin_op(bin_op=operator.le, quad=quad)

    def eq(self, quad):
        self.run_bin_op(bin_op=operator.eq, quad=quad)

    def not_eq(self, quad):
        self.run_bin_op(bin_op=operator.ne, quad=quad)

    def _goto(self, quad_idx):
        logger.debug(f"{self.ip:<3} Jmp  to quad ({quad_idx})  ")
        # IP is always incremented after running a quad, so we sub 1
        self.ip = quad_idx - 1

    def goto(self, quad):
        self._goto(quad_idx=quad.res.value)

    def gotof(self, quad):
        if not self.get_val(quad.left):
            self.goto(quad)

    def assign(self, quad):
        self.set_value(value=self.get_val(quad.left), destination=quad.res)

    def print(self, quad):
        print(self.get_val(quad.res))

    def era(self, quad):
        self.temp_context = {}
        logger.debug(f"{self.ip:<3} ERA To    {quad.left.name}  ")

        function = self.fun_dir.search(quad.left.name)
        if function.params:
            for param in function.params[::-1]:
                self.pending_params_stack.append(param)
        if function.ret_type != VarTypes.VOID:
            self.pending_return_val.append(function)

    def param(self, quad):
        param_target = self.pending_params_stack.pop()
        logger.debug(f"{self.ip:<3} Set param {param_target.param_id}"
                     f"({param_target.address})  ")
        self.set_value(value=self.get_val(quad.left),
                       destination=param_target,
                       temp_ctx=True)

    def gosub(self, quad):
        self.context_stack.append(self.temp_context)
        self.temp_context = None
        self.pending_return_jump.append(self.ip)
        self._goto(quad_idx=quad.left.quad_idx)

    def return_(self, quad):
        self.set_value(
            value=self.get_val(quad.res),
            destination=self.pending_return_val.pop(),
            global_ctx=True,
        )

    def endproc(self, quad):
        self.context_stack.pop()
        old_ip = self.ip
        self.ip = self.pending_return_jump.pop()
        logger.debug(f"{old_ip:<3} Set ip to    ({self.ip})  ")


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
