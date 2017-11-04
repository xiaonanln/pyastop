
BUILTIN_NAMES = list(__builtins__.keys())

CONST_TO_CONST_BUILTIN_FUNCS = set([
	'abs', 'all', 'any', 'bin', 'bool', 'callable', 'chr', 'cmp', 'filter', 'dict', 'divmod', 'enumerate', 'eval', 'float',
	'hasattr', 'hash', 'hex', 'int', 'isinstance', 'issubclass', 'iter', 'len', 'list', 'long', 'map', 'max', 'set',
	'min', 'oct', 'ord', 'pow', 'reversed', 'round', 'slice', 'sorted', 'str', 'sum', 'tuple', 'unichr', 'unicode', 'zip', 'range',
	'xrange', 'frozenset',
])

CONST_BUILTIN_NAMES = ('True', 'False', 'None')

for name in CONST_TO_CONST_BUILTIN_FUNCS:
	assert name in BUILTIN_NAMES

for name in CONST_BUILTIN_NAMES:
	assert name, CONST_BUILTIN_NAMES
