
import ast
from BaseASTOptimizer import BaseASTOptimizer

class DeadCodeEliminatingASTOptimizer(BaseASTOptimizer):

	def optimize(self, node):
		if 'body' not in node._fields and 'orelse' not in node._fields and 'finalybody' not in node._fields:
			return node, False

		optimized1, optimized2, optimized3 = False, False, False
		if 'body' in node._fields and isinstance(node.body, list) and node.body and isinstance(node.body[0], ast.stmt):
			# handle stmt* body
			node.body, optimized1 = self.optimizeStmtList(node.body)

		if 'orelse' in node._fields and isinstance(node.orelse, list) and node.orelse and isinstance(node.orelse[0], ast.stmt):
			# handle stmt* orelse
			node.orelse, optimized2 = self.optimizeStmtList(node.orelse)

		if 'finalbody' in node._fields and isinstance(node.finalbody, list) and node.finalbody and isinstance(node.finalbody[0], ast.stmt):
			# handle stmt* finalbody
			node.finalbody, optimized3 = self.optimizeStmtList(node.finalbody)

		return node, (optimized1 or optimized2 or optimized3)

	def optimizeStmtList(self, stmtlist):
		for i, stmt in enumerate(stmtlist):
			if isinstance(stmt, (ast.Return, ast.Break, ast.Continue)) and i != len(stmtlist)-1:
				return stmtlist[:i+1], True

		return stmtlist, False

