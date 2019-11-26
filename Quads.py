from enum import Enum, auto
from VariablesTable import Pointer
from VariablesTable import Variable
from VariablesTable import Param
from VariablesTable import QuadJump
from VariablesTable import Constant
from VariablesTable import Temporal
from VariablesTable import Function


import collections


class QuadOpType(Enum):
    ADDRESS = auto()
    REFERENCE = auto()
    QUAD_IDX = auto()
    CONST = auto()
    PARAM_NUM = auto()


QuadOp = collections.namedtuple("QuadOp", "value op_type")


class Quad:
    def __init__(self, op, left, right, res):
        self.op = op
        self.left = left
        self.right = right
        self.res = res

    @property
    def address_repr(self):
        op = self.op.value
        left = ""
        if self.left:
            left = f"{self.left.value}({self.left.address})"
        right = ""
        if self.right:
            right = f"{self.right.value}({self.right.address})"
        res = ""
        if self.res:
            if isinstance(self.res, Variable) or isinstance(self.res, Temporal):
                res = f"{self.res.value}({self.res.address})"
            else:
                res = f"{self.res.value}"
        return (
            f"({op:7} {left:>13} "
            f"{right:>14} {res:>14})"
        )

    @property
    def name_repr(self):
        op = self.op.value
        left = ""
        if self.left:
            if self.left.vec_dims:
                dims = f"(d:{str(self.left.vec_dims)})"
            else:
                dims = ""
            left = f"{self.left.value} {dims}"
        right = ""
        if self.right:
            if self.right.vec_dims:
                dims = f"(d:{str(self.right.vec_dims)})"
            else:
                dims = ""
            right = f"{self.right.value} {dims}"
        res = ""
        if self.res:
            if self.res.vec_dims:
                dims = f"(d:{str(self.res.vec_dims)})"
            else:
                dims = ""
            res = f"{self.res.value} {dims}"
        return (
            f"({op:7} {left:>14} "
            f"{right:>15} {res:>22})"
        )

    @property
    def type_repr(self):
        op = self.op.value
        operands = [self.left, self.right, self.res]
        op_reprs = []
        for operand in operands:
            op_repr = ""
            if operand:
                if isinstance(operand, Temporal):
                    op_repr = "T"
                elif isinstance(operand, Constant):
                    op_repr = "C"
                elif isinstance(operand, QuadJump):
                    op_repr = "J"
                elif isinstance(operand, Pointer):
                    op_repr = "*"
                elif isinstance(operand, Function):
                    op_repr = "F"
                elif isinstance(operand, Param):
                    op_repr = "P"
                elif isinstance(operand, Variable):
                    op_repr = "V"
            op_reprs.append(op_repr)
        return (
            f"({op:7} {op_reprs[0]:>13} "
            f"{op_reprs[1]:>14} {op_reprs[2]:>14})"
        )

    def __str__(self):
        op = self.op.value
        left = ""
        if self.left:
            left = f"{self.left.name}({self.left.address})"
        right = ""
        if self.right:
            right = f"{self.right.name}({self.right.address})"
        res = ""
        if self.res:
            if isinstance(self.res, Variable) or isinstance(self.res, Temporal):
                res = f"{self.res.value}({self.res.address})"
            else:
                res = f"{self.res.value}"

        return (
            f"({op:7} {left:>13} "
            f"{right:>14} {res:>14})"
        )

    def __repr__(self):
        return self.__str__()


def print_quads(quads, viz_variant="name"):
    print(f"\n{'='*20} Quadruples {'='*20}")
    for idx, quad in enumerate(quads):
        if viz_variant == "name":
            print(f"{idx:>2}", quad.name_repr)
        elif viz_variant == "address":
            print(f"{idx:>2}", quad.address_repr)
        elif viz_variant == "type":
            print(f"{idx:>2}", quad.type_repr)

class Quads:

    def __init__(self):
        self.operator_stack = []
        self.operand_stack = []
        self.jump_stack = []
        self.type_stack = []
        self.quad_stack = []
        self._temp_register_num = 1
