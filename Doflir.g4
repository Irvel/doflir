grammar Doflir;

program: (fun_def| statement | NL)* main_def (fun_def | NL)* EOF;

main_def: 'define main''{' proc_body '}' ;

proc_body: (NL*|statement) (NL|statement)*;

statement
	: assignment
	| condition
	| iterable
	| vec_filtering
	| fun_call_stmt
	| declaration_stmt
	| print_stmt
	| println_stmt
	| vec_declaration_stmt
	| flow_call
	;

assignment: (ID|vec_indexing) '=' expr ';' ;
declaration_stmt: declaration ';' ;
declaration: ID '->' TYPE_NAME ;

fun_def
	: 'define' ID '->' TYPE_NAME '(' parameters? ')' '{' proc_body '}'  // Function definition.
	;
parameters: (vec_declaration|declaration) (',' (vec_declaration|declaration))*;
fun_call_stmt: fun_call ';' ;
fun_call: ID '(' expr_list? ')' ;  // Function call.
flow_call: 'return' (expr)? ';' NL*;

expr_list: expr (',' expr)* ;
tok_list: token (',' token)* ;
filter_list: FILTER (',' FILTER)* ;

vec_declaration: declaration vec_list ;
vec_declaration_stmt: vec_declaration ';' ;
vec_list: '[' tok_list ']';

vec_init_list: '[' tok_list ']';
mat_init_list: '[' vec_init_list (',' vec_init_list)* ']';

vec_indexing: ID '[' expr_list ']' ;
vec_filtering: ID '{' filter_list '}' ;

expr
	: '('expr')'                   #parenExpr
	| vec_indexing                 #vecIdxExpr
	| vec_filtering                #vecFiltExpr
	| vec_init_list                #vecInitExpr
	| mat_init_list                #matInitExpr
	| fun_call                     #unExpr
	| <assoc=right> expr '^' expr  #powExpr     // Exponentiation.
	| '-' expr                     #negExpr     // Negative unary symbol.
	| '+' expr                     #posExpr     // Positive unary simbol.
    | 'not' expr                   #unExpr      // Negation.
	| expr  '@'  expr              #matMultExpr // Matrix multiplication.
	| expr '..'  expr              #dotExpr     // Dot product.
	| expr  '*'  expr              #multExpr    // Multiplication.
	| expr  '/'  expr              #divExpr     // Float division.
	| expr '//'  expr              #intDivExpr  // Integer division.
    | expr  '+'  expr              #addExpr     // Addition.
    | expr  '-'  expr              #subExpr     // Subtraction.
    | expr  '>'  expr              #gtExpr      // Logical greater than.
    | expr '>='  expr              #gtEqExpr    // Logical or equal greater than.
    | expr  '<'  expr              #ltExpr      // Logical less than.
    | expr '<='  expr              #ltEqExpr    // Logical less or equal than.
    | expr '=='  expr              #eqExpr      // Logical equal.
    | expr '!='  expr              #notEqExpr   // Logical not equal.
    | expr 'and' expr              #andExpr     // Logical and.
    | expr  'or' expr              #orExpr      // Logical or.
	| token                        #tokExpr
	| read_table	     	       #readTExpr
	| read_array                   #readAExpr
	| read_console                 #readCExpr
	;

token
	: ID                           #tokIdExpr
    | STRING_LITERAL               #tokStrExpr
    | BOOL                         #tokBoolExpr
    | INTEGER                      #tokIntExpr
    | FLOAT                        #tokFloatExpr
    | 'NaN'                        #tokNanExpr
	;

FILTER
	: 'f_sum'
	| 'f_mean'
	| 'f_var'
	| 'f_min'
	| 'f_max'
	| 'f_std'
	| 'f_normalize'
	| 'f_square'
	| 'f_cube'
	| 'f_strip'
	| 'f_lowercase'
	| 'f_uppercase'
	| 'f_sort'
	| 'f_reverse'
	;


condition
	: 'if' '(' expr ')' '{' proc_body '}'   #ifStmt
    | 'if' '(' expr ')' '{' proc_body '}' (NL)* 'else' '{' proc_body '}' #ifElseStmt
    ;

iterable
	: 'for' '(' expr 'in' expr ')' '{' proc_body '}'   #forStmt
    | 'while' '(' expr ')' '{' proc_body '}'  			#whileStmt
    ;

read_table: 'read_table' '->' TYPE_NAME '['token',' token ']' '(' expr ')' ;
read_array: 'read_array' '->' TYPE_NAME '['token']' '(' expr ')' ;
read_console: 'read_console' '->' TYPE_NAME ;
print_stmt: 'print' '(' expr_list ')' ';' ;
println_stmt: 'println' '(' expr_list ')' ';' ;


TYPE_NAME
	: 'int'
	| 'float'
	| 'bool'
	| 'string'
	| 'vector'
	| 'void'
	;

// Lexer
STRING_LITERAL:  '"' (~["\\\r\n])* '"';
//VECTOR_LITERAL:  '[' (ID | INTEGER | FLOAT)? (',' (ID | INTEGER | FLOAT | VECTOR_LITERAL))* ']';
fragment DIGIT : [0-9] ;
INTEGER        : DIGIT+ ;
FLOAT          : (DIGIT+ '.' DIGIT* | '.' DIGIT+) ;
NUMBER         : (INTEGER | FLOAT) ;
BOOL: 'true' | 'false';
ID: [a-zA-Z][a-zA-Z0-9_]*;


BLOCK_COMMENT: '/*'.*?'*/' -> skip;
LINE_COMMENT: '#' ~[\r\n]* -> skip;
NL: ('\r'? '\n' | '\r') ;  // Windows and UNIX newlines.
WHITESPACE: [ \t\r\n\u000C]+ -> skip ;  // Ignore whitespace.
