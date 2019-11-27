import sys
from termcolor import colored


def bold(txt):
    """Format the text to look bold on the terminal."""
    return colored(str(txt), attrs=["bold"])


def red_bold(txt):
    """Format the text to look red bold on the terminal."""
    return colored(str(txt), "red", attrs=["bold"])


def cyan(txt):
    """Format the text to look cyan on the terminal."""
    return colored(str(txt), "cyan")


class NoTraceBackException(Exception):
    """Disable traceback printing error in Python and use ours instead."""
    def __init__(self, in_filename, line_num, line_txt, err_type, msg):
        err_type = f"{err_type}: "
        err_type = red_bold(err_type)
        self.args = (
            f"{bold(in_filename)}:{bold(line_num)}: "
            f"{err_type}"
            f"{msg}\n{line_txt}",
        )
        sys.exit(self)


class CompError(NoTraceBackException):
    """Base compiler error."""
    def __init__(self, ctx, in_filename, err_type, in_code, msg):
        line_num = max(0, ctx.start.line - 1)
        line_txt = in_code[line_num]
        super().__init__(
            in_filename=in_filename,
            line_num=line_num,
            line_txt=line_txt,
            err_type=err_type,
            msg=msg,
        )


class AlreadyUsedID(CompError):
    """AlreadyUsedID compilation error."""
    def __init__(self, ctx, in_filename, in_code, var_id):
        msg = (f"ID ‘{cyan(var_id)}’ is already in use")
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class UndeclaredVar(CompError):
    """UndeclaredVar compilation error."""
    def __init__(self, ctx, in_filename, in_code, var_id):
        msg = (f"Attempted to use undeclared variable ‘{cyan(var_id)}’")
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class UndeclaredFun(CompError):
    """UndeclaredFun compilation error."""
    def __init__(self, ctx, in_filename, in_code, fun_id):
        msg = (f"Attempted to use undefined function ‘{cyan(fun_id)}’")
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class UninitializedVar(CompError):
    """UninitializedVar compilation error."""
    def __init__(self, ctx, in_filename, in_code, var_id):
        msg = (f"Attempted to use uninitialized variable ‘{cyan(var_id)}’")
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class UndeclaredVec(CompError):
    """UndeclaredVec compilation error."""
    def __init__(self, ctx, in_filename, in_code, vec_id):
        msg = (f"Attempted to use undeclared vector ‘{cyan(vec_id)}’")
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class AlreadyUsedVec(CompError):
    """AlreadyUsedVec compilation error."""
    def __init__(self, ctx, in_filename, in_code, vec_id):
        msg = (f"Vec with ID ‘{cyan(vec_id)}’ already used")
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class FilterReducesBefore(CompError):
    """FilterReducesBefore compilation error."""
    def __init__(self, ctx, in_filename, in_code, vec_filter):
        msg = (
            f"Filter {bold(vec_filter)} reduces the vector to a number "
            "before other filters are applied"
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class VectorNotHomogeneous(CompError):
    """VectorNotHomogeneous compilation error."""
    def __init__(self, ctx, in_filename, in_code):
        msg = ("Vector values must be of homogeneous type")
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class MatrixNotHomogeneous(CompError):
    """MatrixNotHomogeneous compilation error."""
    def __init__(self, ctx, in_filename, in_code):
        msg = ("Matrix values must be of homogeneous type")
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class MatrixColSizeMismatch(CompError):
    """MatrixColSizeMismatch compilation error."""
    def __init__(self, ctx, in_filename, in_code):
        msg = ("All matrix columns must be of the same size")
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class DifferentNumIndexes(CompError):
    """DifferentNumIndexes compilation error."""
    def __init__(self, ctx, in_filename, in_code, vec_id, indexes_provided):
        msg = (
            f"Provided a different number of indexes "
            f"‘{cyan(indexes_provided)}’ "
            f" than the ones declared in ‘{bold(vec_id)}’ "
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class WrongDimType(CompError):
    """WrongDimType compilation error."""
    def __init__(self, ctx, in_filename, in_code, data_type):
        msg = (
            f"Vector dimensions must be int, ‘{cyan(data_type)}’ given instead"
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class WrongIndexType(CompError):
    """WrongIndexType compilation error."""
    def __init__(self, ctx, in_filename, in_code, data_type):
        msg = (
            f"Vector index must be int, ‘{cyan(data_type)}’ given instead"
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class ReturnTypeMismatch(CompError):
    """ReturnTypeMismatch compilation error."""
    def __init__(self, ctx, in_filename, in_code, def_type, ret_type):
        msg = (
            f"Returning a different type than what was defined"
            f"‘{cyan(ret_type)}’ vs expected ‘{cyan(def_type)}’"
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class TypeMismatchVar(CompError):
    """TypeMismatchVar compilation error."""
    def __init__(self, ctx, in_filename, in_code, op_1, op_2):
        msg = (
            f"The type between "
            f"‘{cyan(op_1.value)} {op_1.data_type}’"
            f" and ‘{cyan(op_2.value)} {op_2.data_type}’ must be the same"
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class TypeMismatch(CompError):
    """TypeMismatch compilation error."""
    def __init__(self, ctx, in_filename, in_code, op_1, ex_type):
        msg = (
            f"‘{bold(op_1.value)}’ {cyan(op_1.data_type)}’ "
            f"must be of type ‘{cyan(ex_type)}’"
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class NumDimsMismatch(CompError):
    """NumDimsMismatch compilation error."""
    def __init__(self, ctx, in_filename, in_code, op_1, op_2):
        msg = (
            f"Number of dimensions must be the same between "
            f" ‘{bold(op_1.value)}’ and ‘{bold(op_2.value)}’ "
            f"‘{cyan(op_1.vec_dims)}’ != ‘{cyan(op_2.vec_dims)}’"
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class DimSizeMismatch(CompError):
    """DimSizeMismatch compilation error."""
    def __init__(self, ctx, in_filename, in_code, op_1, op_2):
        msg = (
            f"Dimension size must match between "
            f"‘{bold(op_1.value)}’ and ‘{bold(op_2.value)}’. "
            f"‘{cyan(op_1.vec_dims)}’ vs ‘{cyan(op_2.vec_dims)}’"
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class VecNonVecMismatch(CompError):
    """VecNonVecMismatch compilation error."""
    def __init__(self, ctx, in_filename, in_code, op_1, op_2):
        msg = (
            f"Operands need to be both vector or non vector "
            f"‘{bold(op_1.value)}’ and ‘{bold(op_2.value)}’. "
            f"‘{cyan(op_1.vec_dims)}’ vs ‘{cyan(op_2.vec_dims)}’"
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class MatMultNumDimsMismatch(CompError):
    """MatMultNumDimsMismatch compilation error."""
    def __init__(self, ctx, in_filename, in_code, op_1, op_2):
        msg = (
            f"Number of cols and rows mismatch for matrix multiplication "
            f"{cyan(op_1.vec_dims)} vs {cyan(op_2.vec_dims)}"
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class MatMultNonMatrix(CompError):
    """MatMultNonMatrix compilation error."""
    def __init__(self, ctx, in_filename, in_code, op_1, op_2):
        msg = (
            f"Cannot perform matrix mult on non-matrices "
            f"{cyan(op_1.vec_dims)} vs {cyan(op_2.vec_dims)}"
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class InvalidOperation(CompError):
    """InvalidOperation compilation error."""
    def __init__(self, ctx, in_filename, in_code, op_1, op_2, operator):
        msg = (
            f"Invalid operation: {cyan(op_1.data_type)} "
            f"{operator} {cyan(op_2.data_type)} "
            "is not a valid operation"
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class FilenameNotString(CompError):
    """FilenameNotString compilation error."""
    def __init__(self, ctx, in_filename, in_code, filename):
        msg = (
            f"Filename to read from must be string. ‘{cyan(filename)}’ given "
            "instead"
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )


class ParamArgNumMismatch(CompError):
    """ParamArgNumMismatch compilation error."""
    def __init__(self, ctx, in_filename, in_code, fun_id,
                 num_params, num_args):
        msg = (
            f"Different number of arguments provided for the number of "
            f"parameters in ‘{bold(fun_id)}’. "
            f"‘{cyan(num_args)}’ vs ‘{cyan(num_params)}’"
        )
        super().__init__(
            ctx=ctx,
            in_filename=in_filename,
            err_type="SemanticError",
            in_code=in_code,
            msg=msg,
        )
