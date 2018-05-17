
import ast
from BaseASTOptimizer import BaseASTOptimizer

class BaseSkipInnerASTOptimizer(BaseASTOptimizer):

	"""Optimize all nodes in the function, but no inner functions"""

	def __init__(self, ):
		super(BaseSkipInnerASTOptimizer, self).__init__()
		self.outmostNode = None

	def visit(self, node):
		# assert isinstance(node, ast.stmt)
		if self.outmostNode is None:
			self.outmostNode = node

		if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node is not self.outmostNode:
			return node

		return super(BaseSkipInnerASTOptimizer, self).visit(node)
