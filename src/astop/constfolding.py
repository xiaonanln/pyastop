
import ast
import consts
import astutils
from BaseASTOptimizer import BaseASTOptimizer

class ConstFoldingASTOptimizer(BaseASTOptimizer):
	RequireNameScope = True
	UNFOLDABLE_BUILTIN_FUNCS = ('enumerate', 'iter', 'reversed', 'slice', 'xrange')

	def __init__(self):
		super(ConstFoldingASTOptimizer, self).__init__()

	def optimize(self, node):
		# print 'optimize', ast.dump(node)
		if not astutils.isexpr(node):
			return node, False

		if self.isConstFoldableExpr(node) and self.currentScope.isConstantExpr(node):
			if isinstance(node, ast.Call) and node.func.id in ConstFoldingASTOptimizer.UNFOLDABLE_BUILTIN_FUNCS:
				return node, False # these functions can not be unfolded, because we can not represent them using consts

			node = self.evalConstExpr(node)
			return node, True

		return node, False

	def isConstFoldableExpr(self, node):
			return isinstance(node, (ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.IfExp, ast.Compare, ast.Call))
