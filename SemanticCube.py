from enum import Enum


class VarTypes(Enum):
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    VECTOR = "vector"
    VOID = "void"


class Ops(Enum):
    POW = "^"
    NEG = "neg"
    POS = "pos"
    NOT_ = "not"
    MAT_MULT = "@"
    DOT = ".."
    MULT = "*"
    DIV = "/"
    INT_DIV = "//"
    PLUS = "+"
    MINUS = "-"
    GT = ">"
    GT_EQ = ">="
    LT = "<"
    LT_EQ = "<="
    EQ = "=="
    NOT_EQ = "!="
    AND_ = "and"
    OR_ = "or"
    ASSIGN = "="
    GOTO = "GOTO"
    GOTOF = "GOTOF"
    RETURN_ = "RETURN"
    GOSUB = "GOSUB"
    PARAM = "PARAM"
    ERA = "ERA"
    ENDPROC = "ENDPROC"
    PRINT = "PRINT"
    PRINTLN = "PRINTLN"
    READT = "READT"
    READA = "READA"
    READC = "READC"
    WRITEF = "WRITEF"
    PLOT = "PLOT"
    ALLOC = "ALLOC"
    VER = "VER"


class VecFilters(Enum):
    F_SUM = "f_sum"
    F_MEAN = "f_mean"
    F_VAR = "f_var"
    F_MIN = "f_min"
    F_MAX = "f_max"
    F_STD = "f_std"
    F_NORMALIZE = "f_normalize"
    F_SQUARE = "f_square"
    F_CUBE = "f_cube"
    F_STRIP = "f_strip"
    F_LOWERCASE = "f_lowercase"
    F_UPPERCASE = "f_uppercase"
    F_SORT = "f_sort"
    F_REVERSE = "f_reverse"


class SemanticCube(object):
    """Hold the semantic considerations table for Doflir."""
    def __init__(self):
        self._setup_op_categories()
        self._setup_cube()
        self._setup_enums_map()
        self._setup_filter_reduce()

    def _setup_filter_reduce(self):
        """Defines semantic considerations for filter's reduction to var."""
        self._filter_reduce = {
            VecFilters.F_SUM: True,
            VecFilters.F_MEAN: True,
            VecFilters.F_MIN: True,
            VecFilters.F_MAX: True,
            VecFilters.F_STD: True,
            VecFilters.F_VAR: True,
            VecFilters.F_NORMALIZE: False,
            VecFilters.F_SQUARE: False,
            VecFilters.F_CUBE: False,
            VecFilters.F_STRIP: False,
            VecFilters.F_LOWERCASE: False,
            VecFilters.F_UPPERCASE: False,
            VecFilters.F_SORT: False,
            VecFilters.F_REVERSE: False,
        }

    def _setup_op_categories(self):
        """Defines groups of operations by their function."""
        self._NUM_OPS = [
            Ops.PLUS, Ops.MINUS, Ops.MULT, Ops.DIV, Ops.INT_DIV, Ops.POW,
            Ops.MAT_MULT, Ops.DOT,
        ]

        self._VEC_OPS = [
            Ops.MAT_MULT, Ops.DOT, Ops.PLUS, Ops.MINUS,
        ]

        self._REL_OPS = [
            Ops.AND_, Ops.OR_, Ops.GT, Ops.GT_EQ, Ops.LT, Ops.LT_EQ, Ops.EQ,
            Ops.NOT_EQ,
        ]

    def _setup_enums_map(self):
        """Provides conversion mechanisms between operation codes and names."""
        self._ops_map = {}
        for op in Ops:
            self._ops_map[op.value] = op

        self._var_types_map = {}
        for var_type in VarTypes:
            self._var_types_map[var_type.value] = var_type

        self._vec_filters_map = {}
        for vec_filter in VecFilters:
            self._vec_filters_map[vec_filter.value] = vec_filter

    def _setup_cube(self):
        """Provides expected output type for a pair of operands and op."""
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

            str_op = (VarTypes.STRING, VarTypes.STRING, op)
            semantic_cube[str_op] = VarTypes.BOOL

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

    def is_reduced(self, vec_filter):
        """Accessor for the vec filtering semantic considerations."""
        return self._filter_reduce[vec_filter]

    def result_type(self, op_1_type, op_2_type, operator):
        """Accessor for the semantic cube."""
        target = (op_1_type, op_2_type, operator)
        if target in self._cube:
            return self._cube[target]
        else:
            return None

    def result_type_str(self, op_1_type, op_2_type, operator):
        """Accessor for the semantic cube but takes a txt instead of enum."""
        op_1_enum = self.type_to_enum(type_str=op_1_type)
        op_2_enum = self.type_to_enum(type_str=op_2_type)
        operator_enum = self.op_to_enum(op_str=operator)
        return self.result_type(
            op_1_type=op_1_enum,
            op_2_type=op_2_enum,
            operator=operator_enum
        )

    def type_to_enum(self, type_str):
        """Shorthand method for conversion of names to enum types."""
        return self._var_types_map[type_str]

    def op_to_enum(self, op_str):
        """Shorthand method for conversion of names to enum ops."""
        return self._ops_map[op_str]

    def filter_to_enum(self, filter_str):
        """Shorthand method for conversion of names to enum filters."""
        return self._vec_filters_map[filter_str]
