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
            f"({self.op.value:6} {self.left:>11} "
            f"{self.right:>7} {self.res:>7})")

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
