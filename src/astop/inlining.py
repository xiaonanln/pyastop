
import ast
from BaseASTOptimizer import BaseASTOptimizer

class InliningASTOptimizer(BaseASTOptimizer):

	def optimize(self, node):
		return node, False

