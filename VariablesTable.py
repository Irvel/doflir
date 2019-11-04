class VariablesTable(object):
    """docstring for VariablesTable"""
    def __init__(self):
        self._vars = {}
        self._curr_address = 0

    def search(self, address):
        if address in self._vars:
            return self._vars[address]
        else:
            return None

    def add_var(self, variable):
        self._vars[variable.address] = variable

    def new_address(self):
        self._curr_address += 1
        return self._curr_address


class Function(object):
    """docstring for Function"""
    def __init__(self, name, ret_type, address):
        self.name = name
        self.ret_type = ret_type
        # self.ret_value = ret_value
        self.address = address


class Variable(object):
    """docstring for Variable"""
    def __init__(self, name, data_type, address):
        self.name = name
        self.data_type = data_type
        self.address = address
