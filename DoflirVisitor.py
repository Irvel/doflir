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


    # Visit a parse tree produced by DoflirParser#main_def.
    def visitMain_def(self, ctx:DoflirParser.Main_defContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#proc_body.
    def visitProc_body(self, ctx:DoflirParser.Proc_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#statement.
    def visitStatement(self, ctx:DoflirParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#assignment.
    def visitAssignment(self, ctx:DoflirParser.AssignmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#declaration_stmt.
    def visitDeclaration_stmt(self, ctx:DoflirParser.Declaration_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#declaration.
    def visitDeclaration(self, ctx:DoflirParser.DeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#fun_def.
    def visitFun_def(self, ctx:DoflirParser.Fun_defContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#parameters.
    def visitParameters(self, ctx:DoflirParser.ParametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#fun_call_stmt.
    def visitFun_call_stmt(self, ctx:DoflirParser.Fun_call_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#fun_call.
    def visitFun_call(self, ctx:DoflirParser.Fun_callContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#flow_call.
    def visitFlow_call(self, ctx:DoflirParser.Flow_callContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#expr_list.
    def visitExpr_list(self, ctx:DoflirParser.Expr_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#tok_list.
    def visitTok_list(self, ctx:DoflirParser.Tok_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#filter_list.
    def visitFilter_list(self, ctx:DoflirParser.Filter_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#vec_declaration.
    def visitVec_declaration(self, ctx:DoflirParser.Vec_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#vec_declaration_stmt.
    def visitVec_declaration_stmt(self, ctx:DoflirParser.Vec_declaration_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#vec_list.
    def visitVec_list(self, ctx:DoflirParser.Vec_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#vec_init_list.
    def visitVec_init_list(self, ctx:DoflirParser.Vec_init_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#mat_init_list.
    def visitMat_init_list(self, ctx:DoflirParser.Mat_init_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#vec_indexing.
    def visitVec_indexing(self, ctx:DoflirParser.Vec_indexingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#vec_filtering.
    def visitVec_filtering(self, ctx:DoflirParser.Vec_filteringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#readCExpr.
    def visitReadCExpr(self, ctx:DoflirParser.ReadCExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#ltEqExpr.
    def visitLtEqExpr(self, ctx:DoflirParser.LtEqExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#notEqExpr.
    def visitNotEqExpr(self, ctx:DoflirParser.NotEqExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#dotExpr.
    def visitDotExpr(self, ctx:DoflirParser.DotExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#gtExpr.
    def visitGtExpr(self, ctx:DoflirParser.GtExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#subExpr.
    def visitSubExpr(self, ctx:DoflirParser.SubExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#gtEqExpr.
    def visitGtEqExpr(self, ctx:DoflirParser.GtEqExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#parenExpr.
    def visitParenExpr(self, ctx:DoflirParser.ParenExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#ltExpr.
    def visitLtExpr(self, ctx:DoflirParser.LtExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#divExpr.
    def visitDivExpr(self, ctx:DoflirParser.DivExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#readTExpr.
    def visitReadTExpr(self, ctx:DoflirParser.ReadTExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#tokExpr.
    def visitTokExpr(self, ctx:DoflirParser.TokExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#readAExpr.
    def visitReadAExpr(self, ctx:DoflirParser.ReadAExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#vecIdxExpr.
    def visitVecIdxExpr(self, ctx:DoflirParser.VecIdxExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#orExpr.
    def visitOrExpr(self, ctx:DoflirParser.OrExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#multExpr.
    def visitMultExpr(self, ctx:DoflirParser.MultExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#matInitExpr.
    def visitMatInitExpr(self, ctx:DoflirParser.MatInitExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#posExpr.
    def visitPosExpr(self, ctx:DoflirParser.PosExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#eqExpr.
    def visitEqExpr(self, ctx:DoflirParser.EqExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#notExpr.
    def visitNotExpr(self, ctx:DoflirParser.NotExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#intDivExpr.
    def visitIntDivExpr(self, ctx:DoflirParser.IntDivExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#addExpr.
    def visitAddExpr(self, ctx:DoflirParser.AddExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#negExpr.
    def visitNegExpr(self, ctx:DoflirParser.NegExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#vecInitExpr.
    def visitVecInitExpr(self, ctx:DoflirParser.VecInitExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#unExpr.
    def visitUnExpr(self, ctx:DoflirParser.UnExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#powExpr.
    def visitPowExpr(self, ctx:DoflirParser.PowExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#matMultExpr.
    def visitMatMultExpr(self, ctx:DoflirParser.MatMultExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#vecFiltExpr.
    def visitVecFiltExpr(self, ctx:DoflirParser.VecFiltExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#andExpr.
    def visitAndExpr(self, ctx:DoflirParser.AndExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#tokIdExpr.
    def visitTokIdExpr(self, ctx:DoflirParser.TokIdExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#tokStrExpr.
    def visitTokStrExpr(self, ctx:DoflirParser.TokStrExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#tokBoolExpr.
    def visitTokBoolExpr(self, ctx:DoflirParser.TokBoolExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#tokIntExpr.
    def visitTokIntExpr(self, ctx:DoflirParser.TokIntExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#tokFloatExpr.
    def visitTokFloatExpr(self, ctx:DoflirParser.TokFloatExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#ifStmt.
    def visitIfStmt(self, ctx:DoflirParser.IfStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#ifElseStmt.
    def visitIfElseStmt(self, ctx:DoflirParser.IfElseStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#whileStmt.
    def visitWhileStmt(self, ctx:DoflirParser.WhileStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#read_table.
    def visitRead_table(self, ctx:DoflirParser.Read_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#read_array.
    def visitRead_array(self, ctx:DoflirParser.Read_arrayContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#read_console.
    def visitRead_console(self, ctx:DoflirParser.Read_consoleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#write_file_stmt.
    def visitWrite_file_stmt(self, ctx:DoflirParser.Write_file_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#plot_stmt.
    def visitPlot_stmt(self, ctx:DoflirParser.Plot_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#print_stmt.
    def visitPrint_stmt(self, ctx:DoflirParser.Print_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DoflirParser#println_stmt.
    def visitPrintln_stmt(self, ctx:DoflirParser.Println_stmtContext):
        return self.visitChildren(ctx)



del DoflirParser