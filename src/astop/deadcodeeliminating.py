
import ast
from BaseASTOptimizer import BaseASTOptimizer

class DeadCodeEliminatingASTOptimizer(BaseASTOptimizer):

	def optimize(self, node):
		if not isinstance(node, ast.Call):
			return node, False

		# Call(expr func, expr * args, keyword * keywords, expr? starargs, expr? kwargs)
		

		return node, False

