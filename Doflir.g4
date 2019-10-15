grammar Doflir;

program: (fun_def | statement | NL)* EOF;

statement: (assignment | condition | iterable | vec_filtering | fun_call)';';

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
	: '('expr')'
	| vec_indexing
	| vec_filtering
	| fun_call
	| vec_list
	| <assoc=right> expr '^' expr  // Exponentiation.
	| ('-'|'+') expr  // Conversion to negative/positive.
	| expr ('@') expr  // Matrix multiplication.
	| expr ('..') expr  // Dot product.
	| expr ('*'|'/'|'//') expr  // Multiplication, division and integer division.
    | expr ('+'|'-') expr  // Addition, subtraction.
    | expr ('>'|'>='|'<'|'<='|'=='|'!=') expr  // Relational operators.
    | 'not' expr  // Negation.
    | expr ('and') expr  // Logical and.
    | expr ('or') expr  // Logical or.
	| ID
    | STRING_LITERAL
    | BOOL
    | INTEGER
    | FLOAT
    | 'NaN'
	;


function_call: (ID'('expr(','expr)*')') ;  // Function call.

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
FLOAT          : ('-'?)(DIGIT+ '.' DIGIT* | '.' DIGIT+);
BOOL: 'true' | 'false';


BLOCK_COMMENT: '/*'.*?'*/' -> skip;
LINE_COMMENT: '//' ~[\r\n]* -> skip;
NL: ('\r'? '\n' | '\r') ;  // Windows and UNIX newlines.
WHITESPACE: [ \t\r\n\u000C]+ -> skip ;  // Ignore whitespace.
