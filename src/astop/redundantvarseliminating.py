
import ast
from BaseASTOptimizer import BaseASTOptimizer

class RedundantVarsEliminatingASTOptimizer(BaseASTOptimizer):

	RequireNameScope = True

	def optimize(self, node):
		if not isinstance(node, ast.FunctionDef):
			return node, False

		node.body, optimized = self.optimizeStmtList(node.body, node.scope)
		return node, optimized

	def optimizeStmtList(self, stmtlist, scope):
		for stmt in stmtlist:




		pass



