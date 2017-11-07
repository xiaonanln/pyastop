
import ast
from BaseASTOptimizer import BaseASTOptimizer
import namescope

class FuncArgsUnfoldingASTOptimizer(BaseASTOptimizer):

	RequireTypeInference = True

	def optimize(self, node):
		if not isinstance(node, ast.Call):
			return node, False

		# Call(expr func, expr * args, keyword * keywords, expr? starargs, expr? kwargs)
		return self.tryOptimizeCall(node)

	def tryOptimizeCall(self, call):
		assert isinstance(call, ast.Call)

		# call.func expr
		# Call(expr func, expr * args, keyword * keywords, expr? starargs, expr? kwargs)

		if not call.keywords and not call.starargs and not call.kwargs:
			# no argument need to expand
			return call, False

		func, bounded = self.tryDetermineFunction(call.func)
		print 'FuncArgsUnfoldingASTOptimizer.tryOptimizeCall: func of %s is %s, bounded %s' % (ast.dump(call.func), func, bounded)
		if not func:
			return call, False

		return call, False

	def tryDetermineFunction(self, func):
		pvs = self.currentScope.getPotentialValuesOfExpr(func)
		if isinstance(pvs, namescope.FunctionValues):
			funcdef = pvs.getSingleValue()
			if funcdef:
				return funcdef, isinstance(pvs, namescope.BoundedMethodValues)

		return None, False

