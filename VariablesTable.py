class VariablesTable(object):
    """docstring for VariablesTable"""
    def __init__(self):
        self._vars = {}
        self._curr_address = 0

    def search(self, var_name):
        if var_name in self._vars:
            return self._vars[var_name]
        else:
            return None

    def exists(self, var_name):
        if self.search(var_name):
            return True
        else:
            return False

    def _add_var(self, variable):
        self._vars[variable.name] = variable

    def declare_var(self, name, var_type):
        var = Variable(name=name, data_type=var_type, address=self.new_address)
        self._add_var(variable=var)

    def declare_constant(self, name, var_type):
        # self.add_var
        pass

    def new_address(self):
        self._curr_address += 1
        return self._curr_address


class FunDir(object):
    """docstring for FunDir"""
    def __init__(self):
        super(FunDir, self).__init__()
        self._fun_dir = {}

    def search(self, fun_name):
        if fun_name in self._fun_dir:
            return self._fun_dir[fun_name]
        else:
            return None

    def exists(self, fun_name):
        if self.search(fun_name):
            return True
        else:
            return False

    def _add_fun(self, function):
        self._fun_dir[function.name] = function

    def define_fun(self, name, ret_type, params, address):
        fun = Function(
            name=name,
            ret_type=ret_type,
            params=params,
            address=address
        )
        self._add_fun(function=fun)


class Function(object):
    """docstring for Function"""
    def __init__(self, name, ret_type, params, address):
        self.name = name
        self.ret_type = ret_type
        self.params = params
        self.address = address
        self.params = []


class Variable(object):
    """docstring for Variable"""
    def __init__(self, name, data_type, address):
        self.name = name
        self.data_type = data_type
        self.address = address


class Constant(Variable):
    """docstring for Constant"""
    def __init__(self, name, data_type, address, value):
        super().__init__(name, data_type, address)
        self.value = value
