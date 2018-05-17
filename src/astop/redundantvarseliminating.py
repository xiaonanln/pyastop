
import ast
from BaseASTOptimizer import BaseASTOptimizer
from BaseSkipInnerASTOptimizer import BaseSkipInnerASTOptimizer
import astutils

unoptimizableValue = 'unoptimizableValue'

class _ReplaceVarASTOptimizer(BaseSkipInnerASTOptimizer):

	def __init__(self, vars):
		super(_ReplaceVarASTOptimizer, self).__init__()
		assert vars, vars
		self.vars = vars

	def optimize(self, node):
		print '_ReplaceVarASTOptimizer.optimize', self.node2src(node), self.vars
		if isinstance(node, ast.Assign) and len(node.targets) == 1:
			expr = node.targets[0]
			if isinstance(expr, ast.Name) and expr.id in self.vars:
				return None, True

		if isinstance(node, ast.Expr) and isinstance(node.value, ast.Name) and node.value.id in self.vars:
			return None, True

		if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in self.vars:
			# print 'replacing %s with %s' % (node.id, self.node2str(self.vars[node.id]))
			return self.vars[node.id], True

		return node, False

	# def shouldOptimize(self, node):
	# 	return True

class RedundantVarsEliminatingASTOptimizer(BaseASTOptimizer):

	RequireNameScope = True

	def __init__(self):
		super(RedundantVarsEliminatingASTOptimizer, self).__init__()
		self.scopeAssigns = {} # {scope : assigns}

	def getAssigns(self, scope):
		assert not scope.isGlobalScope(), scope
		if scope not in self.scopeAssigns:
			self.scopeAssigns[scope] = {}

		return self.scopeAssigns[scope]

	def shouldOptimize(self, node):
		return True

	def optimize(self, func):
		if not isinstance(func, ast.FunctionDef):
			return func, False

		print 'optimize func %s' % func.name
		aliases = self.analyzeAliases(func)
		replaceVars = {k: v for k, v in aliases.iteritems() if v is not unoptimizableValue}
		print 'aliases', aliases, 'replaceVars', replaceVars
		newbody, opt = self.optimizeStmtList(func.body, replaceVars)
		if opt:
			func.body = newbody
		return func, opt

	def analyzeAliases(self, func):
		assert isinstance(func, ast.FunctionDef)
		aliases = {}
		for stmt in astutils.substmts_no_inner(func):
			self.visitAssignsInStmt(stmt, aliases)

		return aliases

	def optimizeStmtList(self, stmtlist, replaceVars):
		if not replaceVars:
			return stmtlist, False

		optimized = False
		newstmtlist = []

		for stmt in stmtlist:
			stmt, opted = self.optimizeStmt(stmt, replaceVars)
			if stmt is not None:
				newstmtlist.append(stmt)
			if opted:
				optimized = True

		if optimized:
			return newstmtlist, True
		else:
			return stmtlist, False

	def optimizeStmt(self, stmt, replaceVars):
		if not replaceVars:
			return stmt, False

		print 'optimize %s with aliases %s' % (stmt.__class__.__name__, replaceVars)
		rvopter = _ReplaceVarASTOptimizer(replaceVars)

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

		# if not name.startswith('_pyastop_'):
		# 	# only eliminate _pyastop_ variables
		# 	return

		assert not self.currentScope.isGlobalScope()

		if not self.currentScope.isLocalName(name):
			# can not optimize global variable
			return

		self.removeAffectedValuesByAssign( name, assigns )

		if value == unoptimizableValue:
			assigns[name] = unoptimizableValue
		elif name in assigns:
			# name assigned multiples, we can not optimize it
			assigns[name] = unoptimizableValue
		else:
			assert astutils.isexpr(value)
			# print self, 'assign', name, self.node2src(value), 'sideaffectfree', astutils.isSideEffectFreeExpr(value), 'selfref', astutils.isNameReferenced(name, value)
			if astutils.isSideEffectFreeExpr(value) and not astutils.isNameReferenced(name, value):
			# if isinstance(value, (ast.Name, ast.Num, ast.Str)):
				assigns[name] = value
			else:
				assigns[name] = unoptimizableValue

	def removeAffectedValuesByAssign(self, name, assigns):
		for aname, aval in assigns.items():
			if aval is unoptimizableValue:
				continue

			if astutils.isNameReferenced(name, aval):
				assigns[aname] = unoptimizableValue

