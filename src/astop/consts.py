
BUILTIN_NAMES = list(__builtins__.keys())

CONST_TO_CONST_BUILTIN_FUNCS = set([
	'abs', 'all', 'any', 'bin', 'bool', 'callable', 'chr', 'cmp', 'filter', 'dict', 'divmod', 'enumerate', 'eval', 'float',
	'frozenset', 'hasattr', 'hash', 'hex', 'int', 'isinstance', 'issubclass', 'iter', 'len', 'list', 'long', 'map', 'max',
	'min', 'oct', 'ord', 'pow', 'reversed', 'round', 'set', 'slice', 'sorted', 'str', 'sum', 'tuple', 'unichr', 'unicode', 'zip', 'range',
])