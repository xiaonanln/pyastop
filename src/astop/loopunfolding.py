import ast
import sys
import astutils
from collections import Counter
from BaseASTOptimizer import BaseASTOptimizer


class LoopUnfoldingASTOptimizer(BaseASTOptimizer):

	def __init__(self):
		super(LoopUnfoldingASTOptimizer, self).__init__()

	def optimize(self, node):
		if not isinstance(node, ast.For):
			return node, False

		optNode = self.optimizeFor(node)
		if not optNode:
			return node, False

		return optNode, True

	def optimizeFor(self, node):
		# ast.For
		# if node.orelse is not None:
		if node.orelse: # if For has orelse, we can not optimize it
			return

		if self.containsStmt(lambda x: self.isBreakStmt(x) or self.isContinueStmt(x), node.body ):
			# can not optimize if For body contains continue or break
			return

		expandIter, ok = self.expandIterExpr(node.iter)

		if not ok:
			return

		print [ast.dump(it) for it in expandIter]
		if len(expandIter) > 10:
			return

		newBody = []
		for iterVal in expandIter:
			# print >>sys.stderr, 'assigning', iterVal
			assign = self.makeAssignStmt(node.target, iterVal)
			newBody.append(assign)
			newBody += node.body

		return newBody

	def expandIterExpr(self, iter):
		print 'expandIterExpr', ast.dump(iter)
		# self.dump(iter)
		if isinstance(iter, ast.Call):
			# self.dump(iter.func)
			# if self.isNameEquals(iter.func, 'range') or self.isNameEquals(iter.func, 'xrange'):
			# 	return 'abc'
			return None, False

		elif isinstance(iter, (ast.List, ast.Tuple, ast.Set)):
			return iter.elts, True
		elif isinstance(iter, ast.Dict):
			return iter.keys, True

		return None, False

	def visit_stmt(self, stmt):
		print >>sys.stderr, 'current stmt:', stmt
