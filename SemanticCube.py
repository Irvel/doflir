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
    ASSIGN = "="
    GOTO = "GOTO"
    GOTOF = "GOTOF"
    RETURN = "RETURN"
    GOSUB = "GOSUB"
    PARAM = "PARAM"
    ERA = "ERA"
    ENDPROC = "ENDPROC"
    PRINT = "PRINT"


class SemanticCube(object):

    def __init__(self):
        self._setup_op_categories()
        self._setup_cube()
        self._setup_enums_map()

    def _setup_op_categories(self):
        self._NUM_OPS = [
            Ops.PLUS, Ops.MINUS, Ops.MULT, Ops.DIV, Ops.INT_DIV, Ops.POW,
        ]

        self._VEC_OPS = [
            Ops.MAT_MULT, Ops.DOT, Ops.PLUS, Ops.MINUS,
        ]

        self._REL_OPS = [
            Ops.AND, Ops.OR, Ops.GT, Ops.GT_EQ, Ops.LT, Ops.LT_EQ, Ops.EQ,
            Ops.NOT_EQ,
        ]

    def _setup_enums_map(self):
        self._ops_map = {}
        for op in Ops:
            self._ops_map[op.value] = op

        self._var_types_map = {}
        for var_type in VarTypes:
            self._var_types_map[var_type.value] = var_type

    def _setup_cube(self):
        semantic_cube = {}
        # Setup numeric operations results.
        for op in self._NUM_OPS:
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
        for op in self._REL_OPS:
            bool_op = (VarTypes.BOOL, VarTypes.BOOL, op)
            semantic_cube[bool_op] = VarTypes.BOOL

            int_op = (VarTypes.INT, VarTypes.INT, op)
            semantic_cube[int_op] = VarTypes.BOOL

            float_op = (VarTypes.FLOAT, VarTypes.FLOAT, op)
            semantic_cube[float_op] = VarTypes.BOOL

            float_int_op = (VarTypes.FLOAT, VarTypes.INT, op)
            semantic_cube[float_int_op] = VarTypes.BOOL

            int_float_op = (VarTypes.INT, VarTypes.FLOAT, op)
            semantic_cube[int_float_op] = VarTypes.BOOL

        # String concatenation.
        str_op = (VarTypes.STRING, VarTypes.STRING, Ops.PLUS)
        semantic_cube[str_op] = VarTypes.STRING

        # Setup results for vector operations.
        for op in self._VEC_OPS:
            vec_op = (VarTypes.VECTOR, VarTypes.VECTOR, op)
            semantic_cube[vec_op] = VarTypes.VECTOR

        self._cube = semantic_cube

    def result_type(self, op_1_type, op_2_type, operator):
        target = (op_1_type, op_2_type, operator)
        if target in self._cube:
            return self._cube[target]
        else:
            return None

    def result_type_str(self, op_1_type, op_2_type, operator):
        op_1_enum = self.type_to_enum(type_str=op_1_type)
        op_2_enum = self.type_to_enum(type_str=op_2_type)
        operator_enum = self.op_to_enum(op_str=operator)
        return self.result_type(
            op_1_type=op_1_enum,
            op_2_type=op_2_enum,
            operator=operator_enum
        )

    def type_to_enum(self, type_str):
        return self._var_types_map[type_str]

    def op_to_enum(self, op_str):
        return self._ops_map[op_str]
