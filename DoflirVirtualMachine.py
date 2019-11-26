from collections import deque
from SemanticCube import Ops
from VariablesTable import Variable
from VariablesTable import Params
from VariablesTable import QuadJump
from VariablesTable import Constant
from VariablesTable import Param
from VariablesTable import Pointer
from VariablesTable import VecIdx
from VariablesTable import VarTypes

import argparse
import csv
import numpy as np
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
        self.np_type_map = {
            VarTypes.INT: np.int,
            VarTypes.FLOAT: np.float,
            VarTypes.BOOL: np.bool,
            VarTypes.STRING: "<U20",
        }
        self.lit_type_map = {
            VarTypes.INT: int,
            VarTypes.FLOAT: float,
            VarTypes.BOOL: bool,
            VarTypes.STRING: str,
        }

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
        elif isinstance(operand, VecIdx):
            idx_val = tuple([self.get_val(idx) for idx in operand.idx])
            if operand.address in self.current_context:
                return self.current_context[operand.address][idx_val]
            elif operand.address in self.global_context:
                return self.global_context[operand.address][idx_val]
        else:
            if operand.address in self.current_context:
                return self.current_context[operand.address]
            elif operand.address in self.global_context:
                return self.global_context[operand.address]

    def set_value(self, value, dst, global_ctx=False, temp_ctx=False):
        if isinstance(dst, VecIdx):
            idx_val = tuple([self.get_val(idx) for idx in dst.idx])
            if global_ctx or dst.address in self.global_context:
                self.global_context[dst.address][idx_val] = value
            elif temp_ctx:
                self.temp_context[dst.address][idx_val] = value
            else:
                self.current_context[dst.address][idx_val] = value
        else:
            if global_ctx:
                self.global_context[dst.address] = value
            elif temp_ctx:
                self.temp_context[dst.address] = value
            else:
                self.current_context[dst.address] = value

    def run_quad(self, quad):
        op_method = getattr(self, enum_to_name(quad.op))
        op_method(quad)

    def neg(self, quad):
        res_val = -(self.get_val(quad.left))
        self.set_value(value=res_val, dst=quad.res)

    def pos(self, quad):
        res_val = +(self.get_val(quad.left))
        self.set_value(value=res_val, dst=quad.res)

    def run_bin_op(self, bin_op, quad):
        left_val, right_val = (self.get_val(quad.left),
                               self.get_val(quad.right))
        res_val = bin_op(left_val, right_val)
        logger.debug(
            f"{self.ip:<3} Do  {str(left_val):<3} ({bin_op.__name__:3})  "
            f"{str(right_val):<5} → {str(res_val)}"
        )
        logger.debug(
            f"{self.ip:<3} Put {str(res_val):<3} into  ({str(quad.res)})"
        )
        self.set_value(value=res_val, dst=quad.res)

    def plus(self, quad):
        self.run_bin_op(bin_op=operator.add, quad=quad)

    def minus(self, quad):
        self.run_bin_op(bin_op=operator.sub, quad=quad)

    def mat_mult(self, quad):
        self.run_bin_op(bin_op=np.matmul, quad=quad)

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
        assign_val = self.get_val(quad.left)
        val_str = str(assign_val).replace("\n", "")
        logger.debug(
            f"{self.ip:<3} Assign   {val_str:<3} to "
            f"  ({quad.res.address})"
        )
        self.set_value(value=assign_val, dst=quad.res)

    def print(self, quad):
        print(self.get_val(quad.res), end="")

    def println(self, quad):
        print(self.get_val(quad.res))

    def readc(self, quad):
        in_raw = input()
        target_type = self.lit_type_map[quad.res.data_type]
        assign_val = None
        try:
            assign_val = target_type(in_raw)
        except Exception:
            raise Exception("Provided different type to the expected one")
        self.set_value(value=assign_val, dst=quad.res)

    def readt(self, quad):
        target_type = self.np_type_map[quad.res.data_type]
        table = np.genfromtxt(
            self.get_val(quad.left),
            dtype=target_type, delimiter=","
        )
        self.set_value(value=table, dst=quad.res)

    def reada(self, quad):
        self.readt(quad)

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
                     f"({param_target.address})({self.get_val(quad.left)})  ")
        self.set_value(value=self.get_val(quad.left),
                       dst=param_target,
                       temp_ctx=True)

    def gosub(self, quad):
        self.context_stack.append(self.temp_context)
        self.temp_context = None
        self.pending_return_jump.append(self.ip)
        self._goto(quad_idx=quad.left.quad_idx)

    def return_(self, quad):
        logger.debug(
            f"{self.ip:<3} Return {self.get_val(quad.res):<3})"
        )
        self.set_value(
            value=self.get_val(quad.res),
            dst=self.pending_return_val[-1],
            global_ctx=True,
        )

    def endproc(self, quad):
        self.context_stack.pop()
        if self.pending_return_val:
            self.pending_return_val.pop()
        old_ip = self.ip
        self.ip = self.pending_return_jump.pop()
        logger.debug(f"{old_ip:<3} Set ip to    ({self.ip})  ")

    def alloc(self, quad):
        spec = quad.res
        vec_shape = [self.get_val(d) for d in spec.vec_dims]
        vec_type = self.np_type_map[spec.data_type]
        logger.debug(f"{self.ip:<3} ALLOC   {spec.name}({spec.address})"
                     f"({vec_shape})  ")
        self.set_value(
            value=np.zeros(shape=vec_shape, dtype=vec_type),
            dst=spec,
        )

    def ver(self, quad):
        val_to_ver, upper_lim = (self.get_val(quad.left),
                                 self.get_val(quad.res))
        if val_to_ver < 0 or val_to_ver >= upper_lim:
            raise Exception("Out of bounds access.")
        logger.debug(f"{self.ip:<3} VER     {val_to_ver} < {upper_lim}  ")

    def run_filter_op(self, vec_filter, quad):
        vector = self.get_val(quad.left)
        res_val = vec_filter(vector)
        logger.debug(
            f"{self.ip:<3} Filter  vec with {vec_filter.__name__:<3} "
        )
        self.set_value(value=res_val, dst=quad.res)

    def f_sum(self, quad):
        self.run_filter_op(vec_filter=np.sum, quad=quad)


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
