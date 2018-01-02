
import ast
import astutils
from BaseASTOptimizer import BaseASTOptimizer

class SideAffectFreeExprEliminatingASTOptimizer(BaseASTOptimizer):

	def optimize(self, node):
		if not isinstance(node, ast.stmt): # only optimize stmt
			return node, False

		if not isinstance(node, ast.Expr): # only optimize Expr stmt
			return node, False

		if astutils.isSideEffectFreeExpr(node.value):
			return [], True
		else:
			return node, False
