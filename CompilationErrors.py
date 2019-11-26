import sys
from termcolor import colored


def bold(txt):
    return colored(txt, attrs=["bold"])


def red_bold(txt):
    return colored(txt, "red", attrs=["bold"])


class NoTraceBackException(Exception):
    def __init__(self, in_filename, line_num, line, err_type, msg):
        err_type = f"{err_type}: "
        err_type = red_bold(err_type)
        self.args = (
            f"{bold(in_filename)}:{bold(line_num)}: "
            f"{err_type}"
            f"{msg}\n{line}",
        )
        sys.exit(self)


class CompError(NoTraceBackException):
    def __init__(self, ctx, in_filename, in_code):
        line_num = ctx.start.line
        line = in_code[line_num]
        super().__init__(
            in_filename,
            line_num,
            line,
            "SemanticError",
            f"There was an Error "
        )
