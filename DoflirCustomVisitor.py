from ByteCodeFormat import ByteCodeFormat
from DoflirParser import DoflirParser
from DoflirVisitor import DoflirVisitor
from VariablesTable import VariablesTable
from VariablesTable import FunDir
from VariablesTable import Variable
from VariablesTable import Params
from VariablesTable import QuadJump
from VariablesTable import Constant
from VariablesTable import Param
from VariablesTable import VecIdx
from SemanticCube import Ops
from SemanticCube import SemanticCube
from SemanticCube import VarTypes
from Quads import Quad
from Quads import print_quads
from collections import deque

import CompilationErrors as E
import logging


class DoflirCustomVisitor(DoflirVisitor):
    """A Doflir compiler based on the visitor architecture of antlr4."""
    def __init__(self, in_filename, in_code, debug):
        # The name of the input file that is being compiled.
        self.in_filename = self.clean_filename(in_filename)
        # The raw input text from the Doflir program being compiled.
        self.in_code = in_code.split("\n")
        # Flag that enables or disables the output of compiler debug messages.
        self.debug = debug
        # The table of semantic considerations for resulting data types.
        self.cube = SemanticCube()
        # The global variables table.
        self.global_table = VariablesTable()
        # The function directory.
        self.fun_dir = FunDir()
        # Keep track of the scope in memory with a stack.
        self.scope_stack = deque()
        # The global table is the current scope.
        self.scope_stack.append(self.global_table)
        # Keep track of intertwined operands with an operand stack.
        self.operands_stack = deque()
        # Keep track of intertwined operators with an operator stack.
        self.operators_stack = deque()
        # Keep track of where is it necesary to go back and put a jump.
        self.pending_jumps_stack = deque()
        # Keep track of the pending return value from a function.
        self.return_type_stack = deque()
        # The list of generated quadruples, the IR of Doflir.
        self.quads = []
        self._temp_num = 0

    @property
    def curr_scope(self):
        """Return the topmost scope that the program is aware of."""
        return self.scope_stack[-1]

    @property
    def current_quad_idx(self):
        """Return the idx of the quad that is currently being generated."""
        return len(self.quads) - 1

    def clean_filename(self, filename):
        """Remove directories from a path to just have the file file name."""
        return filename.split("/")[-1]

    def visitProgram(self, ctx: DoflirParser.ProgramContext):
        """Start point for the compilation and end point for the output obj."""
        # Check if there are any statements that are floating without being
        # inside main or a function.
        if ctx.statement:
            for stmt in ctx.statement():
                self.visit(stmt)
        # The goto that points towards main but given that we currently
        # don't know where main is, we leave it pending in the
        # pending_jumps_stack.
        goto_quad = Quad(
            op=Ops.GOTO,
            left=None,
            right=None,
            res=None
        )
        self.quads.append(goto_quad)
        self.pending_jumps_stack.append(self.current_quad_idx)

        # Check for all function definitions before checking main, this
        # makes it so that we can define functions below the block
        # of main code.
        if ctx.fun_def:
            for dfn in ctx.fun_def():
                self.visit(dfn)

        # Parse the main procedure block of code.
        self.visit(ctx.main_def())

        # Output a visual representation of the generated quadruples
        # only if debug is enabled.
        if self.debug:
            self.print_stats()
            print_quads(quads=self.quads, viz_variant="name")
            print_quads(quads=self.quads, viz_variant="address")
            print_quads(quads=self.quads, viz_variant="type")
        return self.generate_obj_code()

    def generate_obj_code(self):
        """Convert the current in-memory IR state into IR bytecode."""
        const_table = {}
        for var in self.global_table.variables:
            if isinstance(var, Constant):
                if var.data_type == VarTypes.STRING:
                    var._value = var._value[1:-1]
                const_table[var.address] = var
        return ByteCodeFormat(
            quads=self.quads,
            const_table=const_table,
            fun_dir=self.fun_dir,
        )

    def print_stats(self):
        """Print the compiler state in a human-friendly way."""
        print(f"\n{'='*10} Global variables {'='*10}\n")
        for var in self.global_table.variables:
            print("→", var)
        print()
        print(f"\n{'='*10} Function directory {'='*10}\n")
        for fun in self.fun_dir.functions:
            if fun.params:
                print(fun.address)
                print(f"- {fun.name:>7}, {fun.ret_type.value:>6}, "
                      f"{str([p.param_id for p in fun.params]):>16}, "
                      f"{fun.address:>9}")
            else:
                print(f"- {fun.name:>7}, {fun.ret_type.value:>6}, "
                      f"{'[]':>16}, {fun.address:>9}")
        print("\n")

    def visitVec_indexing(self, ctx: DoflirParser.Vec_indexingContext):
        """Retrieve a value from a specified location inside a vector."""
        vec_id = ctx.ID().getText()
        vec = (
            self.curr_scope.search(vec_id) or self.global_table.search(vec_id)
        )
        if not vec:
            raise E.UndeclaredVec(ctx, self.in_filename, self.in_code,
                                  vec_id)
        indexes = ctx.expr_list().expr()
        if len(vec.vec_dims) != len(indexes):
            raise E.DifferentNumIndexes(
                ctx, self.in_filename, self.in_code, vec_id, indexes
            )
        vec_idx = []
        for idx_num, idx_expr in enumerate(indexes):
            self.visit(idx_expr)
            idx_res = self.operands_stack.pop()
            if idx_res.data_type != VarTypes.INT:
                raise E.WrongIndexType(
                    ctx, self.in_filename, self.in_code, idx_res.data_type
                )
            vec_idx.append(idx_res)
            # Indexes are expr so we cannot know their value at compile time.
            # We have to settle for a bounds check at runtime with VER.
            ver_quad = Quad(
                op=Ops.VER,
                left=idx_res,
                right=None,
                res=vec.vec_dims[idx_num]
            )
            self.quads.append(ver_quad)
        # Put the resolved expr into the operands stack as it hasn't
        # been consumed yet.
        self.operands_stack.append(
            VecIdx(vec_id=vec_id, idx=vec_idx, address=vec.address,
                   data_type=vec.data_type)
        )

    def visitVec_filtering(self, ctx: DoflirParser.Vec_filteringContext):
        """Parse the expression of applying a filter into a vector."""
        vec_id = ctx.ID().getText()
        vec = (
            self.curr_scope.search(vec_id) or self.global_table.search(vec_id)
        )
        if not vec:
            raise E.UndeclaredVec(ctx, self.in_filename, self.in_code,
                                  vec_id)
        # Some filters collapse the vector into a single value. We know which
        # ones do this at compile time, so we can ensure that a collapsed
        # single value won't be assigned onto a vector variable.
        is_reduced = False
        vec_filters = []
        for idx, vec_filter_ctx in enumerate(ctx.filter_list().FILTER()):
            vec_filter = self.cube.filter_to_enum(vec_filter_ctx.getText())
            if self.cube.is_reduced(vec_filter=vec_filter):
                is_reduced = True
                if idx < len(ctx.filter_list().FILTER()) - 1:
                    raise E.FilterReducesBefore(
                        ctx, self.in_filename, self.in_code, vec_filter.value
                    )
            vec_filters.append(vec_filter)

        # The filtering operates on a temporal copy of the vector.
        tmp_vec = self.allocate_temp_vec(
            data_type=vec.data_type,
            vec_dims=vec.vec_dims
        )
        self.quads.append(
            Quad(
                op=Ops.ASSIGN,
                left=vec,
                right=None,
                res=tmp_vec
            )
        )
        # Don't apply the last filter because it might reduce the vector into
        # a single value. If it does so, we need to set the result into a
        # temporal value instead of a temporal vector.
        for vec_filter in vec_filters[:-1]:
            self.quads.append(
                Quad(
                    op=vec_filter,
                    left=tmp_vec,
                    right=None,
                    res=tmp_vec
                )
            )
        result_var = None
        if is_reduced:
            result_var = self.curr_scope.make_temp(temp_type=vec.data_type)
        else:
            result_var = tmp_vec
        self.operands_stack.append(result_var)
        final_quad = Quad(
            op=vec_filters[-1],
            left=tmp_vec,
            right=None,
            res=result_var,
        )
        self.quads.append(final_quad)

        return self.visitChildren(ctx)

    def allocate_temp_vec(self, data_type, vec_dims):
        """Indicate to the VM that we want a vector of size vec_dims."""
        tmp_vec = self.curr_scope.make_temp(
            temp_type=data_type,
            vec_dims=vec_dims,
        )
        allocate_quad_tmp_vec = Quad(
            op=Ops.ALLOC,
            left=None,
            right=None,
            res=tmp_vec
        )
        self.quads.append(allocate_quad_tmp_vec)
        return tmp_vec

    def visitVecInitExpr(self, ctx: DoflirParser.VecInitExprContext):
        """Parse a vector constant into an allocated vector in memory."""
        # Determine size of the given vector.
        vec_init_list = []
        for tok in ctx.vec_init_list().tok_list().token():
            self.visit(tok)
            vec_init_list.append(self.operands_stack.pop())
        dim_size = self.curr_scope.make_const(
            value=len(vec_init_list),
            const_type=VarTypes.INT,
        )
        # Allocate a temporal vector with the size of the init vector.
        tmp_vec = self.allocate_temp_vec(
            data_type=vec_init_list[0].data_type,
            vec_dims=[dim_size]
        )
        # Assign the read init values into our temp_vector one by one.
        for vec_idx, init_val in enumerate(vec_init_list):
            vec_idx_const = self.curr_scope.make_const(
                value=vec_idx,
                const_type=VarTypes.INT,
            )
            # We need to index the temporal vector and so we need a
            # VecIdx for doing so.
            dst_idx = VecIdx(vec_id=tmp_vec.name, idx=[vec_idx_const],
                             address=tmp_vec.address,
                             data_type=tmp_vec.data_type)
            if init_val.data_type != dst_idx.data_type:
                raise E.VectorNotHomogeneous(
                    ctx, self.in_filename, self.in_code
                )
            assign_quad = Quad(
                op=Ops.ASSIGN,
                left=init_val,
                right=None,
                res=dst_idx
            )
            self.quads.append(assign_quad)

        self.operands_stack.append(tmp_vec)

    def visitMatInitExpr(self, ctx: DoflirParser.MatInitExprContext):
        """Parse a matrix constant into an allocated matrix in memory."""
        col_size_num = None
        mat_init_list = []
        # Figure out the dimensions of the matrix.
        for vec_list in ctx.mat_init_list().vec_init_list():
            vec_init_list = []
            for tok in vec_list.tok_list().token():
                self.visit(tok)
                vec_init_list.append(self.operands_stack.pop())
            if col_size_num is None:
                col_size_num = len(vec_init_list)
            # Doflir does not support having different sizes of columns
            # within the same matrix. Throw error.
            elif col_size_num != len(vec_init_list):
                raise E.MatrixColSizeMismatch(
                    ctx, self.in_filename, self.in_code
                )
            mat_init_list.append(vec_init_list)
        row_size = self.curr_scope.make_const(
            value=len(mat_init_list),
            const_type=VarTypes.INT,
        )
        col_size = self.curr_scope.make_const(
            value=col_size_num,
            const_type=VarTypes.INT,
        )
        # Allocate a temporal matrix with the size of the init matrix.
        tmp_mat = self.allocate_temp_vec(
            data_type=mat_init_list[0][0].data_type,
            vec_dims=[row_size, col_size]
        )

        # Assign the read init values into our temp_matrix one by one.
        for row_idx, row in enumerate(mat_init_list):
            row_idx_const = self.curr_scope.make_const(
                value=row_idx,
                const_type=VarTypes.INT,
            )
            for col_idx, init_val in enumerate(row):
                col_idx_const = self.curr_scope.make_const(
                    value=col_idx,
                    const_type=VarTypes.INT,
                )
                dst_idx = VecIdx(
                    vec_id=tmp_mat.name,
                    idx=[row_idx_const, col_idx_const],
                    address=tmp_mat.address,
                    data_type=tmp_mat.data_type
                )
                if init_val.data_type != dst_idx.data_type:
                    raise E.MatrixNotHomogeneous(
                        ctx, self.in_filename, self.in_code
                    )
                assign_quad = Quad(
                    op=Ops.ASSIGN,
                    left=init_val,
                    right=None,
                    res=dst_idx
                )
                self.quads.append(assign_quad)
        self.operands_stack.append(tmp_mat)

    def visitTokIdExpr(self, ctx: DoflirParser.TokIdExprContext):
        """Parse the expression that a single token ID represents."""
        var_id = ctx.ID().getText()
        var = (
            self.curr_scope.search(var_id) or self.global_table.search(var_id)
        )
        if not var:
            raise E.UndeclaredVar(ctx, self.in_filename, self.in_code,
                                  var_id)
        self.operands_stack.append(var)

    def visitTokIntExpr(self, ctx: DoflirParser.TokIntExprContext):
        """Parse an int literal expression into the operands stack."""
        self.operands_stack.append(
            self.global_table.declare_or_search(
                value=int(ctx.getText()),
                const_type=VarTypes.INT,
                is_const=True,
            )
        )

    def visitTokFloatExpr(self, ctx: DoflirParser.TokFloatExprContext):
        """Parse a float literal expression into the operands stack."""
        self.operands_stack.append(
            self.global_table.declare_or_search(
                value=float(ctx.getText()),
                const_type=VarTypes.FLOAT,
                is_const=True,
            )
        )

    def visitTokStrExpr(self, ctx: DoflirParser.TokStrExprContext):
        """Parse a string literal expression into the operands stack."""
        self.operands_stack.append(
            self.global_table.declare_or_search(
                value=str(ctx.getText()),
                const_type=VarTypes.STRING,
                is_const=True,
            )
        )

    def visitTokBoolExpr(self, ctx: DoflirParser.TokBoolExprContext):
        """Parse a bool literal expression into the operands stack."""
        self.operands_stack.append(
            self.global_table.declare_or_search(
                value=bool(ctx.getText().capitalize()),
                const_type=VarTypes.BOOL,
                is_const=True,
            )
        )

    def visitDeclaration_stmt(self, ctx: DoflirParser.DeclarationContext):
        """Declare a variable into the symbols table."""
        var_id = ctx.declaration().ID().getText()
        var_type = ctx.declaration().TYPE_NAME().getText().upper()
        if self.debug:
            logging.debug(f"Declaring variable ({var_id}, {var_type})")
        # We allow local variables to override global variables. If
        # two variables have the same name, one local and one global;
        # the local variable will take precedence.
        if self.curr_scope.exists(var_id):
            raise E.AlreadyUsedID(ctx, self.in_filename, self.in_code, var_id)
        is_glob = False
        if len(self.scope_stack) == 1:
            is_glob = True
        self.curr_scope.declare_var(
            name=var_id, var_type=VarTypes[var_type], is_glob=is_glob
        )
        return self.visitChildren(ctx)

    def visitVec_declaration_stmt(
            self, ctx: DoflirParser.Vec_declaration_stmtContext):
        """Declare a vector into the symbols table."""
        vec_id = ctx.vec_declaration().declaration().ID().getText()
        vec_type = ctx.vec_declaration().declaration().TYPE_NAME().getText().upper()
        if self.curr_scope.exists(vec_id):
            raise E.AlreadyUsedVec(ctx, self.in_filename, self.in_code, vec_id)
        is_glob = False
        if len(self.scope_stack) == 1:
            is_glob = True

        vec_dims = []
        for dim in ctx.vec_declaration().vec_list().tok_list().token():
            self.visit(dim)
            dim_expr = self.operands_stack.pop()
            if dim_expr.data_type != VarTypes.INT:
                raise E.WrongDimType(
                    ctx, self.in_filename, self.in_code, dim_expr.data_type
                )
            # The dimensions provided could be an uninitialized variable.
            if not dim_expr.is_initialized:
                raise E.UninitializedVar(
                    ctx, self.in_filename, self.in_code, dim_expr.value
                )
            vec_dims.append(dim_expr)
        if self.debug:
            logging.debug(f"Declaring vector ({vec_id}, {vec_type})")
        vec = self.curr_scope.declare_vector(
            name=vec_id, vec_type=VarTypes[vec_type], vec_dims=vec_dims,
            is_glob=is_glob
        )
        allocate_quad = Quad(
            op=Ops.ALLOC,
            left=None,
            right=None,
            res=vec
        )
        self.quads.append(allocate_quad)

    def visitAssignment(self, ctx: DoflirParser.AssignmentContext):
        """Parse an assignment operation between two operands statement."""
        # We need to figure out if we're assigning to a variable or to
        # a point of a vector indicated by a vector index.
        if ctx.ID():
            # We need to do this again cause ID here is not an expr
            identifier = ctx.ID().getText()
            variable = (
                self.curr_scope.search(identifier) or
                self.global_table.search(identifier)
            )
            if not variable:
                raise E.UndeclaredVar(ctx, self.in_filename, self.in_code,
                                      identifier)
            self.operands_stack.append(variable)

        elif ctx.vec_indexing():
            identifier = ctx.vec_indexing().ID().getText()
            vec = (
                self.curr_scope.search(identifier) or
                self.global_table.search(identifier)
            )
            if not vec:
                raise E.UndeclaredVec(ctx, self.in_filename, self.in_code,
                                      identifier)
            self.visit(ctx.vec_indexing())

        self.operators_stack.append(Ops.ASSIGN)
        self.visit(ctx.expr())
        if self.operators_stack and self.operators_stack[-1] == Ops.ASSIGN:
            op_1 = self.operands_stack.pop()
            op_2 = self.operands_stack.pop()
            if op_1.data_type != op_2.data_type:
                raise E.TypeMismatchVar(ctx, self.in_filename, self.in_code,
                                        op_1, op_2)
            # If one vector is being assigned to another vector, make sure they
            # have the same number of dimensions.
            if op_1.vec_dims or op_2.vec_dims:
                if not self.check_size_dims(op_1.vec_dims, op_2.vec_dims):
                    raise E.NumDimsMismatch(ctx, self.in_filename,
                                            self.in_code, op_1, op_2)
            op_2.is_initialized = True
            assign_quad = Quad(
                op=Ops.ASSIGN,
                left=op_1,
                right=None,
                res=op_2
            )
            self.quads.append(assign_quad)

    def check_mat_mult_dims(self, dims_1, dims_2):
        """Return if dims_1 and dims_2 can take part in a matrix mult."""
        # Two matrices can be multiplied only when the number of columns in
        # the first equals the number of rows in the second
        col_1 = dims_1[1].value
        row_2 = dims_2[0].value
        return col_1 == row_2

    def check_size_dims(self, dims_1, dims_2):
        """Return whether dims_1 and dims_2 are of the same length."""
        if dims_1 and dims_2:
            return len(dims_1) == len(dims_2)
        else:
            return False

    def check_dims_match(self, dims_1, dims_2):
        """Return whether dims_1 and dims_2 are of the same internal size."""
        if self.check_size_dims(dims_1, dims_2):
            for dim_1, dim_2 in zip(dims_1, dims_2):
                if dim_1.value != dim_2.value:
                    return False
        else:
            return False
        return True

    def generate_bin_quad(self, ctx):
        """Generic method for generating binary op quadruples."""
        operator = self.operators_stack.pop()
        op_2 = self.operands_stack.pop()
        op_1 = self.operands_stack.pop()
        result_type = self.cube.result_type(
            op_1_type=op_1.data_type,
            op_2_type=op_2.data_type,
            operator=operator
        )
        if not result_type:
            raise E.InvalidOperation(ctx, self.in_filename, self.in_code, op_1,
                                     op_2, operator)
        if not op_1.is_initialized:
            raise E.UninitializedVar(
                ctx, self.in_filename, self.in_code, op_1.value
            )
        if not op_2.is_initialized:
            raise E.UninitializedVar(
                ctx, self.in_filename, self.in_code, op_2.value
            )

        both_are_vec = op_1.vec_dims and op_2.vec_dims
        if both_are_vec or not both_are_vec:
            if both_are_vec:
                # Matrix multiplications need special treatment because they
                # can result in a matrix with different dimensions that the
                # original matrices.
                if operator == Ops.MAT_MULT:
                    if len(op_1.vec_dims) != 2 or len(op_2.vec_dims) != 2:
                        raise E.MatMultNonMatrix(
                            ctx, self.in_filename, self.in_code, op_1, op_2
                        )
                    if not self.check_mat_mult_dims(op_1.vec_dims,
                                                    op_2.vec_dims):
                        raise E.MatMultNumDimsMismatch(
                            ctx, self.in_filename, self.in_code, op_1, op_2
                        )
                    # Resulting dim of mat mult (n x m) @ (f x v) is (n x v)
                    result_tmp = self.curr_scope.make_temp(
                        temp_type=result_type,
                        vec_dims=[op_1.vec_dims[0], op_2.vec_dims[1]],
                    )
                else:
                    if not self.check_size_dims(op_2.vec_dims, op_2.vec_dims):
                        raise E.NumDimsMismatch(
                            ctx, self.in_filename, self.in_code, op_1, op_2
                        )
                    if not self.check_dims_match(op_2.vec_dims, op_2.vec_dims):
                        raise E.DimSizeMismatch(
                            ctx, self.in_filename, self.in_code, op_1, op_2
                        )
                    result_tmp = self.curr_scope.make_temp(
                        temp_type=result_type,
                        vec_dims=op_1.vec_dims
                    )
            else:
                result_tmp = self.curr_scope.make_temp(temp_type=result_type)
            new_quad = Quad(
                op=operator,
                left=op_1,
                right=op_2,
                res=result_tmp
            )
            self.quads.append(new_quad)
            self.operands_stack.append(result_tmp)
        else:
            # Do not allow using a matrix with a variable and viceversa.
            raise E.VecNonVecMismatch(
                ctx, self.in_filename, self.in_code, op_1, op_2
            )

    def try_op(self, op, ctx):
        """Check that this op is at the top of the stack to consume it."""
        if self.operators_stack and self.operators_stack[-1] == op:
            self.generate_bin_quad(ctx)

    def visitUnOpExpr(self, ctx, operator):
        """Generic method for parsing unary op expressions."""
        self.visit(ctx.expr())
        operand = self.operands_stack.pop()
        if not operand.is_initialized:
            raise E.UninitializedVar(
                ctx, self.in_filename, self.in_code, operand.value
            )

        result_tmp = self.curr_scope.make_temp(temp_type=operand.data_type)
        new_quad = Quad(
            op=operator,
            left=operand,
            right=None,
            res=result_tmp
        )
        self.quads.append(new_quad)
        self.operands_stack.append(result_tmp)

    def visitNegExpr(self, ctx: DoflirParser.NegExprContext):
        """Unary numeric negation operation. -(1) turns into -1."""
        self.visitUnOpExpr(ctx=ctx, operator=Ops.NEG)

    def visitPosExpr(self, ctx: DoflirParser.PosExprContext):
        """Unary numeric positive operation. +(1) turns into +1."""
        self.visitUnOpExpr(ctx=ctx, operator=Ops.POS)

    def visitNotExpr(self, ctx: DoflirParser.NotExprContext):
        """Boolean unary negation operation. true turns into false."""
        self.visitUnOpExpr(ctx=ctx, operator=Ops.NOT_)

    def visitBinOpExpr(self, ctx, operator):
        """Parse a binary operation into the stack."""
        self.visit(ctx.expr(0))
        self.try_op(op=operator, ctx=ctx)
        self.operators_stack.append(operator)
        self.visit(ctx.expr(1))
        self.try_op(op=operator, ctx=ctx)

    def visitMatMultExpr(self, ctx: DoflirParser.MatMultExprContext):
        """Parse a matrix multiplication between two matrices expression."""
        self.visitBinOpExpr(ctx=ctx, operator=Ops.MAT_MULT)

    def visitDotExpr(self, ctx: DoflirParser.DotExprContext):
        """Parse a dot product between two matrices expression."""
        self.visitBinOpExpr(ctx=ctx, operator=Ops.DOT)

    def visitMultExpr(self, ctx: DoflirParser.MultExprContext):
        """Parse a multiplication operation between two operands expression."""
        self.visitBinOpExpr(ctx=ctx, operator=Ops.MULT)

    def visitDivExpr(self, ctx: DoflirParser.DivExprContext):
        """Float division operation between two operands."""
        self.visitBinOpExpr(ctx=ctx, operator=Ops.DIV)

    def visitIntDivExpr(self, ctx: DoflirParser.IntDivExprContext):
        """Integer division operation between two operands."""
        self.visitBinOpExpr(ctx=ctx, operator=Ops.INT_DIV)

    def visitPowExpr(self, ctx: DoflirParser.PowExprContext):
        """Power operation between two operands."""
        self.visitBinOpExpr(ctx=ctx, operator=Ops.POW)

    def visitAddExpr(self, ctx: DoflirParser.AddExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.PLUS)

    def visitSubExpr(self, ctx: DoflirParser.SubExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.MINUS)

    def visitGtExpr(self, ctx: DoflirParser.GtExprContext):
        """Parse a logical greater than relop between two operands."""
        self.visitBinOpExpr(ctx=ctx, operator=Ops.GT)

    def visitGtEqExpr(self, ctx: DoflirParser.GtEqExprContext):
        """Parse a logical greater than or equal relop between two operands."""
        self.visitBinOpExpr(ctx=ctx, operator=Ops.GT_EQ)

    def visitLtExpr(self, ctx: DoflirParser.LtExprContext):
        """Parse a logical less than relop between two operands."""
        self.visitBinOpExpr(ctx=ctx, operator=Ops.LT)

    def visitLtEqExpr(self, ctx: DoflirParser.LtEqExprContext):
        """Parse a logical less than or equal relop between two operands."""
        self.visitBinOpExpr(ctx=ctx, operator=Ops.LT_EQ)

    def visitEqExpr(self, ctx: DoflirParser.EqExprContext):
        """Parse a logical equal relop between two operands."""
        self.visitBinOpExpr(ctx=ctx, operator=Ops.EQ)

    def visitNotEqExpr(self, ctx: DoflirParser.NotEqExprContext):
        """Parse a logical not equal relop between two operands."""
        self.visitBinOpExpr(ctx=ctx, operator=Ops.NOT_EQ)

    def visitAndExpr(self, ctx: DoflirParser.AndExprContext):
        """Parse a logical and relop between two operands."""
        self.visitBinOpExpr(ctx=ctx, operator=Ops.AND_)

    def visitOrExpr(self, ctx: DoflirParser.OrExprContext):
        """Parse a logical or relop between two operands."""
        self.visitBinOpExpr(ctx=ctx, operator=Ops.OR_)

    def visitCondition(self, ctx):
        """Parse the condition portion of a conditional statement."""
        self.visit(ctx.expr())
        expr_res = self.operands_stack.pop()
        # We need a boolean for our GOTOF.
        if expr_res.data_type is not VarTypes.BOOL:
            raise E.TypeMismatch(
                ctx, self.in_filename, self.in_code, expr_res, VarTypes.BOOL
            )
        gotof_quad = Quad(
            op=Ops.GOTOF,
            left=expr_res,
            right=None,
            res=None
        )
        self.quads.append(gotof_quad)
        self.pending_jumps_stack.append(self.current_quad_idx)

    def visitIfStmt(self, ctx: DoflirParser.IfStmtContext):
        """Parse a simple if conditional statement."""
        self.visitCondition(ctx)  # Parse condition and generate GOTOF.
        self.visit(ctx.proc_body())
        pending_gotof = self.pending_jumps_stack.pop()
        self.quads[pending_gotof].res = QuadJump(self.current_quad_idx + 1)

    def visitIfElseStmt(self, ctx: DoflirParser.IfElseStmtContext):
        """Parse an if-else conditional statement."""
        self.visitCondition(ctx)  # Parse condition and generate GOTOF.
        self.visit(ctx.proc_body(0))
        pending_goto = self.pending_jumps_stack.pop()
        self.quads[pending_goto].res = QuadJump(self.current_quad_idx + 2)
        # Avoid going into the else statement given that condition was true.
        goto_quad = Quad(
            op=Ops.GOTO,
            left=None,
            right=None,
            res=None
        )
        self.quads.append(goto_quad)
        self.pending_jumps_stack.append(self.current_quad_idx)
        self.visit(ctx.proc_body(1))
        pending_goto = self.pending_jumps_stack.pop()
        self.quads[pending_goto].res = QuadJump(self.current_quad_idx + 1)

    def visitWhileStmt(self, ctx: DoflirParser.WhileStmtContext):
        """Parse a while loop statement."""
        cond_quad_idx = self.current_quad_idx + 1
        self.visitCondition(ctx)  # Parse condition and generate GOTOF.
        self.visit(ctx.proc_body())
        pending_gotof = self.pending_jumps_stack.pop()
        self.quads[pending_gotof].res = QuadJump(self.current_quad_idx + 2)
        goto_quad = Quad(
            op=Ops.GOTO,
            left=None,
            right=None,
            res=QuadJump(cond_quad_idx)
        )
        self.quads.append(goto_quad)

    def visitFun_def(self, ctx: DoflirParser.Fun_defContext):
        """Parse a function definition statement."""
        fun_id = ctx.ID().getText()
        return_type = self.cube.type_to_enum(
            type_str=ctx.TYPE_NAME().getText()
        )
        # Check that the function does not collide with the name of a
        # variable or another function.
        if (self.global_table.exists(var_name=fun_id) or
                self.fun_dir.exists(fun_name=fun_id)):
            raise E.AlreadyUsedID(
                ctx, self.in_filename, self.in_code, fun_id
            )
        # Create a new scope for the statements inside the function body.
        self.scope_stack.append(VariablesTable())
        params = None
        if ctx.parameters():
            params = []
            # Parse all of the variable parameters from the function.
            for param in ctx.parameters().declaration():
                param_id = param.ID().getText()
                param_type_str = param.TYPE_NAME().getText()
                if self.global_table.exists(param_id):
                    raise E.AlreadyUsedID(
                        ctx, self.in_filename, self.in_code, param_id
                    )
                if self.fun_dir.exists(param_id) or fun_id == param_id:
                    raise E.AlreadyUsedID(
                        ctx, self.in_filename, self.in_code, param_id
                    )
                param_type = self.cube.type_to_enum(type_str=param_type_str)
                param_address = self.curr_scope.new_address(
                    v_type=param_type,
                    is_glob=False,
                )
                var = Variable(
                    name=param_id,
                    data_type=param_type,
                    address=param_address,
                    )
                var.is_initialized = True
                self.curr_scope._add_var(variable=var)
                params.append(
                    Params(
                        param_id=param_id,
                        param_type=param_type,
                        address=param_address
                    )
                )
            # Parse all of the vector parameters from the function.
            for param in ctx.parameters().vec_declaration():
                param_id = param.declaration().ID().getText()
                param_type_str = param.declaration().TYPE_NAME().getText()
                if self.global_table.exists(param_id):
                    raise E.AlreadyUsedID(
                        ctx, self.in_filename, self.in_code, param_id
                    )
                if self.fun_dir.exists(param_id) or fun_id == param_id:
                    raise E.AlreadyUsedID(
                        ctx, self.in_filename, self.in_code, param_id
                    )
                param_type = self.cube.type_to_enum(type_str=param_type_str)
                param_address = self.curr_scope.new_address(
                    v_type=param_type,
                    is_glob=False,
                )

                vec_dims = []
                for dim in param.vec_list().tok_list().token():
                    self.visit(dim)
                    dim_expr = self.operands_stack.pop()
                    if dim_expr.data_type != VarTypes.INT:
                        raise E.WrongDimType(
                            ctx, self.in_filename, self.in_code,
                            dim_expr.data_type
                        )
                    vec_dims.append(dim_expr)
                if self.debug:
                    logging.debug(f"Declaring vector ({param_id}, {param_type})")
                vec = self.curr_scope.declare_vector(
                    name=param_id, vec_type=param_type, vec_dims=vec_dims,
                    is_glob=False
                )
                params.append(
                    Params(
                        param_id=param_id,
                        param_type=param_type,
                        address=vec.address,
                    )
                )
                allocate_quad = Quad(
                    op=Ops.ALLOC,
                    left=None,
                    right=None,
                    res=vec
                )
                self.quads.append(allocate_quad)
        if self.debug:
            logging.debug(f"Defining function ({fun_id}, {return_type})")
        self.fun_dir.define_fun(
            name=fun_id,
            ret_type=return_type,
            params=params,
            address=self.global_table.new_address(
                v_type=return_type,
                is_glob=True,
            ),
            quad_idx=self.current_quad_idx + 1,
        )
        self.return_type_stack.append(return_type)
        self.visit(ctx.proc_body())
        ret_quad = Quad(Ops.ENDPROC, None, None, None)
        self.quads.append(ret_quad)
        self.return_type_stack.pop()
        self.scope_stack.pop()

    def visitFlow_call(self, ctx: DoflirParser.Flow_callContext):
        """Parse a return statement."""
        ret_val = VarTypes.VOID
        return_type = self.return_type_stack[-1]
        # If the return tok was used on its own, then there's no return value.
        if ctx.expr():
            self.visit(ctx.expr())
            ret_val = self.operands_stack.pop()
            if return_type != ret_val.data_type:
                raise E.ReturnTypeMismatch(
                    ctx,
                    self.in_filename,
                    self.in_code,
                    return_type,
                    ret_val.data_type
                )
        ret_quad = Quad(Ops.RETURN_, None, None, ret_val)
        self.quads.append(ret_quad)

    def visitFun_call(self, ctx: DoflirParser.Fun_callContext):
        """Parse a function call statement."""
        fun_id = ctx.ID().getText()
        target_fun = self.fun_dir.search(fun_name=fun_id)
        if not target_fun:
            raise E.UndeclaredFun(
                ctx, self.in_filename, self.in_code, fun_id
            )
        era_quad = Quad(
            op=Ops.ERA,
            left=target_fun,
            right=None,
            res=None
        )
        self.quads.append(era_quad)
        # Check if the function is being called with arguments.
        if ctx.expr_list():
            num_args = len(ctx.expr_list().expr())
            # Verify that the number of given arguments is the same as the
            # number of parameters specified in the function definition.
            if not target_fun.num_params == num_args:
                raise E.ParamArgNumMismatch(
                    ctx=ctx,
                    in_filename=self.in_filename,
                    in_code=self.in_code,
                    fun_id=fun_id,
                    num_params=target_fun.num_params,
                    num_args=num_args
                )
            par_num = 1
            for expr, param in zip(ctx.expr_list().expr(), target_fun.params):
                self.visit(expr)
                expr_res = self.operands_stack.pop()
                if not expr_res.data_type == param.param_type:
                    raise E.TypeMismatch(
                        ctx, self.in_filename, self.in_code,
                        expr_res.data_type, param.param_type
                    )
                param_quad = Quad(
                    op=Ops.PARAM,
                    left=expr_res,
                    right=None,
                    res=Param(par_num),
                )
                self.quads.append(param_quad)
                par_num += 1
        # Tell the VM to switch the IP to the actual function.
        gosub_quad = Quad(
            op=Ops.GOSUB,
            left=target_fun,
            right=None,
            res=None
        )
        self.quads.append(gosub_quad)

        if target_fun.ret_type != VarTypes.VOID:
            # Make a copy of the return value of the function into a temporal
            # to not loose it in subsequent function calls.
            ret_tmp = self.curr_scope.make_temp(temp_type=target_fun.ret_type)
            assign_ret_quad = Quad(
                op=Ops.ASSIGN,
                left=target_fun,
                right=None,
                res=ret_tmp
            )
            self.quads.append(assign_ret_quad)
            self.operands_stack.append(ret_tmp)

    def visitMain_def(self, ctx: DoflirParser.Main_defContext):
        """Parse the main procedure body."""
        pending_goto = self.pending_jumps_stack.pop()
        # Set the first line of the quadruples to jump to this point.
        self.quads[pending_goto].res = QuadJump(self.current_quad_idx + 1)
        self.visitChildren(ctx)

    def visitPrint_stmt(self, ctx: DoflirParser.Print_stmtContext):
        """Parse a print to console statement."""
        for expr in ctx.expr_list().expr():
            self.visit(expr)
            print_expr = self.operands_stack.pop()
            if not print_expr.is_initialized:
                raise E.UninitializedVar(
                    ctx, self.in_filename, self.in_code, print_expr.value
                )
            print_quad = Quad(
                op=Ops.PRINT,
                left=None,
                right=None,
                res=print_expr
            )
            self.quads.append(print_quad)

    def visitPrintln_stmt(self, ctx: DoflirParser.Println_stmtContext):
        """Parse a println to console statement."""
        for expr in ctx.expr_list().expr():
            self.visit(expr)
            print_expr = self.operands_stack.pop()
            if not print_expr.is_initialized:
                raise E.UninitializedVar(
                    ctx, self.in_filename, self.in_code, print_expr.value
                )
            print_quad = Quad(
                op=Ops.PRINTLN,
                left=None,
                right=None,
                res=print_expr
            )
            self.quads.append(print_quad)

    def visitPlot_stmt(self, ctx: DoflirParser.Plot_stmtContext):
        """Parse a plot to UI statement."""
        self.visit(ctx.expr())
        plot_expr = self.operands_stack.pop()
        if not plot_expr.is_initialized:
            raise E.UninitializedVar(
                ctx, self.in_filename, self.in_code, plot_expr.value
            )
        self.quads.append(
            Quad(
                op=Ops.PLOT,
                left=None,
                right=None,
                res=plot_expr
            )
        )

    def visitWrite_file_stmt(self, ctx: DoflirParser.Write_file_stmtContext):
        """Parse a write to file statement."""
        self.visit(ctx.expr(0))
        # Make sure there's actually something to write there.
        write_expr = self.operands_stack.pop()
        if not write_expr.is_initialized:
            raise E.UninitializedVar(
                ctx, self.in_filename, self.in_code, write_expr.value
            )
        self.visit(ctx.expr(1))
        # Check thet the filename points to actually something.
        filename_expr = self.operands_stack.pop()
        if not filename_expr.is_initialized:
            raise E.UninitializedVar(
                ctx, self.in_filename, self.in_code, filename_expr.value
            )
        if filename_expr.data_type != VarTypes.STRING:
            raise E.FilenameNotString(
                ctx, self.in_filename, self.in_code, filename_expr.data_type
            )
        self.quads.append(
            Quad(
                op=Ops.WRITEF,
                left=write_expr,
                right=None,
                res=filename_expr
            )
        )

    def visitRead_table(self, ctx: DoflirParser.Read_tableContext):
        """Parse a read table from file statement."""
        self.visit(ctx.expr())
        filename_expr = self.operands_stack.pop()
        self.visit(ctx.token(0))
        rows_expr = self.operands_stack.pop()
        self.visit(ctx.token(1))
        cols_expr = self.operands_stack.pop()
        table_type = VarTypes[ctx.TYPE_NAME().getText().upper()]
        if rows_expr.data_type != VarTypes.INT:
            raise E.WrongDimType(
                ctx, self.in_filename, self.in_code, rows_expr.data_type
            )
        if cols_expr.data_type != VarTypes.INT:
            raise E.WrongDimType(
                ctx, self.in_filename, self.in_code, cols_expr.data_type
            )
        if filename_expr.data_type != VarTypes.STRING:
            raise E.FilenameNotString(
                ctx, self.in_filename, self.in_code, filename_expr.data_type
            )
        tmp_vec = self.allocate_temp_vec(
            data_type=table_type,
            vec_dims=[rows_expr, cols_expr]
        )
        read_table_quad = Quad(
            op=Ops.READT,
            left=filename_expr,
            right=None,
            res=tmp_vec
        )
        self.quads.append(read_table_quad)
        self.operands_stack.append(tmp_vec)

    def visitRead_array(self, ctx: DoflirParser.Read_arrayContext):
        """Parse a read array from file statement."""
        self.visit(ctx.expr())
        filename_expr = self.operands_stack.pop()
        self.visit(ctx.token())
        len_expr = self.operands_stack.pop()
        arr_type = VarTypes[ctx.TYPE_NAME().getText().upper()]
        if filename_expr.data_type != VarTypes.STRING:
            raise E.FilenameNotString(
                ctx, self.in_filename, self.in_code, filename_expr.data_type
            )
        tmp_vec = self.allocate_temp_vec(
            data_type=arr_type,
            vec_dims=[len_expr]
        )
        read_array_quad = Quad(
            op=Ops.READA,
            left=filename_expr,
            right=None,
            res=tmp_vec
        )
        self.quads.append(read_array_quad)
        self.operands_stack.append(tmp_vec)

    def visitRead_console(self, ctx: DoflirParser.Read_consoleContext):
        """Parse a read input from console statement."""
        input_type = VarTypes[ctx.TYPE_NAME().getText().upper()]
        input_tmp = self.curr_scope.make_temp(temp_type=input_type)
        read_console_quad = Quad(
            op=Ops.READC,
            left=None,
            right=None,
            res=input_tmp
        )
        self.quads.append(read_console_quad)
        self.operands_stack.append(input_tmp)
