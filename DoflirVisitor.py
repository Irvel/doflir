# Generated from Doflir.g4 by ANTLR 4.7.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .DoflirParser import DoflirParser
else:
    from DoflirParser import DoflirParser

# This class defines a complete generic visitor for a parse tree produced by DoflirParser.

class DoflirVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by DoflirParser#program.
    def visitProgram(self, ctx:DoflirParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#statement.
    def visitStatement(self, ctx:DoflirParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#assignment.
    def visitAssignment(self, ctx:DoflirParser.AssignmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#vec_indexing.
    def visitVec_indexing(self, ctx:DoflirParser.Vec_indexingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#vec_filtering.
    def visitVec_filtering(self, ctx:DoflirParser.Vec_filteringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#fun_call.
    def visitFun_call(self, ctx:DoflirParser.Fun_callContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#fun_def.
    def visitFun_def(self, ctx:DoflirParser.Fun_defContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#parameters.
    def visitParameters(self, ctx:DoflirParser.ParametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#vec_list.
    def visitVec_list(self, ctx:DoflirParser.Vec_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#expr.
    def visitExpr(self, ctx:DoflirParser.ExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#function_call.
    def visitFunction_call(self, ctx:DoflirParser.Function_callContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#flow_call.
    def visitFlow_call(self, ctx:DoflirParser.Flow_callContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#condition.
    def visitCondition(self, ctx:DoflirParser.ConditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#iterable.
    def visitIterable(self, ctx:DoflirParser.IterableContext):
        return self.visitChildren(ctx)



del DoflirParser