grammar Doflir;

program: (fun_def | statement | NL)* EOF;

statement: (assignment | condition | iterable | vec_filtering | fun_call)';';

declaration: ID '->' TYPE_NAME ;
assignment: (ID|vec_indexing) '=' expr;
vec_indexing: ID '[' expr (',' expr)* ']';
vec_filtering: (ID|vec_indexing) '{' expr (',' expr)* '}';
fun_call: ID'('expr(','expr)*')';  // Function call.

fun_def
	: 'define' ID '->' TYPE_NAME '(' parameters? ')' '{' statement* flow_call '}'  // Function definition.
	;
parameters: (ID | ID '=' expr) (',' parameters)*;

vec_list: '['(expr? | (expr (',' expr)*))']';

expr
	: '('expr')' #parenExpr
	| vec_indexing #unExpr
	| vec_filtering #unExpr
	| fun_call #unExpr
	| vec_list #unExpr
	| <assoc=right> left=expr '^' right=expr  #powExpr  // Exponentiation.
	| ('-'|'+') expr                    #unExpr     // Conversion to negative/positive.
    | 'not' expr                        #unExpr     // Negation.
	| left=expr '@'  right=expr         #matExpr    // Matrix multiplication.
	| left=expr '..' right=expr         #dotExpr    // Dot product.
	| left=expr '*'  right=expr         #multExpr   // Multiplication.
	| left=expr '/'  right=expr         #divExpr    // Float division.
	| left=expr '//' right=expr         #intDivExpr // Integer division.
    | left=expr '+'  right=expr         #addExpr    // Addition.
    | left=expr '-'  right=expr         #subExpr    // Subtraction.
    | left=expr ('>'|'>='|'<'|'<='|'=='|'!=') right=expr  #relExpr // Relational operators.
    | left=expr ('and') right=expr  #andExpr // Logical and.
    | left=expr ('or') right=expr  #orExpr // Logical or.
	| tok_id=ID              #tokIdExpr
    | tok_str=STRING_LITERAL #tokStrExpr
    | tok_bool=BOOL          #tokBoolExpr
    | tok_int=INTEGER        #tokIntExpr
    | tok_float=FLOAT        #tokFloatExpr
    | tok_nan='NaN'          #tokNanExpr
	;



flow_call: 'return' (expr)? ';';

condition
	: 'if' '(' expr ')' '{' statement '}'
    | 'if' '(' expr ')' '{' statement '}' 'else' '{' statement '}'
    ;

iterable
	: 'for' '(' expr 'in' expr ')' '{' statement '}'
    | 'while' '(' expr ')' '{' statement '}'
    ;

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
INTEGER        : ('-'?)DIGIT+ ;
FLOAT          : ('-'?)(DIGIT+ '.' DIGIT* | '.' DIGIT+) ;
NUMBER         : (INTEGER | FLOAT) ;
BOOL: 'true' | 'false';


BLOCK_COMMENT: '/*'.*?'*/' -> skip;
LINE_COMMENT: '//' ~[\r\n]* -> skip;
NL: ('\r'? '\n' | '\r') ;  // Windows and UNIX newlines.
WHITESPACE: [ \t\r\n\u000C]+ -> skip ;  // Ignore whitespace.
