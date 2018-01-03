
import ast
from BaseASTOptimizer import BaseASTOptimizer
import astutils

unoptimizableValue = 'unoptimizableValue'

class _ReplaceVarASTOptimizer(BaseASTOptimizer):

	def __init__(self, vars):
		super(_ReplaceVarASTOptimizer, self).__init__()
		self.vars = vars
		self._visitingStmt = None

	def visit(self, node):
		# assert isinstance(node, ast.stmt)
		if self._visitingStmt is None:
			assert isinstance(node, ast.stmt)
			self._visitingStmt = node

		return super(_ReplaceVarASTOptimizer, self).visit(node)

	def optimize(self, node):
		# print '_ReplaceVarASTOptimizer.optimize', self.node2src(node), self.vars
		if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in self.vars:
			return self.vars[node.id], True
		else:
			return node, False

	def shouldOptimize(self, node):
		if isinstance(node, ast.stmt) and node is not self._visitingStmt: # do not optimize into inner stmt
			return False

		return True

class RedundantVarsEliminatingASTOptimizer(BaseASTOptimizer):

	RequireNameScope = True

	def optimize(self, node):
		# if isinstance(node, ast.Module):
		# 	print 'optimize module %s' % node

		if not isinstance(node, (ast.stmt, ast.mod)): # only optimize stmts
			return node, False

		stmt = node

		optimized = False
		# visit all stmt lists, which is body of functions, classes, etc ...
		if isinstance(stmt, (ast.Module, ast.Interactive, ast.Suite, ast.FunctionDef, ast.ClassDef, ast.For, ast.While, ast.If, ast.TryExcept, ast.TryFinally)):
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

		assigns = {}
		optimized = False
		newstmtlist = []

		for stmt in stmtlist:
			stmt, opted = self.optimizeStmt(stmt, assigns)
			if stmt is not None:
				newstmtlist.append(stmt)
			if opted:
				optimized = True

		if optimized:
			return newstmtlist, True
		else:
			return stmtlist, False

	def optimizeStmt(self, stmt, assigns):
		stmt, optimized = self._optimizeStmts(stmt, assigns)
		self.visitAssignsInStmt(stmt, assigns)
		return stmt, optimized

	def _optimizeStmts(self, stmt, assigns):
		rvopter = _ReplaceVarASTOptimizer(assigns)
		stmt = rvopter.visit(stmt)
		return stmt, rvopter.optimized

	def visitAssignsInStmt(self, stmt, assigns):
		if isinstance(stmt, ast.FunctionDef):
			self.onAssignName(stmt.name, unoptimizableValue, assigns)
		elif isinstance(stmt, ast.ClassDef):
			self.onAssignName(stmt.name, unoptimizableValue, assigns)
		elif isinstance(stmt, ast.Assign):
			for target in stmt.targets:
				self.visitAssignedNameInExpr(target, stmt.value, assigns)
		elif isinstance(stmt, ast.Delete):
			for expr in stmt.targets:
				self.visitAssignedNameInExpr(expr, unoptimizableValue, assigns)
		elif isinstance(stmt, ast.AugAssign):
			self.visitAssignedNameInExpr(stmt.target, ast.BinOp(stmt.target, stmt.op, stmt.value), assigns) # target op= value ==> target = target op value
		elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
			for alias in stmt.names:
				self.visitAssignedNamesInAlias(alias, unoptimizableValue, assigns)
		else:
			for substmt in astutils.substmts(stmt):
				self.visitAssignsInStmt(substmt, assigns)

	def visitAssignedNameInExpr(self, expr, value, assigns):
		if isinstance(expr, (ast.Attribute, ast.Subscript)):
			pass
		elif isinstance(expr, (ast.List, ast.Tuple)):
			if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
				for i, exp in enumerate(expr.elts):
					self.visitAssignedNameInExpr(exp, value.elts[i], assigns)
			else:
				for exp in expr.elts:
					self.visitAssignedNameInExpr(exp, unoptimizableValue, assigns)
		elif isinstance(expr, ast.Name):
			self.onAssignName(expr, value, assigns)
		else:
			assert False, ('should not assign', ast.dump(expr))

	def visitAssignedNamesInAlias(self, alias, value, assigns):
		assert isinstance(alias, ast.alias), repr(alias)
		if alias.asname:
			self.onAssignName(alias.asname, value, assigns)
		else:
			self.onAssignName(alias.name, value, assigns)

	def onAssignName(self, name, value, assigns):
		assert isinstance(name, (ast.Name, basestring)), `name`
		if isinstance(name, ast.Name):
			name = name.id

		if self.currentScope.isGlobalScope():
			# don't optimize in global scope for global names matter
			return

		if not self.currentScope.isLocalName(name):
			# can not optimize global variable
			return

		self.removeAffectedValuesByAssign( name, assigns )

		if value == unoptimizableValue:
			if name in assigns:
				del assigns[name]
		else:
			assert astutils.isexpr(value)
			if astutils.isSideEffectFreeExpr(value):
			# if isinstance(value, (ast.Name, ast.Num, ast.Str)):
				assigns[name] = value
				# print self, 'assign', name, value, assigns

	def removeAffectedValuesByAssign(self, name, assigns):
		for aname, aval in assigns.items():
			if astutils.isNameReferenced(name, aval):
				del assigns[aname]

