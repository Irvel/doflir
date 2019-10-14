from antlr4.error.ErrorListener import ErrorListener


class DoflirErrorListener(ErrorListener):

    def __init__(self, output):
        self.output = output
        self._symbol = ""

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.output.write(f"Syntax error: {msg}")
        self._symbol = offendingSymbol.text

    @property
    def symbol(self):
        return self._symbol
