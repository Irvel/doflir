grammar Doflir;

program: (fun_def| statement | NL)* main_def (fun_def | NL)* EOF;

main_def: 'define main''{' proc_body '}' ;

proc_body: (NL*|statement) (NL|statement)*;

statement: (assignment | condition | iterable | vec_filtering | fun_call_stmt | declaration_stmt | print_stmt | vec_declaration_stmt | flow_call);

assignment: (ID|vec_indexing) '=' expr ';' ;
declaration_stmt: declaration ';' ;
declaration: ID '->' TYPE_NAME ;

fun_def
	: 'define' ID '->' TYPE_NAME '(' parameters? ')' '{' proc_body '}'  // Function definition.
	;
parameters: declaration (',' declaration)*;
fun_call_stmt: fun_call ';' ;
fun_call: ID '(' expr_list? ')' ;  // Function call.
flow_call: 'return' (expr)? ';' NL*;

expr_list: (expr | (expr (',' expr)*)) ;

vec_declaration_stmt: declaration vec_list ';' ;
vec_list: '[' expr_list ']';
vec_indexing: ID '[' expr_list ']' ';' ;
vec_filtering: (ID|vec_indexing) '{' expr_list '}' ';';

expr
	: '('expr')'                   #parenExpr
	| vec_indexing                 #unExpr
	| vec_filtering                #unExpr
	| fun_call                     #unExpr
	| <assoc=right> expr '^' expr  #powExpr    // Exponentiation.
	| '-' expr                     #negExpr    // Negative unary symbol.
	| '+' expr                     #posExpr    // Positive unary simbol.
    | 'not' expr                   #unExpr     // Negation.
	| expr  '@'  expr              #matExpr    // Matrix multiplication.
	| expr '..'  expr              #dotExpr    // Dot product.
	| expr  '*'  expr              #multExpr   // Multiplication.
	| expr  '/'  expr              #divExpr    // Float division.
	| expr '//'  expr              #intDivExpr // Integer division.
    | expr  '+'  expr              #addExpr    // Addition.
    | expr  '-'  expr              #subExpr    // Subtraction.
    | expr  '>'  expr              #gtExpr     // Logical greater than.
    | expr '>='  expr              #gtEqExpr   // Logical or equal greater than.
    | expr  '<'  expr              #ltExpr     // Logical less than.
    | expr '<='  expr              #ltEqExpr   // Logical less or equal than.
    | expr '=='  expr              #eqExpr     // Logical equal.
    | expr '!='  expr              #notEqExpr  // Logical not equal.
    | expr 'and' expr              #andExpr    // Logical and.
    | expr  'or' expr              #orExpr     // Logical or.
	| tok_id=ID                    #tokIdExpr
    | tok_str=STRING_LITERAL       #tokStrExpr
    | tok_bool=BOOL                #tokBoolExpr
    | tok_int=INTEGER              #tokIntExpr
    | tok_float=FLOAT              #tokFloatExpr
    | tok_nan='NaN'                #tokNanExpr
	;




condition
	: 'if' '(' expr ')' '{' proc_body '}'   #ifStmt
    | 'if' '(' expr ')' '{' proc_body '}' (NL)* 'else' '{' proc_body '}' #ifElseStmt
    ;

iterable
	: 'for' '(' expr 'in' expr ')' '{' proc_body '}'   #forStmt
    | 'while' '(' expr ')' '{' proc_body '}'  			#whileStmt
    ;

print_stmt: 'print' '(' expr ')' ';' ;

TYPE_NAME
	: 'int'
	| 'float'
	| 'bool'
	| 'string'
	| 'vector'
	| 'void'
	;

// Lexer
ID: [a-zA-Z][a-zA-Z0-9_]*;
STRING_LITERAL:  '"' (~["\\\r\n])* '"';
//VECTOR_LITERAL:  '[' (ID | INTEGER | FLOAT)? (',' (ID | INTEGER | FLOAT | VECTOR_LITERAL))* ']';
fragment DIGIT : [0-9] ;
INTEGER        : DIGIT+ ;
FLOAT          : (DIGIT+ '.' DIGIT* | '.' DIGIT+) ;
NUMBER         : (INTEGER | FLOAT) ;
BOOL: 'true' | 'false';


BLOCK_COMMENT: '/*'.*?'*/' -> skip;
LINE_COMMENT: '#' ~[\r\n]* -> skip;
NL: ('\r'? '\n' | '\r') ;  // Windows and UNIX newlines.
WHITESPACE: [ \t\r\n\u000C]+ -> skip ;  // Ignore whitespace.
