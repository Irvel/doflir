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

    # Visit a parse tree produced by DoflirParser#statement.
    def visitStatement(self, ctx: DoflirParser.StatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DoflirParser#vec_indexing.
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

    # Visit a parse tree produced by DoflirParser#vec_filtering.
    def visitVec_filtering(self, ctx: DoflirParser.Vec_filteringContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DoflirParser#parameters.
    def visitParameters(self, ctx: DoflirParser.ParametersContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DoflirParser#expr.
    # def visitExpr(self, ctx: DoflirParser.ExprContext):
        # exprText = ctx.getText()
        # print(dir(ctx))
        # print(f"Expression after tokenization = {exprText}")
        # if ctx.NUMBER():
        #     num = ctx.NUMBER().getText()
        #     print(num)
        #     return num
        # return self.visitChildren(ctx)

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
        # self.operands_stack.append(
        #     (str(ctx.getText())[1:-1], VarTypes.STRING)
        # )
        self.operands_stack.append(
            self.global_table.declare_or_search(
                value=str(ctx.getText()),
                const_type=VarTypes.STRING,
                is_const=True,
            )
        )

    def visitTokBoolExpr(self, ctx: DoflirParser.TokBoolExprContext):
        # self.operands_stack.append(
        #     (bool(ctx.getText().capitalize()), VarTypes.BOOL)
        # )
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
        vec_id = ctx.declaration().ID().getText()
        vec_type = ctx.declaration().TYPE_NAME().getText().upper()
        if self.curr_scope.exists(vec_id):
            raise Exception(f"Vector with ID {vec_id} already used")
        is_glob = False
        if len(self.scope_stack) == 1:
            is_glob = True

        vec_dims = []
        for dim in ctx.vec_list().expr_list().expr():
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

    def visitVec_list(self, ctx: DoflirParser.Vec_listContext):
        return self.visitChildren(ctx)

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
            assert op_1.data_type == op_2.data_type
            op_2.is_initialized = True
            assign_quad = Quad(
                op=Ops.ASSIGN,
                left=op_1,
                right=None,
                res=op_2
            )
            self.quads.append(assign_quad)

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

        result_tmp = self.curr_scope.make_temp(temp_type=result_type)
        new_quad = Quad(
            op=operator,
            left=op_1,
            right=op_2,
            res=result_tmp
        )
        self.quads.append(new_quad)
        self.operands_stack.append(result_tmp)

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
        # self.fun_dir.add(fun_id)
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

            # ret_tmp = self.new_temp(data_type=target_fun.ret_type)
            # ret_tmp = f"{fun_id}_{ret_tmp}"
            self.operands_stack.append(ret_tmp)

    def visitMain_def(self, ctx: DoflirParser.Main_defContext):
        pending_goto = self.pending_jumps_stack.pop()
        self.quads[pending_goto].res = QuadJump(self.current_quad_idx + 1)
        self.visitChildren(ctx)

    def visitPrint_stmt(self, ctx: DoflirParser.Print_stmtContext):
        self.visitChildren(ctx)
        print_expr = self.operands_stack.pop()
        print_quad = Quad(
            op=Ops.PRINT,
            left=None,
            right=None,
            res=print_expr
        )
        self.quads.append(print_quad)

    # Visit a parse tree produced by DoflirParser#condition.
    def visitCondition(self, ctx: DoflirParser.ConditionContext):
        return self.visitChildren(ctx)
