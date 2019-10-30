from enum import Enum


class VarTypes(Enum):
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    VECTOR = "vector"
    VOID = "void"


class Ops(Enum):
    PLUS = "+"
    MINUS = "-"
    MULT = "*"
    DIV = "/"
    INT_DIV = "//"
    POW = "^"
    MAT_MULT = "@"
    DOT = ".."
    AND = "and"
    OR = "or"
    GT = ">"
    GT_EQ = ">="
    LT = "<"
    LT_EQ = "<="
    EQ = "=="
    NOT_EQ = "!="


NUM_OPS = [
    Ops.PLUS, Ops.MINUS, Ops.MULT, Ops.DIV, Ops.INT_DIV, Ops.POW,
]

VEC_OPS = [
    Ops.MAT_MULT, Ops.DOT, Ops.PLUS, Ops.MINUS,
]

REL_OPS = [
    Ops.AND, Ops.OR, Ops.GT, Ops.GT_EQ, Ops.LT, Ops.LT_EQ, Ops.EQ, Ops.NOT_EQ,
]


def make_cube():
    semantic_cube = {}
    # Setup numeric operations results.
    for op in NUM_OPS:
        int_op = (VarTypes.INT, VarTypes.INT, op)
        semantic_cube[int_op] = VarTypes.INT

        float_op = (VarTypes.FLOAT, VarTypes.FLOAT, op)
        semantic_cube[float_op] = VarTypes.FLOAT

        float_int_op = (VarTypes.FLOAT, VarTypes.INT, op)
        semantic_cube[float_int_op] = VarTypes.FLOAT

        int_float_op = (VarTypes.INT, VarTypes.FLOAT, op)
        semantic_cube[int_float_op] = VarTypes.FLOAT

    # Division always produces float.
    div_op = (VarTypes.INT, VarTypes.INT, Ops.DIV)
    semantic_cube[div_op] = VarTypes.FLOAT

    # Int division always produces int.
    div_op = (VarTypes.FLOAT, VarTypes.INT, Ops.INT_DIV)
    semantic_cube[div_op] = VarTypes.INT
    div_op = (VarTypes.INT, VarTypes.FLOAT, Ops.INT_DIV)
    semantic_cube[div_op] = VarTypes.INT
    div_op = (VarTypes.FLOAT, VarTypes.FLOAT, Ops.INT_DIV)
    semantic_cube[div_op] = VarTypes.INT

    # Setup boolean results for relational operations.
    for op in REL_OPS:
        bool_op = (VarTypes.BOOL, VarTypes.BOOL, op)
        semantic_cube[bool_op] = VarTypes.BOOL

    # String concatenation.
    str_op = (VarTypes.STRING, VarTypes.STRING, Ops.PLUS)
    semantic_cube[str_op] = VarTypes.STRING

    # Setup results for vector operations.
    for op in VEC_OPS:
        vec_op = (VarTypes.VECTOR, VarTypes.VECTOR, op)
        semantic_cube[vec_op] = VarTypes.VECTOR

    return semantic_cube


def result_type(operand_1, operand_2, operator):
    semantic_cube = make_cube()
    target = (operand_1.data_type, operand_2.data_type, operator)
    if target in semantic_cube:
        return semantic_cube[target]
    else:
        return None
