from collections import deque
import logging


class Quad:

    def __init__(self, op, left, right, res):
        self.op = op
        self.left = left
        self.right = right
        self.res = res

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
            if isinstance(self.res, int) or isinstance(self.res, str):
                res = self.res
            else:
                res = f"{self.res.name}({self.res.address})"
        return (
            f"({op:7} {left:>13} "
            f"{right:>14} {res:>14})"
        )

    def __repr__(self):
        return self.__str__()


class Quads:

    def __init__(self):
        self.operator_stack = []
        self.operand_stack = []
        self.jump_stack = []
        self.type_stack = []
        self.quad_stack = []
        self._temp_register_num = 1
