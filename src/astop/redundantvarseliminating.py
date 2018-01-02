
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



		self.visitAssignsInStmt(stmt, assigns)

	def visitAssignsInStmt(self, stmt, assigns):
		if isinstance(stmt, ast.FunctionDef):
			self.onAssignNonSideEffect(stmt.name)
		elif isinstance(stmt, ast.ClassDef):
			self.onAssignNonSideEffect(stmt.name)
		elif isinstance(stmt, ast.Assign):
			for target in stmt.targets:
				self.visitAssignedNameInExpr(target, stmt.value)
		elif isinstance(stmt, ast.Delete):
			for expr in stmt.targets:
				self.visitAssignedNameInExpr(expr, unresolvedName)
		elif isinstance(stmt, ast.AugAssign):
			self.visitAssignedNameInExpr(stmt.target, ast.BinOp(stmt.target, stmt.op, stmt.value)) # target op= value ==> target = target op value
		elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
			for alias in stmt.names:
				self.visitAssignedNamesInAlias(alias, anyValue)
		else:
			for substmt in astutils.substmts(stmt):
				self.visitStmt(substmt, res)

	def visitAssignedNameInExpr(self, expr, value):
		if isinstance(expr, (ast.Attribute, ast.Subscript)):
			pass
		elif isinstance(expr, (ast.List, ast.Tuple)):
			if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
				for i, exp in enumerate(expr.elts):
					self.visitAssignedNameInExpr(exp, value.elts[i])
			else:
				for exp in expr.elts:
					self.visitAssignedNameInExpr(exp, anyValue)
		elif isinstance(expr, ast.Name):
			if not isinstance(value, PotentialValues):
				pv = self.expr2pvs(value)
				# print 'potential value of %s ==> %s' % (ast.dump(value), pv)
			else:
				pv = value # if value is PotentialValues, just keep it
			self.onAssignName(expr, pv)
		else:
			assert False, ('should not assign', ast.dump(expr))

	def onAssignNonSideEffectFree(self, name, assigns):
		assert isinstance(name, ast.Name), `name`
		print 'onAssignNonSideEffect', `name`
		if name in assigns:
			del assigns[name]

	def onDelete(self, name, assigns):
		assert isinstance(name, ast.Name), `name`
		print 'onDelete', `name`
		if name in assigns:
			del assigns[name]

	def onAssignSideEffectFree(self, name, value, assigns):
		assigns[name] = name

		# if isinstance(stmt, ast.FunctionDef):

		# stmt = FunctionDef(identifier
		# name, arguments
		# args,
		# stmt * body, expr * decorator_list)
		# | ClassDef(identifier
		# name, expr * bases, stmt * body, expr * decorator_list)
		# | Return(expr? value)
		#
		# | Delete(expr * targets)
		# | Assign(expr * targets, expr
		# value)
		# | AugAssign(expr
		# target, operator
		# op, expr
		# value)
		#
		# --
		# not sure if bool is allowed, can
		# always
		# use
		# int
		# | Print(expr? dest, expr * values, bool
		# nl)
		#
		# -- use
		# 'orelse'
		# because else is a
		# keyword in target
		# languages
		# | For(expr
		# target, expr
		# iter, stmt * body, stmt * orelse)
		# | While(expr
		# test, stmt * body, stmt * orelse)
		# | If(expr
		# test, stmt * body, stmt * orelse)
		# | With(expr
		# context_expr, expr? optional_vars, stmt * body)
		#
		# -- 'type' is a
		# bad
		# name
		# | Raise(expr? type, expr? inst, expr? tback)
		# | TryExcept(stmt * body, excepthandler * handlers, stmt * orelse)
		# | TryFinally(stmt * body, stmt * finalbody)
		# | Assert(expr
		# test, expr? msg)
		#
		# | Import(alias * names)
		# | ImportFrom(identifier? module, alias * names, int? level)
		#
		# -- Doesn
		# 't capture requirement that locals must be
		# -- defined if globals is
		# -- still
		# supports
		# use as a
		# function!
		# | Exec(expr
		# body, expr? globals, expr? locals)
		#
		# | Global(identifier * names)
		# | Expr(expr
		# value)
		# | Pass | Break | Continue

		return stmt, False




