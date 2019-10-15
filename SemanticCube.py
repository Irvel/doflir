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


def result_type(operand_1, operand_2, operator):
    semantic_cube = {
        (VarTypes.INT, VarTypes.INT, Ops.PLUS): VarTypes.INT,
        (VarTypes.INT, VarTypes.INT, Ops.MINUS): VarTypes.INT,
        (VarTypes.INT, VarTypes.INT, Ops.MULT): VarTypes.INT,
        (VarTypes.INT, VarTypes.INT, Ops.DIV): VarTypes.FLOAT,
        (VarTypes.INT, VarTypes.INT, Ops.INT_DIV): VarTypes.INT,
        (VarTypes.INT, VarTypes.INT, Ops.POW): VarTypes.INT,
        (VarTypes.INT, VarTypes.INT, Ops.AND): VarTypes.BOOL,
        (VarTypes.INT, VarTypes.INT, Ops.OR): VarTypes.BOOL,
        (VarTypes.INT, VarTypes.INT, Ops.GT): VarTypes.BOOL,
        (VarTypes.INT, VarTypes.INT, Ops.GT_EQ): VarTypes.BOOL,
        (VarTypes.INT, VarTypes.INT, Ops.LT): VarTypes.BOOL,
        (VarTypes.INT, VarTypes.INT, Ops.LT_EQ): VarTypes.BOOL,
        (VarTypes.INT, VarTypes.INT, Ops.EQ): VarTypes.BOOL,
        (VarTypes.INT, VarTypes.INT, Ops.NOT_EQ): VarTypes.BOOL,
        (VarTypes.INT, VarTypes.FLOAT, Ops.PLUS): VarTypes.FLOAT,
        (VarTypes.FLOAT, VarTypes.INT, Ops.PLUS): VarTypes.FLOAT,
        (VarTypes.FLOAT, VarTypes.FLOAT, Ops.PLUS): VarTypes.FLOAT,
    }
    target = (operand_1.data_type, operand_2.data_type, operator)
    if target in semantic_cube:
        return semantic_cube[target]
    else:
        return None
