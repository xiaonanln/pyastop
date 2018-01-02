
import ast
from BaseASTOptimizer import BaseASTOptimizer
import astutils

class RedundantVarsEliminatingASTOptimizer(BaseASTOptimizer):

	RequireNameScope = True

	def optimize(self, stmt):
		if not isinstance(stmt, ast.stmt): # only optimize stmts
			return stmt, False

		optimized = False
		# visit all stmt lists, which is body of functions, classes, etc ...
		if isinstance(stmt, (ast.Module, ast.Interactive, ast.Suite, ast.ClassDef, ast.For, ast.While, ast.If, ast.TryExcept, ast.TryFinally)):
			stmts, opted = self.optimizeStmtList(stmt.body)
			if opted:
				stmt.body = stmts
				optimized = True

		if isinstance(stmt, ast.TryExcept):
			for handler in stmt.handlers:
				# ExceptHandler(expr? type, expr? name, stmt* body)
				stmts, opted = self.optimizeStmtList(handler.body)
				if opted:
					handler.body = stmts
					optimized = True

		if isinstance(stmt, (ast.For, ast.While, ast.If, ast.TryExcept)):
			stmts, opted = self.optimizeStmtList(stmt.orelse)
			if opted:
				stmt.orelse = stmts
				optimized = True

		if isinstance(stmt, ast.TryFinally):
			stmts, opted = self.optimizeStmtList(stmt.finalbody)
			if opted:
				stmt.finalbody = stmts
				optimized = True

		return stmt, optimized

	def optimizeStmtList(self, stmtlist):
		for stmt in stmtlist:
			pass
		pass
