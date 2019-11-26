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

import logging


class DoflirCustomVisitor(DoflirVisitor):

    def __init__(self):
        self.cube = SemanticCube()
        self.global_table = VariablesTable()
        self.fun_dir = FunDir()
        self.scope_stack = deque()
        self.scope_stack.append(self.global_table)
        self.operands_stack = deque()
        self.operators_stack = deque()
        self.pending_jumps_stack = deque()
        self.return_type_stack = deque()
        self.quads = []
        self._temp_num = 0

    @property
    def curr_scope(self):
        return self.scope_stack[-1]

    @property
    def current_quad_idx(self):
        return len(self.quads) - 1

    def new_temp(self, data_type):
        self._temp_num += 1
        return f"t{data_type.value[0]}_{self._temp_num}"

    def visitProgram(self, ctx: DoflirParser.ProgramContext):
        if ctx.statement:
            for stmt in ctx.statement():
                self.visit(stmt)

        goto_quad = Quad(
            op=Ops.GOTO,
            left=None,
            right=None,
            res=None
        )
        self.quads.append(goto_quad)
        self.pending_jumps_stack.append(self.current_quad_idx)
        if ctx.fun_def:
            for dfn in ctx.fun_def():
                self.visit(dfn)
        self.visit(ctx.main_def())
        self.print_stats()
        print_quads(quads=self.quads, viz_variant="name")
        # print_quads(quads=self.quads, viz_variant="address")
        # print_quads(quads=self.quads, viz_variant="type")
        return self.generate_obj_code()

    def generate_obj_code(self):
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

    def visitStatement(self, ctx: DoflirParser.StatementContext):
        return self.visitChildren(ctx)

    def visitVec_indexing(self, ctx: DoflirParser.Vec_indexingContext):
        vec_id = ctx.ID().getText()
        vec = self.curr_scope.search(vec_id) or self.global_table.search(vec_id)
        if not vec:
            raise Exception(
                f"Attempted to use undeclared vector {vec_id}"
            )
        if len(vec.vec_dims) != len(ctx.expr_list().expr()):
            raise Exception(
                f"Provided more indices than declared in {vec_id}"
            )
        vec_idx = []
        for idx_num, idx_expr in enumerate(ctx.expr_list().expr()):
            self.visit(idx_expr)
            idx_res = self.operands_stack.pop()
            if idx_res.data_type != VarTypes.INT:
                raise Exception(f"Vector index must be int {idx_res.data_type} given instead.")
            vec_idx.append(idx_res)
            ver_quad = Quad(
                op=Ops.VER,
                left=idx_res,
                right=None,
                res=vec.vec_dims[idx_num]
            )
            self.quads.append(ver_quad)
        self.operands_stack.append(
            VecIdx(vec_id=vec_id, idx=vec_idx, address=vec.address,
                   data_type=vec.data_type)
        )

    def visitVec_filtering(self, ctx: DoflirParser.Vec_filteringContext):
        vec_id = ctx.ID().getText()
        vec = self.curr_scope.search(vec_id) or self.global_table.search(vec_id)
        if not vec:
            raise Exception(
                f"Attempted to use undeclared vector {vec_id}"
            )
        is_reduced = False
        vec_filters = []
        for idx, vec_filter_ctx in enumerate(ctx.filter_list().FILTER()):
            vec_filter = self.cube.filter_to_enum(vec_filter_ctx.getText())
            if self.cube.is_reduced(vec_filter=vec_filter):
                is_reduced = True
                if idx < len(ctx.filter_list().FILTER()) - 1:
                    raise Exception(
                        f"{vec_filter.value} Reduces the vector to a number before other filters."
                    )
            vec_filters.append(vec_filter)

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
        # Determine shape of the given vector with the depth level
        # Are there further nested levels?
        # print(ctx.depth(), ctx.getRuleIndex(), ctx.getSourceInterval())
        vec_init_list = []
        for tok in ctx.vec_init_list().tok_list().token():
            self.visit(tok)
            vec_init_list.append(self.operands_stack.pop())
        dim_size = self.curr_scope.make_const(
            value=len(vec_init_list),
            const_type=VarTypes.INT,
        )
        tmp_vec = self.allocate_temp_vec(
            data_type=vec_init_list[0].data_type,
            vec_dims=[dim_size]
        )

        for vec_idx, init_val in enumerate(vec_init_list):
            vec_idx_const = self.curr_scope.make_const(
                value=vec_idx,
                const_type=VarTypes.INT,
            )
            dst_idx = VecIdx(vec_id=tmp_vec.name, idx=[vec_idx_const],
                             address=tmp_vec.address,
                             data_type=tmp_vec.data_type)
            if init_val.data_type != dst_idx.data_type:
                raise Exception("Vector values must be of homogeneous type.")
            assign_quad = Quad(
                op=Ops.ASSIGN,
                left=init_val,
                right=None,
                res=dst_idx
            )
            self.quads.append(assign_quad)

        self.operands_stack.append(tmp_vec)
        # Parse expression values
        # Allocate a temp vector that will hold the parsed values
        # Put the allocated vector as a pending operand

    def visitMatInitExpr(self, ctx: DoflirParser.MatInitExprContext):
        col_size_num = None
        mat_init_list = []
        for vec_list in ctx.mat_init_list().vec_init_list():
            vec_init_list = []
            for tok in vec_list.tok_list().token():
                self.visit(tok)
                vec_init_list.append(self.operands_stack.pop())
            if col_size_num is None:
                col_size_num = len(vec_init_list)
            elif col_size_num != len(vec_init_list):
                raise Exception(
                    "All matrix columns must be of the same size")
            mat_init_list.append(vec_init_list)

        row_size = self.curr_scope.make_const(
            value=len(mat_init_list),
            const_type=VarTypes.INT,
        )
        col_size = self.curr_scope.make_const(
            value=col_size_num,
            const_type=VarTypes.INT,
        )
        tmp_vec = self.allocate_temp_vec(
            data_type=mat_init_list[0][0].data_type,
            vec_dims=[row_size, col_size]
        )

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
                    vec_id=tmp_vec.name,
                    idx=[row_idx_const, col_idx_const],
                    address=tmp_vec.address,
                    data_type=tmp_vec.data_type
                )
                if init_val.data_type != dst_idx.data_type:
                    raise Exception("Matrix values must be of homogeneous type.")
                assign_quad = Quad(
                    op=Ops.ASSIGN,
                    left=init_val,
                    right=None,
                    res=dst_idx
                )
                self.quads.append(assign_quad)
        self.operands_stack.append(tmp_vec)

    def visitParameters(self, ctx: DoflirParser.ParametersContext):
        return self.visitChildren(ctx)

    def visitTokIdExpr(self, ctx: DoflirParser.TokIdExprContext):
        var_id = ctx.ID().getText()
        var = self.curr_scope.search(var_id) or self.global_table.search(var_id)
        if not var:
            raise Exception(
                f"Attempted to use undeclared variable {var_id}"
            )
        self.operands_stack.append(var)

    def visitTokIntExpr(self, ctx: DoflirParser.TokIntExprContext):
        self.operands_stack.append(
            self.global_table.declare_or_search(
                value=int(ctx.getText()),
                const_type=VarTypes.INT,
                is_const=True,
            )
        )

    def visitTokFloatExpr(self, ctx: DoflirParser.TokFloatExprContext):
        self.operands_stack.append(
            self.global_table.declare_or_search(
                value=float(ctx.getText()),
                const_type=VarTypes.FLOAT,
                is_const=True,
            )
        )

    def visitTokStrExpr(self, ctx: DoflirParser.TokStrExprContext):
        self.operands_stack.append(
            self.global_table.declare_or_search(
                value=str(ctx.getText()),
                const_type=VarTypes.STRING,
                is_const=True,
            )
        )

    def visitTokBoolExpr(self, ctx: DoflirParser.TokBoolExprContext):
        self.operands_stack.append(
            self.global_table.declare_or_search(
                value=bool(ctx.getText().capitalize()),
                const_type=VarTypes.BOOL,
                is_const=True,
            )
        )

    def visitDeclaration_stmt(self, ctx: DoflirParser.DeclarationContext):
        var_id = ctx.declaration().ID().getText()
        var_type = ctx.declaration().TYPE_NAME().getText().upper()
        logging.debug(f"Declaring variable ({var_id}, {var_type})")
        if self.curr_scope.exists(var_id):
            raise Exception(f"Variable with ID {var_id} already used")
        is_glob = False
        if len(self.scope_stack) == 1:
            is_glob = True
        self.curr_scope.declare_var(
            name=var_id, var_type=VarTypes[var_type], is_glob=is_glob
        )
        return self.visitChildren(ctx)

    def visitVec_declaration_stmt(self, ctx: DoflirParser.Vec_declaration_stmtContext):
        vec_id = ctx.vec_declaration().declaration().ID().getText()
        vec_type = ctx.vec_declaration().declaration().TYPE_NAME().getText().upper()
        if self.curr_scope.exists(vec_id):
            raise Exception(f"Vector with ID {vec_id} already used")
        is_glob = False
        if len(self.scope_stack) == 1:
            is_glob = True

        vec_dims = []
        for dim in ctx.vec_declaration().vec_list().tok_list().token():
            self.visit(dim)
            dim_expr = self.operands_stack.pop()
            if dim_expr.data_type != VarTypes.INT:
                raise Exception(f"Vector dimensions must be int {dim_expr.data_type} given instead.")
            vec_dims.append(dim_expr)
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
        if ctx.ID():
            # We need to do this again cause ID here is not an expr
            identifier = ctx.ID().getText()
            variable = (
                self.curr_scope.search(identifier) or
                self.global_table.search(identifier)
            )
            if not variable:
                raise Exception(f"Attempted to use undeclared variable {identifier}")
            self.operands_stack.append(variable)

        elif ctx.vec_indexing():
            identifier = ctx.vec_indexing().ID().getText()
            vec = (
                self.curr_scope.search(identifier) or
                self.global_table.search(identifier)
            )
            if not vec:
                raise Exception(f"Attempted to use undeclared vector {identifier}")
            self.visit(ctx.vec_indexing())

        self.operators_stack.append(Ops.ASSIGN)
        self.visit(ctx.expr())
        if self.operators_stack and self.operators_stack[-1] == Ops.ASSIGN:
            op_1 = self.operands_stack.pop()
            op_2 = self.operands_stack.pop()
            if op_1.data_type != op_2.data_type:
                raise Exception(
                    f'The type between '
                    f'"{op_1.value} {op_1.data_type}"'
                    f' and "{op_2.value} {op_2.data_type}" must be the same'
                )
            if op_1.vec_dims or op_2.vec_dims:
                if not self.check_size_dims(op_1.vec_dims, op_2.vec_dims):
                    raise Exception(
                        f'Number of dimensions must be the same between '
                        f' "{op_1}" and "{op_2}"'
                    )
            op_2.is_initialized = True
            assign_quad = Quad(
                op=Ops.ASSIGN,
                left=op_1,
                right=None,
                res=op_2
            )
            self.quads.append(assign_quad)

    def check_mat_mult_dims(self, dims_1, dims_2):
        # Two matrices can be multiplied only when the number of columns in
        # the first equals the number of rows in the second
        col_1 = dims_1[1].value
        row_2 = dims_2[0].value
        return col_1 == row_2

    def check_size_dims(self, dims_1, dims_2):
        if dims_1 and dims_2:
            return len(dims_1) == len(dims_2)
        else:
            return False

    def check_dims_match(self, dims_1, dims_2):
        if self.check_size_dims(dims_1, dims_2):
            for dim_1, dim_2 in zip(dims_1, dims_2):
                if dim_1.value != dim_2.value:
                    return False
        else:
            return False
        return True

    def generate_bin_quad(self):
        operator = self.operators_stack.pop()
        op_2 = self.operands_stack.pop()
        op_1 = self.operands_stack.pop()
        result_type = self.cube.result_type(
            op_1_type=op_1.data_type,
            op_2_type=op_2.data_type,
            operator=operator
        )
        if not result_type:
            raise Exception(
                f"Invalid operation: {op_1.data_type} {operator} {op_2.data_type} "
                "is not a valid operation."
            )
        if not op_1.is_initialized:
            raise Exception(f"Attempt too use uninitialized variable.{op_1}")
        if not op_2.is_initialized:
            raise Exception(f"Attempt too use uninitialized variable.{op_2}")

        both_are_vec = op_1.vec_dims and op_2.vec_dims
        if both_are_vec or not both_are_vec:
            if both_are_vec:
                if operator == Ops.MAT_MULT:
                    if len(op_1.vec_dims) != 2 or len(op_2.vec_dims) != 2:
                        raise Exception(
                            f'Cannot perform matrix mult on non-matrices'
                        )
                    if not self.check_mat_mult_dims(op_1.vec_dims,
                                                    op_2.vec_dims):
                        raise Exception(
                            f'Number of cols and rows mismatch for mat mult.'
                            f'{op_1.vec_dims} vs {op_2.vec_dims}'
                        )
                    # Resulting dim of mat mult (n x m) @ (f x v) is (n x v)
                    result_tmp = self.curr_scope.make_temp(
                        temp_type=result_type,
                        vec_dims=[op_1.vec_dims[0], op_2.vec_dims[1]],
                    )
                else:
                    if not self.check_size_dims(op_2.vec_dims, op_2.vec_dims):
                        raise Exception(
                            f'Number of dimensions must be the same between '
                            f' "{op_1}" and "{op_2}"'
                        )
                    if not self.check_dims_match(op_2.vec_dims, op_2.vec_dims):
                        raise Exception(
                            f'Dimension size must match between '
                            f'"{op_1.value}{op_1.vec_dims}"'
                            f' and {op_2.value}{op_2.vec_dims}'
                        )
                    result_tmp = self.curr_scope.make_temp(temp_type=result_type,
                                                           vec_dims=op_1.vec_dims)
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
            raise Exception("Operands need to be both vector or non vector")

    def try_op(self, op):
        if self.operators_stack and self.operators_stack[-1] == op:
            self.generate_bin_quad()

    def visitUnOpExpr(self, ctx, operator):
        self.visit(ctx.expr())
        operand = self.operands_stack.pop()
        if not operand.is_initialized:
            raise Exception(f"Attempt too use uninitialized variable.{operand}")

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
        self.visitUnOpExpr(ctx=ctx, operator=Ops.NEG)

    def visitPosExpr(self, ctx: DoflirParser.PosExprContext):
        self.visitUnOpExpr(ctx=ctx, operator=Ops.POS)

    def visitBinOpExpr(self, ctx, operator):
        self.visit(ctx.expr(0))
        self.try_op(op=operator)
        self.operators_stack.append(operator)
        self.visit(ctx.expr(1))
        self.try_op(op=operator)

    def visitMatMultExpr(self, ctx: DoflirParser.MatMultExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.MAT_MULT)

    def visitMultExpr(self, ctx: DoflirParser.MultExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.MULT)

    def visitDivExpr(self, ctx: DoflirParser.DivExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.DIV)

    def visitIntDivExpr(self, ctx: DoflirParser.IntDivExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.INT_DIV)

    def visitPowExpr(self, ctx: DoflirParser.PowExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.POW)

    def visitAddExpr(self, ctx: DoflirParser.AddExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.PLUS)

    def visitSubExpr(self, ctx: DoflirParser.SubExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.MINUS)

    def visitGtExpr(self, ctx: DoflirParser.GtExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.GT)

    def visitGtEqExpr(self, ctx: DoflirParser.GtEqExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.GT_EQ)

    def visitLtExpr(self, ctx: DoflirParser.LtExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.LT)

    def visitLtEqExpr(self, ctx: DoflirParser.LtEqExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.LT_EQ)

    def visitEqExpr(self, ctx: DoflirParser.EqExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.EQ)

    def visitNotEqExpr(self, ctx: DoflirParser.NotEqExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.NOT_EQ)

    def visitAndExpr(self, ctx: DoflirParser.AndExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.AND_)

    def visitOrExpr(self, ctx: DoflirParser.OrExprContext):
        self.visitBinOpExpr(ctx=ctx, operator=Ops.OR_)

    def visitIfCondition(self, ctx):
        self.visit(ctx.expr())
        expr_res = self.operands_stack.pop()
        if expr_res.data_type is not VarTypes.BOOL:
            raise Exception("Type mismatch with {expr_res} of type {expr_res_type}")
        gotof_quad = Quad(
            op=Ops.GOTOF,
            left=expr_res,
            right=None,
            res=None
        )
        self.quads.append(gotof_quad)
        self.pending_jumps_stack.append(self.current_quad_idx)

    def visitIfStmt(self, ctx: DoflirParser.IfStmtContext):
        self.visitIfCondition(ctx)
        self.visit(ctx.proc_body())
        pending_gotof = self.pending_jumps_stack.pop()
        self.quads[pending_gotof].res = QuadJump(self.current_quad_idx + 1)
        # TODO: Maybe don't do anything if the current_quad is the last?

    def visitIfElseStmt(self, ctx: DoflirParser.IfElseStmtContext):
        self.visitIfCondition(ctx)
        self.visit(ctx.proc_body(0))
        pending_goto = self.pending_jumps_stack.pop()
        self.quads[pending_goto].res = QuadJump(self.current_quad_idx + 2)
        # Jump the Else statement
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
        cond_quad_idx = self.current_quad_idx + 1
        self.visitIfCondition(ctx)
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
        fun_id = ctx.ID().getText()
        return_type = self.cube.type_to_enum(
            type_str=ctx.TYPE_NAME().getText()
        )

        if self.global_table.exists(var_name=fun_id):
            raise Exception("Cannot define function with variable of the same name")
        if self.fun_dir.exists(fun_name=fun_id):
            raise Exception("Cannot define two functions the same name")
        self.scope_stack.append(VariablesTable())
        params = None
        if ctx.parameters():
            params = []
            for param in ctx.parameters().declaration():
                param_id = param.ID().getText()
                param_type_str = param.TYPE_NAME().getText()
                if self.global_table.exists(param_id):
                    raise Exception(f"Parameter with ID {param_id} already globally used")
                if self.fun_dir.exists(param_id) or fun_id == param_id:
                    raise Exception(f"Parameter with ID {param_id} is same name of function")
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
            for param in ctx.parameters().vec_declaration():
                param_id = param.declaration().ID().getText()
                param_type_str = param.declaration().TYPE_NAME().getText()
                if self.global_table.exists(param_id):
                    raise Exception(f"Parameter with ID {param_id} already globally used")
                if self.fun_dir.exists(param_id) or fun_id == param_id:
                    raise Exception(f"Parameter with ID {param_id} is same name of function")
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
                        raise Exception(f"Vector dimensions must be int {dim_expr.data_type} given instead.")
                    vec_dims.append(dim_expr)
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
        ret_val = VarTypes.VOID
        return_type = self.return_type_stack[-1]
        if ctx.expr():
            self.visit(ctx.expr())
            ret_val = self.operands_stack.pop()
            if return_type != ret_val.data_type:
                raise Exception(f"Returning a different type than what was defined.")
        ret_quad = Quad(Ops.RETURN_, None, None, ret_val)
        self.quads.append(ret_quad)

    def visitFun_call(self, ctx: DoflirParser.Fun_callContext):
        fun_id = ctx.ID().getText()
        target_fun = self.fun_dir.search(fun_name=fun_id)
        if not target_fun:
            raise Exception(f"\"{fun_id}\" Has not been defined.")
        era_quad = Quad(
            op=Ops.ERA,
            left=target_fun,
            right=None,
            res=None
        )
        self.quads.append(era_quad)

        if ctx.expr_list():
            num_args = len(ctx.expr_list().expr())
            if not target_fun.num_params == num_args:
                raise Exception(f"\"{fun_id}\" different num of parameters provided {target_fun.num_params} vs {num_args}")
            if not num_args == 0:
                par_num = 1
                for expr, param in zip(ctx.expr_list().expr(), target_fun.params):
                    self.visit(expr)
                    expr_res = self.operands_stack.pop()

                    assert expr_res.data_type == param.param_type
                    param_quad = Quad(
                        op=Ops.PARAM,
                        left=expr_res,
                        right=None,
                        res=Param(par_num),
                    )
                    self.quads.append(param_quad)
                    par_num += 1

        gosub_quad = Quad(
            op=Ops.GOSUB,
            left=target_fun,
            right=None,
            res=None
        )
        self.quads.append(gosub_quad)

        if target_fun.ret_type != VarTypes.VOID:
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
        pending_goto = self.pending_jumps_stack.pop()
        self.quads[pending_goto].res = QuadJump(self.current_quad_idx + 1)
        self.visitChildren(ctx)

    def visitPrint_stmt(self, ctx: DoflirParser.Print_stmtContext):
        for expr in ctx.expr_list().expr():
            self.visit(expr)
            print_expr = self.operands_stack.pop()
            if not print_expr.is_initialized:
                raise Exception(f"Attempt too use uninitialized variable.{print_expr}")
            print_quad = Quad(
                op=Ops.PRINT,
                left=None,
                right=None,
                res=print_expr
            )
            self.quads.append(print_quad)

    def visitPrintln_stmt(self, ctx: DoflirParser.Println_stmtContext):
        for expr in ctx.expr_list().expr():
            self.visit(expr)
            print_expr = self.operands_stack.pop()
            if not print_expr.is_initialized:
                raise Exception(f"Attempt too use uninitialized variable.{print_expr}")
            print_quad = Quad(
                op=Ops.PRINTLN,
                left=None,
                right=None,
                res=print_expr
            )
            self.quads.append(print_quad)

    def visitPlot_stmt(self, ctx: DoflirParser.Plot_stmtContext):
        self.visit(ctx.expr())
        plot_expr = self.operands_stack.pop()
        if not plot_expr.is_initialized:
            raise Exception(f"Attempt too use uninitialized variable.{plot_expr}")
        self.quads.append(
            Quad(
                op=Ops.PLOT,
                left=None,
                right=None,
                res=plot_expr
            )
        )

    def visitWrite_file_stmt(self, ctx: DoflirParser.Write_file_stmtContext):
        self.visit(ctx.expr(0))
        write_expr = self.operands_stack.pop()
        if not write_expr.is_initialized:
            raise Exception(f"Attempt too use uninitialized variable.{write_expr}")
        self.visit(ctx.expr(1))
        filename_expr = self.operands_stack.pop()
        if not filename_expr.is_initialized:
            raise Exception(f"Attempt too use uninitialized variable.{filename_expr}")
        if filename_expr.data_type != VarTypes.STRING:
            raise Exception("Filename to read from must be string.")
        self.quads.append(
            Quad(
                op=Ops.WRITEF,
                left=write_expr,
                right=None,
                res=filename_expr
            )
        )

    def visitRead_table(self, ctx: DoflirParser.Read_tableContext):
        self.visit(ctx.expr())
        filename_expr = self.operands_stack.pop()
        self.visit(ctx.token(0))
        rows_expr = self.operands_stack.pop()
        self.visit(ctx.token(1))
        cols_expr = self.operands_stack.pop()
        table_type = VarTypes[ctx.TYPE_NAME().getText().upper()]
        if filename_expr.data_type != VarTypes.STRING:
            raise Exception("Filename to read from must be string.")
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
        self.visit(ctx.expr())
        filename_expr = self.operands_stack.pop()
        self.visit(ctx.token())
        len_expr = self.operands_stack.pop()
        arr_type = VarTypes[ctx.TYPE_NAME().getText().upper()]
        if filename_expr.data_type != VarTypes.STRING:
            raise Exception("Filename to read from must be string.")
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

        return self.visitChildren(ctx)
