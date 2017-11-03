
import ast
from BaseASTOptimizer import BaseASTOptimizer

class FuncArgsUnfoldingASTOptimizer(BaseASTOptimizer):

	RequireTypeInference = True

	def optimize(self, node):
		if not isinstance(node, ast.Call):
			return node, False

		# Call(expr func, expr * args, keyword * keywords, expr? starargs, expr? kwargs)

		return node, False

	def tryOptimizeCall(self, call):
		assert isinstance(call, ast.Call)
		pass
