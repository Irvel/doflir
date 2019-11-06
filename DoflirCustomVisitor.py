from DoflirParser import DoflirParser
from DoflirVisitor import DoflirVisitor
from VariablesTable import VariablesTable
from VariablesTable import Variable
from SemanticCube import Ops
from SemanticCube import SemanticCube
from SemanticCube import VarTypes
from Quads import Quad
from collections import deque

import logging

class DoflirCustomVisitor(DoflirVisitor):

    def __init__(self):
        self.cube = SemanticCube()
        self.global_table = VariablesTable()
        self.scope_stack = deque()
        self.scope_stack.append(self.global_table)
        self.operands_stack = deque()
        self.operators_stack = deque()
        self.quads = []
        self._temp_num = 0

    @property
    def curr_scope(self):
        return self.scope_stack[-1]

    def new_temp(self, data_type):
        self._temp_num += 1
        return f"t{data_type.value[0]}_{self._temp_num}"

    def visitProgram(self, ctx: DoflirParser.ProgramContext):
        exprText = ctx.getText()
        print(f"Expression after tokenization = {exprText}")
        # print(ctx.fun_def())
        # print(ctx.statement())

        return self.visitChildren(ctx)

    # Visit a parse tree produced by DoflirParser#statement.
    def visitStatement(self, ctx: DoflirParser.StatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DoflirParser#vec_indexing.
    def visitVec_indexing(self, ctx: DoflirParser.Vec_indexingContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DoflirParser#vec_filtering.
    def visitVec_filtering(self, ctx: DoflirParser.Vec_filteringContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DoflirParser#fun_call.
    def visitFun_call(self, ctx: DoflirParser.Fun_callContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DoflirParser#fun_def.
    def visitFun_def(self, ctx: DoflirParser.Fun_defContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DoflirParser#parameters.
    def visitParameters(self, ctx: DoflirParser.ParametersContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DoflirParser#vec_list.
    def visitVec_list(self, ctx: DoflirParser.Vec_listContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DoflirParser#expr.
    def visitExpr(self, ctx: DoflirParser.ExprContext):
        exprText = ctx.getText()
        print(dir(ctx))
        print(f"Expression after tokenization = {exprText}")
        if ctx.NUMBER():
            num = ctx.NUMBER().getText()
            print(num)
            return num
        return self.visitChildren(ctx)

    # def visitBinExpr(self, ctx: DoflirParser.BinExprContext):
    #     return self.visitChildren(ctx)

    # Visit a parse tree produced by DoflirParser#tokExpr.
    # def visitTokExpr(self, ctx:DoflirParser.TokExprContext):
    #     tok = ctx.tok
    #     # print(dir(tok))
    #     print(tok.text)
    #     return self.visitChildren(ctx)

    def visitDeclaration(self, ctx: DoflirParser.DeclarationContext):
        var_id = ctx.ID().getText()
        var_type = ctx.TYPE_NAME().getText().upper()
        logging.debug(f"Declaring variable ({var_id}, {var_type})")
        if self.curr_scope.exists(var_id):
            raise Exception(f"Variable with ID {var_id} already used")
        self.curr_scope.declare_var(
            name=var_id, var_type=VarTypes[var_type]
        )
        return self.visitChildren(ctx)

    def visitAssignment(self, ctx: DoflirParser.AssignmentContext):
        if ctx.ID():
            # We need to do this again cause ID here is not an expr
            identifier = ctx.ID().getText()
            variable = self.curr_scope.search(identifier)
            if not variable:
                raise Exception(f"Attempted to use undeclared variable {identifier}")
            self.operands_stack.append((identifier, variable.data_type))
            # self.operands_stack.append(ctx.ID().getText())
            self.operators_stack.append(Ops.ASSIGN)
            # print("I am being assigned", ctx.ID())
            self.visitChildren(ctx)
            if self.operators_stack and self.operators_stack[-1] == Ops.ASSIGN:
                op_1, op_1_type = self.operands_stack.pop()
                op_2, op_2_type = self.operands_stack.pop()
                assert op_1_type == op_2_type
                new_quad = Quad(
                    op=Ops.ASSIGN,
                    left=op_1,
                    right="",
                    res=op_2
                )
                print(new_quad)
                self.quads.append(new_quad)
            return
            var_name = ctx.ID().getText()
            value = ctx.expr()
            if self.curr_scope.exists(var_name):
                pass
            if not self.var_table.search(var_name):
                var = Variable(
                    name=var_name, data_type="int", value=value, scope="ok"
                )
                self.var_table.add_symbol(var)
            else:
                # Array
                pass
        else:
            pass

    def generate_bin_quad(self):
        operator = self.operators_stack.pop()
        op_1, op_1_type = self.operands_stack.pop()
        op_2, op_2_type = self.operands_stack.pop()
        result_type = self.cube.result_type(
            op_1_type=op_1_type,
            op_2_type=op_2_type,
            operator=operator
        )
        if not result_type:
            raise Exception(
                f"Invalid operation: {op_1_type} {operator} {op_2_type} "
                "is not a valid operation."
            )
        temp_name = self.new_temp(data_type=result_type)
        new_quad = Quad(
            op=operator,
            left=op_1,
            right=op_2,
            res=temp_name
        )
        print(new_quad)
        self.quads.append(new_quad)
        self.operands_stack.append((temp_name, result_type))

    def try_op(self, op):
        if self.operators_stack and self.operators_stack[-1] == op:
            self.generate_bin_quad()

    def visitAddExpr(self, ctx: DoflirParser.AddExprContext):
        self.visit(ctx.expr(0))
        self.try_op(op=Ops.PLUS)
        self.operators_stack.append(Ops.PLUS)
        self.visit(ctx.expr(1))
        self.try_op(op=Ops.PLUS)

    def visitMultExpr(self, ctx: DoflirParser.AddExprContext):
        self.visit(ctx.expr(0))
        self.try_op(op=Ops.MULT)
        self.operators_stack.append(Ops.MULT)
        self.visit(ctx.expr(1))
        self.try_op(op=Ops.MULT)

    def visitDivExpr(self, ctx: DoflirParser.AddExprContext):
        self.visit(ctx.expr(0))
        self.try_op(op=Ops.DIV)
        self.operators_stack.append(Ops.DIV)
        self.visit(ctx.expr(1))
        self.try_op(op=Ops.DIV)

    def visitTokIdExpr(self, ctx: DoflirParser.TokIdExprContext):
        identifier = ctx.ID().getText()
        variable = self.curr_scope.search(identifier)
        if not variable:
            raise Exception(f"Attempted to use undeclared variable {identifier}")
        self.operands_stack.append((identifier, variable.data_type))

    # Visit a parse tree produced by DoflirParser#tokIntExpr.
    def visitTokIntExpr(self, ctx: DoflirParser.TokIntExprContext):
        num = int(ctx.tok_int.text)
        self.operands_stack.append((num, VarTypes.INT))
        # return

    def visitTokFloatExpr(self, ctx: DoflirParser.TokFloatExprContext):
        return float(ctx.tok_float.text), VarTypes.FLOAT

    # Visit a parse tree produced by DoflirParser#tokStrExpr.
    def visitTokStrExpr(self, ctx: DoflirParser.TokStrExprContext):
        return ctx.tok_str.text, VarTypes.STRING

    def visitTokBoolExpr(self, ctx: DoflirParser.TokBoolExprContext):
        return bool(ctx.tok_bool.text.capitalize()), VarTypes.BOOL

    # Visit a parse tree produced by DoflirParser#flow_call.
    def visitFlow_call(self, ctx: DoflirParser.Flow_callContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DoflirParser#condition.
    def visitCondition(self, ctx: DoflirParser.ConditionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DoflirParser#iterable.
    def visitIterable(self, ctx: DoflirParser.IterableContext):
        return self.visitChildren(ctx)
