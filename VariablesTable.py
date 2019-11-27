from SemanticCube import VarTypes


class VariablesTable(object):
    """Keep track of variables information and their memory."""
    def __init__(self):
        self._vars = {}
        self._curr_address = 0
        self.global_i = 4_000
        self.global_f = 6_000
        self.global_b = 8_000
        self.global_s = 9_000
        self.global_v = 10_000
        self.local_i = 11_000
        self.local_f = 13_000
        self.local_b = 15_000
        self.local_s = 17_000
        self.local_v = 18_000
        self.temp_i = 19_000
        self.temp_f = 21_000
        self.temp_b = 22_000
        self.temp_s = 23_000
        self.temp_v = 24_000
        self.const_i = 25_000
        self.const_f = 25_500
        self.const_b = 26_000
        self.const_s = 27_000
        self.const_v = 28_000
        self._temp_num = 1

    def search(self, var_name):
        """Look for a variable within the ones we know of already."""
        if var_name in self._vars:
            return self._vars[var_name]
        else:
            return None

    def exists(self, var_name):
        """Return True if the var_name exists in the table."""
        if self.search(var_name):
            return True
        else:
            return False

    @property
    def variables(self):
        """Shorthand for accessing the list of all variables in the table."""
        return [var for var in self._vars.values()]

    def _add_var(self, variable):
        """Add a variable to the table."""
        self._vars[variable.name] = variable

    def declare_var(self, name, var_type, is_glob=False, is_tmp=False,
                    is_const=False, is_initialized=False):
        """Outside method for declaring a variable in this table."""
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
        var.is_initialized = is_initialized
        self._add_var(variable=var)

    def declare_vector(self, name, vec_type, vec_dims, is_glob=False,
                       is_tmp=False, is_const=False):
        """Outside method for declaring a vector in this table."""
        vec = Variable(
            name=name,
            data_type=vec_type,
            address=self.new_address(
                    v_type=vec_type,
                    is_glob=is_glob,
                    is_tmp=is_tmp,
                    is_const=is_const),
            vec_dims=vec_dims,
        )
        self._add_var(variable=vec)
        return vec

    def declare_constant(self, value, const_type, is_glob=False, is_tmp=False,
                         is_const=False):
        """Outside method for declaring a constant in this table."""
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
        """Shorthand method for either retrieving or declaring a variable."""
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
        """Generate unique incremental names for temporary variables."""
        if data_type is not VarTypes.INT:
            name = f"t{data_type.value[0]}_{self._temp_num}"
        else:
            name = f"t_{self._temp_num}"
        self._temp_num += 1
        return name

    def make_temp(self, temp_type, is_glob=False, is_tmp=True,
                  is_const=False, vec_dims=None):
        """Outside method for making a temporal variable."""
        name = self.make_temp_name(temp_type)
        temp = Temporal(
            name=name,
            data_type=temp_type,
            address=self.new_address(
                    v_type=temp_type,
                    is_glob=is_glob,
                    is_tmp=is_tmp,
                    is_const=is_const
                ),
            vec_dims=vec_dims,
            )
        return temp

    def make_const(self, value, const_type, vec_dims=None):
        """Outside method for making a constant."""
        const = Constant(
            value=value,
            data_type=const_type,
            address=self.new_address(v_type=VarTypes.INT, is_const=True)
        )
        return const

    def new_address(self, v_type, is_glob=False, is_tmp=False, is_const=False):
        """Return a new address of the requested type."""
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
            elif v_type == VarTypes.STRING:
                new_address = self.global_s
                self.global_s += 1
            elif v_type == VarTypes.VOID:
                new_address = self.global_v
                self.global_v += 1
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
            elif v_type == VarTypes.STRING:
                new_address = self.temp_s
                self.temp_s += 1
            elif v_type == VarTypes.VOID:
                new_address = self.temp_v
                self.temp_v += 1
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
            elif v_type == VarTypes.STRING:
                new_address = self.const_s
                self.const_s += 1
            elif v_type == VarTypes.VOID:
                new_address = self.const_v
                self.const_v += 1
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
            elif v_type == VarTypes.STRING:
                new_address = self.local_s
                self.local_s += 1
            elif v_type == VarTypes.VOID:
                new_address = self.local_v
                self.local_v += 1
        return new_address


class FunDir(object):
    """Keep track of information required to instantiate Functions."""
    def __init__(self):
        super(FunDir, self).__init__()
        self._fun_dir = {}

    def search(self, fun_name):
        """Look for a function within the ones we know of already."""
        if fun_name in self._fun_dir:
            return self._fun_dir[fun_name]
        else:
            return None

    def exists(self, fun_name):
        """Return True if the fun_name exists in the directory."""
        if self.search(fun_name):
            return True
        else:
            return False

    @property
    def functions(self):
        """Return a listing of the functions in this directory."""
        return [fun for fun in self._fun_dir.values()]

    def _add_fun(self, function):
        """Register a new function in this directory."""
        self._fun_dir[function.name] = function

    def define_fun(self, name, ret_type, params, address, quad_idx):
        """Outside method for registering a function in this directory."""
        fun = Function(
            name=name,
            ret_type=ret_type,
            params=params,
            address=address,
            quad_idx=quad_idx,
        )
        self._add_fun(function=fun)


class Function(object):
    """Keep track of semantically important details in a function."""
    def __init__(self, name, ret_type, params, address, quad_idx):
        self.name = name
        self.ret_type = ret_type
        self.params = params
        self.address = address
        self.quad_idx = quad_idx
        # Functions are never vectors. We keep this here because
        # it allows us to do some duck typing.
        self.vec_dims = None

    @property
    def num_params(self):
        """Get the defined number of params from this function."""
        if self.params:
            return len(self.params)
        else:
            return 0

    @property
    def value(self):
        """Accesor for the function name and quad where it was defined."""
        return f"{self.name}({self.quad_idx})"


class Params(object):
    """Keep track of semantically important details from a parameter."""
    def __init__(self, param_id, param_type, address):
        self.param_id = param_id
        self.param_type = param_type
        self.address = address

    def __repr__(self):
        param_repr = (
            f"{self.param_id:>7}, {self.param_type.value:>6}, "
            f"{self.address:>9}, "
        )
        return param_repr


class VecIdx(object):
    """Keep track of semantically important details from a vector index."""
    def __init__(self, vec_id, idx, address, data_type):
        self.vec_id = vec_id
        self.idx = idx
        self.address = address
        self.data_type = data_type
        # Vectors are init by default to 0, so one can retrieve with
        # index safely.
        self.is_initialized = True
        self.vec_dims = None      # A vector index is not a vector.

    @property
    def name(self):
        """Shorthand for value to allow duck typing."""
        return self.value

    @property
    def value(self):
        """Accesor for the VecIdx shape."""
        short_idx = tuple([i.value for i in self.idx])
        return f"{self.vec_id}{short_idx}"


class Variable(object):
    """Keep track of semantically important details of a variable."""
    def __init__(self, name, data_type, address, vec_dims=None):
        self.name = name
        self.data_type = data_type
        self.address = address
        self.vec_dims = vec_dims
        self.is_initialized = False

    @property
    def value(self):
        """Accesor for the variable name."""
        return self.name

    def __repr__(self):
        """Return a human friendly way of reading its contents."""
        var_repr = (
            f"{self.name:>7}, {self.data_type.value:>6}, "
            f"{self.address:>9}, "
        )
        if self.vec_dims:
            var_repr += f"{str(self.vec_dims):>9}"
        return var_repr


class Constant(Variable):
    """Keep track of semantically important details of a constant."""
    def __init__(self, value, data_type, address):
        super().__init__(str(value), data_type, address)
        self._value = value
        self.is_initialized = True

    @property
    def value(self):
        """Accesor for the value this constant holds."""
        return self._value

    def __repr__(self):
        """Human friendly version of its contents."""
        return str(self._value)


class Temporal(Variable):
    """Keep track of semantically important details of a temporal."""
    def __init__(self, name, data_type, address, vec_dims=None):
        super().__init__(name, data_type, address, vec_dims)
        self.is_initialized = True


class QuadJump(object):
    """Keep track of semantically important details of a quad jump."""
    def __init__(self, quad_idx):
        self.quad_idx = quad_idx
        self.vec_dims = None

    @property
    def value(self):
        """Accesor for the quad index that it points to."""
        return self.quad_idx


class Param(object):
    """Keep track of semantically important details of a argument passing."""
    def __init__(self, param_num):
        self.param_num = param_num
        self.vec_dims = None

    @property
    def value(self):
        """Accesor for the param num."""
        return self.param_num
