from SemanticCube import VarTypes
import collections

Params = collections.namedtuple("Params", "param_id param_type")


class VariablesTable(object):
    """docstring for VariablesTable"""
    def __init__(self):
        self._vars = {}
        self._curr_address = 0
        self.global_i = 5_000
        self.global_f = 8_000
        self.global_b = 9_000
        self.local_i = 11_000
        self.local_f = 13_000
        self.local_b = 15_000
        self.temp_i = 16_000
        self.temp_f = 18_000
        self.temp_b = 20_000
        self.const_i = 21_000
        self.const_f = 21_500
        self.const_b = 22_000
        self._temp_num = 1

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

    @property
    def variables(self):
        return [var for var in self._vars.values()]

    def _add_var(self, variable):
        self._vars[variable.name] = variable

    def declare_var(self, name, var_type, is_glob=False, is_tmp=False,
                    is_const=False):
        var = Variable(
            name=name,
            data_type=var_type,
            address=self.new_address(
                    v_type=var_type,
                    is_glob=is_glob,
                    is_tmp=is_tmp,
                    is_const=is_const
                )
            )
        self._add_var(variable=var)

    def declare_constant(self, value, const_type, is_glob=False, is_tmp=False,
                         is_const=False):
        const = Constant(
            value=value,
            data_type=const_type,
            address=self.new_address(v_type=const_type, is_glob=is_glob,
                                     is_tmp=is_tmp, is_const=is_const)
        )
        self._vars[const.name] = const
        return const

    def declare_or_search(self, value, const_type, is_glob=False, is_tmp=False,
                          is_const=True):
        if not self.exists(value):
            return self.declare_constant(
                value=value,
                const_type=const_type,
                is_glob=is_glob,
                is_tmp=is_tmp,
                is_const=is_const,
            )
        else:
            return self.search(value)

    def make_temp_name(self, data_type):
        if data_type is not VarTypes.INT:
            name = f"t{data_type.value[0]}_{self._temp_num}"
        else:
            name = f"t_{self._temp_num}"
        self._temp_num += 1
        return name

    def make_temp(self, temp_type, is_glob=False, is_tmp=True,
                  is_const=False):
        name = self.make_temp_name(temp_type)
        temp = Temporal(
            name=name,
            data_type=temp_type,
            address=self.new_address(
                    v_type=temp_type,
                    is_glob=is_glob,
                    is_tmp=is_tmp,
                    is_const=is_const
                )
            )
        return temp
        # self._add_var(variable=var)

    def new_address(self, v_type, is_glob=False, is_tmp=False, is_const=False):
        new_address = None
        if is_glob:
            if v_type == VarTypes.INT:
                new_address = self.global_i
                self.global_i += 1
            elif v_type == VarTypes.FLOAT:
                new_address = self.global_f
                self.global_f += 1
            elif v_type == VarTypes.BOOL:
                new_address = self.global_b
                self.global_b += 1
        elif is_tmp:
            if v_type == VarTypes.INT:
                new_address = self.temp_i
                self.temp_i += 1
            elif v_type == VarTypes.FLOAT:
                new_address = self.temp_f
                self.temp_f += 1
            elif v_type == VarTypes.BOOL:
                new_address = self.temp_b
                self.temp_b += 1
        elif is_const:
            if v_type == VarTypes.INT:
                new_address = self.const_i
                self.const_i += 1
            elif v_type == VarTypes.FLOAT:
                new_address = self.const_f
                self.const_f += 1
            elif v_type == VarTypes.BOOL:
                new_address = self.const_b
                self.const_b += 1
        else:
            if v_type == VarTypes.INT:
                new_address = self.local_i
                self.local_i += 1
            elif v_type == VarTypes.FLOAT:
                new_address = self.local_f
                self.local_f += 1
            elif v_type == VarTypes.BOOL:
                new_address = self.local_b
                self.local_b += 1
        return new_address


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

    @property
    def functions(self):
        return [fun for fun in self._fun_dir.values()]

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

    @property
    def num_params(self):
        if self.params:
            return len(self.params)
        else:
            return 0


class Variable(object):
    """docstring for Variable"""
    def __init__(self, name, data_type, address):
        self.name = name
        self.data_type = data_type
        self.address = address


class Constant(Variable):
    """docstring for Constant"""
    def __init__(self, value, data_type, address):
        super().__init__(str(value), data_type, address)
        self.value = value


class Temporal(Variable):
    """docstring for Temporal"""
    def __init__(self, name, data_type, address):
        super().__init__(name, data_type, address)