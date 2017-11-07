
import ast
import astutils
import namescope
from BaseASTOptimizer import BaseASTOptimizer

class InliningASTOptimizer(BaseASTOptimizer):

	RequireTypeInference = True

	def optimize(self, node):
		if not isinstance(node, ast.Call):
			return node, False

		# Call(expr func, expr * args, keyword * keywords, expr? starargs, expr? kwargs)
		return self.tryOptimizeCall(node)

	def tryOptimizeCall(self, call):
		assert isinstance(call, ast.Call)
		# Call(expr func, expr * args, keyword * keywords, expr? starargs, expr? kwargs)

		func, bounded = self.tryDetermineFunction(call.func)
		if not func:
			return call, False


		return call, False

	#
	# 	assert isinstance(func, ast.FunctionDef)
	# 	# 	arguments = (expr* args, identifier? vararg, identifier? kwarg, expr* defaults)
	# 	if func.args.vararg or func.args.kwarg:
	# 		return call, False # if function def has *arg or **kwargs, do not optimize
	#
	# 	# print 'FuncArgsUnfoldingASTOptimizer.tryOptimizeCall: func of %s is %s, bounded %s' % (ast.dump(call.func), func, bounded)
	# 	argstart = 1 if bounded else 0
	# 	argname2index = {}
	# 	for i, arg in enumerate(func.args.args):
	# 		if i < argstart: continue
	# 		if isinstance(arg, ast.Name):
	# 			argname2index[arg.id] = i - argstart
	#
	# 	callargs = list(call.args)
	# 	if call.starargs:
	# 		if not isinstance(call.starargs, (ast.List, ast.Tuple, ast.Set) ):
	# 			return call, False
	#
	# 		callargs = callargs + call.starargs.elts # call.starargs must be list, tuple, ...
	#
	# 	keys = []
	# 	values = []
	# 	# keyword = (identifier arg, expr value)
	# 	if call.keywords:
	# 		keys += [kw.arg for kw in call.keywords]
	# 		values += [kw.value for kw in call.keywords]
	#
	# 	if call.kwargs:
	# 		if not isinstance(call.kwargs, ast.Dict):
	# 			return call, False
	#
	# 		for k in call.kwargs.keys:
	# 			if not isinstance(k, ast.Name):
	# 				return call, False
	#
	# 		keys += [k.id for k in call.kwargs.keys]
	# 		values += call.kwargs.values
	#
	# 	assert len(keys) == len(values)
	# 	for key, val in zip(keys, values):
	# 		assert key in argname2index, 'argument %s is not valid' % key
	# 		argindex = argname2index[key]
	# 		while argindex >= len(callargs):
	# 			callargs.append(None)
	#
	# 		assert callargs[argindex] is None, 'duplicate argument %s' % key
	# 		callargs[argindex] = val
	#
	# 	for i, arg in enumerate(callargs):
	# 		if arg is None:
	# 			defaultindex = argstart + i - (len(func.args.args) - len(func.args.defaults))
	# 			assert defaultindex >= 0, 'default index is %d while optimizing %s' % (defaultindex, self.node2src(call))
	# 			defaultval = func.args.defaults[defaultindex]
	# 			if not self.isImmutableDefaultArg(defaultval):
	# 				return call, False
	#
	# 			callargs[i] = astutils.copy_node(defaultval)
	#
	# 	newcall = ast.Call(call.func, callargs, [], None, None)
	# 	newcall = self.copyLocation(newcall, call)
	# 	# print 'Old call: %s' % self.node2src(call)
	# 	# print 'New call: %s' % self.node2src(newcall)
	# 	return newcall, True
	# 	# return call, False
	#
	def tryDetermineFunction(self, func):
		pvs = self.currentScope.getPotentialValuesOfExpr(func)
		if isinstance(pvs, namescope.FunctionValues):
			funcdef = pvs.getSingleValue()
			if funcdef:
				return funcdef, isinstance(pvs, namescope.BoundedMethodValues)

		return None, False
	#
	# def isImmutableDefaultArg(self, expr):
	# 	if isinstance(expr, (ast.Num, ast.Str, ast.Tuple)):
	# 		return True
	# 	elif isinstance(expr, ast.Name):
	# 		return expr.id in consts.CONST_BUILTIN_NAMES
	# 	else:
	# 		return False


