from collections import deque
import logging


class Quad:

    def __init__(self, op, left, right, res):
        self.op = op
        self.left = left
        self.right = right
        self.res = res

    def __str__(self):
        return (
            f"({self.op.value:2} {self.left:>4} "
            f"{self.right:>4} {self.res:>6})")


class Quads:

    def __init__(self):
        self.operator_stack = []
        self.operand_stack = []
        self.jump_stack = []
        self.type_stack = []
        self.quad_stack = []
        self._temp_register_num = 1
