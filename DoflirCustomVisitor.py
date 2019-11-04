from DoflirParser import DoflirParser
from DoflirVisitor import DoflirVisitor
from VariablesTable import VariablesTable
from VariablesTable import Variable
from SemanticCube import VarTypes
from SemanticCube import Ops
from collections import deque

import logging
import SemanticCube


class DoflirCustomVisitor(DoflirVisitor):

    def __init__(self):
        self.cube = SemanticCube.make_cube()
        self.global_table = VariablesTable()
        self.context_stack = deque()
        self.context_stack.append(self.global_table)

    @property
    def curr_context(self):
        return self.context_stack[-1]

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
        logging.debug("Declaring variable with ID")
        var_id = ctx.ID()
        if self.curr_context.exists(var_id):
            raise Exception(f"Variable with ID {var_id} already used")
        self.curr_context.declare_var(
            name=var_id, var_type=VarTypes[ctx.TYPE_NAME()]
        )
        return self.visitChildren(ctx)

    def visitAssignment(self, ctx: DoflirParser.AssignmentContext):
        print("I am being assigned", ctx.ID())
        if ctx.ID():
            var_name = ctx.ID()
            value = ctx.expr()
            if not self.var_table.search(var_name):
                var = Variable(
                    name=var_name, data_type="int", value=value, scope="ok"
                )
                self.var_table.add_symbol(var)
            else:
                pass
                # TODO: Throw error, variable already declared
        else:
            pass
        return self.visitChildren(ctx)

    def visitAddExpr(self, ctx: DoflirParser.AddExprContext):
        # ch_ret = self.visitChildren(ctx)
        left_val, left_type = self.visit(ctx.expr(0))
        right_val, right_type = self.visit(ctx.expr(1))
        result_val = left_val + right_val
        result_type = self.cube[(left_type, right_type, Ops.PLUS)]
        print("Out res = ", result_type)
        # print("hello1", left)
        # print("hello2", right)
        return result_val

    # Visit a parse tree produced by DoflirParser#tokIntExpr.
    def visitTokIntExpr(self, ctx: DoflirParser.TokIntExprContext):
        return int(ctx.tok_int.text), VarTypes.INT

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
