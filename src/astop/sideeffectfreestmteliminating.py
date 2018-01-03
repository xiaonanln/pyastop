
import ast
import astutils
from BaseASTOptimizer import BaseASTOptimizer

class SideEffectFreeStmtEliminatingASTOptimizer(BaseASTOptimizer):

	RequireNameScope = True

	def optimize(self, node):
		if not isinstance(node, ast.stmt): # only optimize stmt
			return node, False

		if isinstance(node, ast.Expr): # only optimize Expr stmt
			if astutils.isSideEffectFreeExpr(node.value):
				return [], True

		elif isinstance(node, ast.Assign):
			allTargetsEffectFree = True
			for target in node.targets:
				if not isinstance(target, ast.Name):
					allTargetsEffectFree = False
					break

				if self.currentScope.isGlobalName(target.id):
					allTargetsEffectFree = False
					break

				if astutils.isNameReferenced(target.id, self.currentScope.node):
					allTargetsEffectFree = False
					break

			if allTargetsEffectFree:
				return [], True

		elif isinstance(node, ast.If):
			if not node.body and not node.orelse and astutils.isSideEffectFreeExpr(node.test):
				return [], True

		return node, False


