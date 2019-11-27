from collections import deque
from VariablesTable import Constant
from VariablesTable import VecIdx
from VariablesTable import VarTypes

import argparse
import numpy as np
import matplotlib.pyplot as plt
import logging
import operator
import pickle

logger = logging.getLogger("doflir_vm_logger")
np.set_printoptions(suppress=True)


class DoflirVirtualMachine(object):
    """VM that Interprets Doflir bytecode and executes it."""
    def __init__(self, bytecode):
        # The list of quadruples in their intermediate representation form.
        self.quads = bytecode.quads
        # Store the function directory for keeping track of activation records.
        self.fun_dir = bytecode.fun_dir
        # The general instruction pointer.
        self.ip = 0
        # A stack to hold memory contexts that get activated with functions.
        self.context_stack = deque()
        # Our base global context is aware of all of the constants.
        self.context_stack.append(bytecode.const_table)
        # A stack of temporal contexts where parameters are placed on before
        # switching to the context within a procedure. Given that multiple
        # activation records can be happen before a call to gosub, we need
        # a stack to keep track of the argument - parameter assignments.
        self.temp_contexts = deque()
        # A stack of pending parameters that are to be assigned before gosub.
        self.pending_params_stack = deque()
        # A stack that keeps track of our previous ip before making a jump
        # with gosub. It allows us to return to that prevous point later.
        self.pending_return_jump = deque()
        # Stack to keep track of whether the function is pending to return
        # a value upon completion.
        self.pending_return_val = deque()
        # Map of Doflir types to numpy types.
        self.np_type_map = {
            VarTypes.INT: np.int,
            VarTypes.FLOAT: np.float,
            VarTypes.BOOL: np.bool,
            VarTypes.STRING: "<U20",
        }
        # Map of Doflir types to Python types.
        self.lit_type_map = {
            VarTypes.INT: int,
            VarTypes.FLOAT: float,
            VarTypes.BOOL: bool,
            VarTypes.STRING: str,
        }

    @property
    def current_quad(self):
        """Returns the current quad where the instruction pointer is in."""
        if self.ip < len(self.quads):
            return self.quads[self.ip]
        else:
            return None

    @property
    def current_context(self):
        """Returns the context located at the top of the context_stack."""
        return self.context_stack[-1]

    @property
    def global_context(self):
        """Returns the first context in the context_stack."""
        return self.context_stack[0]

    @property
    def temp_context(self):
        """Returns the context located at the top of the temp_stack."""
        return self.temp_contexts[-1]

    def run(self):
        """Main loop for execution."""
        while self.current_quad is not None:
            self.run_quad(self.current_quad)
            self.ip += 1

    def get_val(self, operand):
        """Resolve and fetch the actual value from memory."""
        if isinstance(operand, Constant):
            # Constants are represented directly.
            return operand.value
        elif isinstance(operand, VecIdx):
            idx_val = tuple([self.get_val(idx) for idx in operand.idx])
            # Search in both the current local context and the global context.
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
        # Set a value in memory.
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
        """Execute a method that matches the quad Operation name."""
        op_method = getattr(self, enum_to_name(quad.op))
        op_method(quad)

    def neg(self, quad):
        """Unary numeric negation operation. -(1) turns into -1."""
        res_val = -(self.get_val(quad.left))
        self.set_value(value=res_val, dst=quad.res)

    def pos(self, quad):
        """Unary numeric positive operation. +(1) turns into +1."""
        res_val = +(self.get_val(quad.left))
        self.set_value(value=res_val, dst=quad.res)

    def not_(self, quad):
        """Boolean unary negation operation. true turns into false."""
        res_val = not (self.get_val(quad.left))
        self.set_value(value=res_val, dst=quad.res)

    def run_bin_op(self, bin_op, quad):
        """Run a binary operation with the provided quad and op."""
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
        """Addition operation between two operands."""
        self.run_bin_op(bin_op=operator.add, quad=quad)

    def minus(self, quad):
        """Subtraction operation between two operands."""
        self.run_bin_op(bin_op=operator.sub, quad=quad)

    def mat_mult(self, quad):
        """Matrix multiplication between two matrixes."""
        self.run_bin_op(bin_op=np.matmul, quad=quad)

    def dot(self, quad):
        """Dot product between two matrixes."""
        self.run_bin_op(bin_op=np.dot, quad=quad)

    def mult(self, quad):
        """Multiplication operation between two operands."""
        self.run_bin_op(bin_op=operator.mul, quad=quad)

    def div(self, quad):
        """Float division operation between two operands."""
        self.run_bin_op(bin_op=operator.truediv, quad=quad)

    def int_div(self, quad):
        """Integer division operation between two operands."""
        self.run_bin_op(bin_op=operator.floordiv, quad=quad)

    def pow(self, quad):
        """Power operation between two operands."""
        self.run_bin_op(bin_op=operator.pow, quad=quad)

    def and_(self, quad):
        """Logical and relop between two operands."""
        self.run_bin_op(bin_op=operator.and_, quad=quad)

    def or_(self, quad):
        """Logical or relop between two operands."""
        self.run_bin_op(bin_op=operator.or_, quad=quad)

    def gt(self, quad):
        """Logical greater than relop between two operands."""
        self.run_bin_op(bin_op=operator.gt, quad=quad)

    def gt_eq(self, quad):
        """Logical greater than or equal relop between two operands."""
        self.run_bin_op(bin_op=operator.ge, quad=quad)

    def lt(self, quad):
        """Logical less than relop between two operands."""
        self.run_bin_op(bin_op=operator.lt, quad=quad)

    def lt_eq(self, quad):
        """Logical less than or equal relop between two operands."""
        self.run_bin_op(bin_op=operator.le, quad=quad)

    def eq(self, quad):
        """Logical equal relop between two operands."""
        self.run_bin_op(bin_op=operator.eq, quad=quad)

    def not_eq(self, quad):
        """Logical not equal relop between two operands."""
        self.run_bin_op(bin_op=operator.ne, quad=quad)

    def _goto(self, quad_idx):
        """Set the instruction pointer to an arbitrary instruction."""
        logger.debug(f"{self.ip:<3} Jmp  to quad ({quad_idx})  ")
        # IP is always incremented after running a quad, so we sub 1
        self.ip = quad_idx - 1

    def goto(self, quad):
        """Handler for the goto function call."""
        self._goto(quad_idx=quad.res.value)

    def gotof(self, quad):
        """Set the instruction pointer to an arbitrary instruction if false."""
        if not self.get_val(quad.left):
            self.goto(quad)

    def assign(self, quad):
        """Set the value of one operand as the value of another operand """
        assign_val = self.get_val(quad.left)
        val_str = str(assign_val).replace("\n", "")
        logger.debug(
            f"{self.ip:<3} Assign   {val_str:<3} to "
            f"  ({quad.res.address})"
        )
        self.set_value(value=assign_val, dst=quad.res)

    def print(self, quad):
        """Display operand to console."""
        print(self.get_val(quad.res), end="")

    def println(self, quad):
        """Display opearnd to console and append a newline."""
        print(self.get_val(quad.res))

    def plot(self, quad):
        """Graphically plot the operand."""
        plt.plot(self.get_val(quad.res))
        plt.show()

    def writef(self, quad):
        """Write to file."""
        data = self.get_val(quad.left)
        filename = self.get_val(quad.res)
        np.savetxt(filename, data, delimiter=" ", fmt="%s")

    def readc(self, quad):
        """Read input value from console."""
        in_raw = input()
        target_type = self.lit_type_map[quad.res.data_type]
        assign_val = None
        try:
            assign_val = target_type(in_raw)
        except Exception:
            raise Exception("Provided different type to the expected one")
        self.set_value(value=assign_val, dst=quad.res)

    def readt(self, quad):
        """Read input table from a file."""
        target_type = self.np_type_map[quad.res.data_type]
        table = np.genfromtxt(
            self.get_val(quad.left),
            dtype=target_type, delimiter=","
        )
        self.set_value(value=table, dst=quad.res)

    def reada(self, quad):
        """Read input array from a file."""
        self.readt(quad)

    def era(self, quad):
        """Expand the activation table from the function in the operand."""
        self.temp_contexts.append({})
        logger.debug(f"{self.ip:<3} ERA To    {quad.left.name}  ")

        function = self.fun_dir.search(quad.left.name)
        if function.params:
            for param in function.params[::-1]:
                self.pending_params_stack.append(param)
        if function.ret_type != VarTypes.VOID:
            self.pending_return_val.append(function)

    def param(self, quad):
        """Pass an argument towards a parameter of a function."""
        param_target = self.pending_params_stack.pop()
        logger.debug(f"{self.ip:<3} Set param {param_target.param_id}"
                     f"({param_target.address})({self.get_val(quad.left)})  ")
        self.set_value(value=self.get_val(quad.left),
                       dst=param_target,
                       temp_ctx=True)

    def gosub(self, quad):
        """Activate the context of a function and switch the ip to it."""
        self.context_stack.append(self.temp_context)
        self.temp_contexts.pop()
        self.pending_return_jump.append(self.ip)
        self._goto(quad_idx=quad.left.quad_idx)

    def return_(self, quad):
        """Assign return value for a function."""
        logger.debug(
            f"{self.ip:<3} Return {self.get_val(quad.res):<3})"
        )
        self.set_value(
            value=self.get_val(quad.res),
            dst=self.pending_return_val[-1],
            global_ctx=True,
        )

    def endproc(self, quad):
        """Finish execution of a procedure and move back the ip."""
        self.context_stack.pop()
        if self.pending_return_val:
            self.pending_return_val.pop()
        old_ip = self.ip
        self.ip = self.pending_return_jump.pop()
        logger.debug(f"{old_ip:<3} Set ip to    ({self.ip})  ")

    def alloc(self, quad):
        """Inflate a vector in memory."""
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
        """Check that the operand dimensions are within the vector bounds."""
        val_to_ver, upper_lim = (self.get_val(quad.left),
                                 self.get_val(quad.res))
        if val_to_ver < 0 or val_to_ver >= upper_lim:
            raise Exception("Out of bounds access.")
        logger.debug(f"{self.ip:<3} VER     {val_to_ver} < {upper_lim}  ")

    def run_filter_op(self, vec_filter, quad):
        """Run a unary filter operation on the operand vector."""
        vector = self.get_val(quad.left)
        res_val = vec_filter(vector)
        logger.debug(
            f"{self.ip:<3} Filter  vec with {vec_filter.__name__:<3} "
        )
        self.set_value(value=res_val, dst=quad.res)

    def f_sum(self, quad):
        """Sum all of the elements of a vector into a single value."""
        self.run_filter_op(vec_filter=np.sum, quad=quad)

    def f_mean(self, quad):
        """Compute the average of the elements in a vector"""
        self.run_filter_op(vec_filter=np.mean, quad=quad)

    def f_var(self, quad):
        """Compute the variance of the elements in a vector"""
        self.run_filter_op(vec_filter=np.var, quad=quad)

    def f_min(self, quad):
        """Find the minimum of the elements in a vector"""
        self.run_filter_op(vec_filter=np.min, quad=quad)

    def f_max(self, quad):
        """Find the maximum of the elements in a vector"""
        self.run_filter_op(vec_filter=np.max, quad=quad)

    def f_std(self, quad):
        """Compute the sandard dev of the elements in a vector"""
        self.run_filter_op(vec_filter=np.std, quad=quad)

    def f_normalize(self, quad):
        """Compute the normalized vector version of the elements in a vector"""
        self.run_filter_op(vec_filter=normalize, quad=quad)

    def f_square(self, quad):
        """Compute the squared vector version of the elements in a vector"""
        self.run_filter_op(vec_filter=np.square, quad=quad)

    def f_cube(self, quad):
        """Compute the cubed vector version of the elements in a vector"""
        self.run_filter_op(vec_filter=cube, quad=quad)

    def f_strip(self, quad):
        """Remove trailing whitespace from elements in vector."""
        self.run_filter_op(vec_filter=vec_strip, quad=quad)

    def f_lowercase(self, quad):
        """Convert all characters to lowercase."""
        self.run_filter_op(vec_filter=vec_lower, quad=quad)

    def f_uppercase(self, quad):
        """Convert all characters to uppercase"""
        self.run_filter_op(vec_filter=vec_upper, quad=quad)

    def f_sort(self, quad):
        """Sort the elements of a vector."""
        self.run_filter_op(vec_filter=np.sort, quad=quad)

    def f_reverse(self, quad):
        """Reverse the elements of a vector."""
        self.run_filter_op(vec_filter=vec_reverse, quad=quad)


def vec_strip(vector):
    """Remove trailing whitespace from elements in vector."""
    stripped = []
    for val in vector:
        stripped.append(str(val).strip())
    return stripped


def vec_lower(vector):
    """Convert all characters to lowercase."""
    lowered = []
    for val in vector:
        lowered.append(str(val).lower())
    return lowered


def vec_upper(vector):
    """Convert all characters to uppercase"""
    uppered = []
    for val in vector:
        uppered.append(str(val).upper())
    return uppered


def vec_reverse(vector):
    """Reverse the elements of a vector."""
    return vector[::-1]


def cube(vector):
    """Compute the cubed vector version of the elements in a vector"""
    return vector * vector * vector


def normalize(vector):
    """Compute the normalized vector version of the elements in a vector"""
    return vector / np.linalg.norm(vector)


def enum_to_name(enum):
    """Convert an enum into a function-like name."""
    return enum.name.lower()


def setup_logging(debug):
    """Configure level and format of log messages"""
    if debug:
        logger.setLevel(logging.DEBUG)
    FORMAT = "%(levelname)s: %(message)s"
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(console)


def main():
    """Configure options parsed at the begginnig of the program."""
    parser = argparse.ArgumentParser(description="Doflir VM")
    parser.add_argument("in_file",
                        type=str, help="Filename of Doflir obj to run")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(args.debug)
    bytecode = read_bytecode(filename=args.in_file)
    run_program(bytecode)


def read_bytecode(filename):
    """Read the intermediate representation produced by DoflirCompiler."""
    with open(filename, "rb") as f:
        bytecode = pickle.load(f)
    return bytecode


def run_program(bytecode):
    doflir_vm = DoflirVirtualMachine(bytecode)
    doflir_vm.run()


if __name__ == "__main__":
    main()
