class VariablesTable(object):
    """docstring for VariablesTable"""
    def __init__(self):
        self._symbols = {}

    def search(self, name):
        if name in self._symbols:
            return self._symbols[name]
        else:
            return None

    def add_symbol(self, symbol):
        self._symbols[symbol.name] = symbol


class Function(object):
    """docstring for Function"""
    def __init__(self, name, ret_type, ret_value):
        self.name = name
        self.ret_type = ret_type
        self.ret_value = ret_value


class Variable(object):
    """docstring for Variable"""
    def __init__(self, name, data_type, value, scope):
        self.name = name
        self.data_type = data_type
        self.value = value
        self.scope = scope
