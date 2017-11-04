import ast
import astutils
import consts

class NameScope(object):
	def __init__(self, node, parent):
		self.node = node
		self.parent = parent
		self.globals = set()
		self.locals = set()

	def isNameResolved(self, name):
		if name in self.globals:
			globalScope = self.getGlobalScope()
			return globalScope and globalScope.isNameResolved(name)

		while self:
			if name in self.locals:
				return True

	def addGlobalName(self, name):
		assert isinstance(name, str), name
		self.globals.add(name)

	def isGlobalScope(self):
		return self.parent == builtinsNameScope

	def isBuiltinsScope(self):
		return self == builtinsNameScope

	def getGlobalScope(self):
		while self and not self.isGlobalScope():
			self = self.parent

		return self # find the global scope or None if not found

	def visitModuleBody(self, node):
		assert node, ast.Module
		# let all stmts add names to the local scope
		for stmt in node.body:
			self.visitStmt(stmt)

	def visitStmt(self, stmt):
		if isinstance(stmt, (ast.FunctionDef, ast.ClassDef)):
			self.onAssignName(stmt.name)
		elif isinstance(stmt, (ast.Delete, ast.Assign)):
			for expr in stmt.targets:
				self.visitAssignedNamesInExpr(expr)
		elif isinstance(stmt, ast.AugAssign):
			self.visitAssignedNamesInExpr(stmt.target)
		elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
			for alias in stmt.names:
				self.visitAssignedNamesInAlias(alias)

		if self.isGlobalScope() and isinstance(stmt, (ast.FunctionDef, ast.ClassDef)):
			# if this is the module scope, and we are visiting functions or classes, put the function or class's global names to the current local names
			for stmt in stmt.body:
				self.visitGlobalStmt(stmt, asLocal=True)

	def visitAssignedNamesInExpr(self, expr):
		if isinstance(expr, (ast.Attribute, ast.Subscript)):
			pass
		elif isinstance(expr, (ast.List, ast.Tuple)):
			for exp in expr.elts:
				self.visitAssignedNamesInExpr(exp)
		elif isinstance(expr, ast.Name):
			self.onAssignName(expr)
		else:
			assert False, ('should not assign', ast.dump(expr))

	def visitAssignedNamesInAlias(self, alias):
		assert isinstance(alias, ast.alias), repr(alias)
		if alias.asname:
			self.onAssignName(alias.asname)

	def visitGlobalStmt(self, stmt, asLocal=False):
		if isinstance(stmt, ast.Global):
			for name in stmt.names:
				self.addGlobalName(name)
		else:
			for ss in astutils.substmts(stmt):
				self.visitGlobalStmt(ss, asLocal=asLocal)

	def visitFunctionBody(self, node):
		assert node, ast.FunctionDef

		# find all global names first
		for stmt in node.body:
			self.visitGlobalStmt(stmt, asLocal=False)

		# let all stmts add names to the local scope
		for stmt in node.body:
			self.visitStmt(stmt)

	def visitClassBody(self, node):
		assert node, ast.ClassDef
		# let all stmts add names to the local scope
		for stmt in node.body:
			self.visitStmt(stmt)

	def onAssignName(self, name):
		"""called when name is assigned"""
		assert isinstance(name, (ast.Name, str)), repr(name)
		if isinstance(name, ast.Name):
			assert isinstance(name.ctx, (ast.Store, ast.Del)), (name.id, name.ctx)
			name = name.id

		if name in self.globals:
			return

		self.locals.add(name)

	def isConstantExpr(self, expr):
		if isinstance(expr, ast.Num):
			return True
		elif isinstance(expr, ast.Str):
			return True
		elif isinstance(expr, ast.BoolOp):
			return all( self.isConstantExpr(e) for e in expr.values )
		elif isinstance(expr, ast.BinOp):
			return all( self.isConstantExpr(e) for e in (expr.left, expr.right) )
		elif isinstance(expr, ast.UnaryOp):
			return self.isConstantExpr(expr.operand)
		elif isinstance(expr, ast.IfExp):
			return all(self.isConstantExpr(e) for e in (expr.test, expr.body, expr.orelse))
		elif isinstance(expr, ast.Dict):
			return all(self.isConstantExpr(e) for e in (expr.keys + expr.values))
		elif isinstance(expr, ast.Set):
			return all(self.isConstantExpr(e) for e in expr.elts)
		elif isinstance(expr, ast.Compare):
			return all(self.isConstantExpr(e) for e in [expr.left] + expr.comparators)
		elif isinstance(expr, (ast.List, ast.Tuple)):
			return all(self.isConstantExpr(e) for e in expr.elts)
		elif isinstance(expr, ast.Call):
			# Call(expr func, expr * args, keyword * keywords, expr? starargs, expr? kwargs)
			# keyword = (identifier arg, expr value)
			return self.isCallArgumentsConst(expr) and self.isConstToConstFunc(expr.func)
		elif isinstance(expr, ast.Name):
			return expr.id in  consts.CONST_BUILTIN_NAMES

		# elif isinstance(expr, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
		# 	# | ListComp(expr elt, comprehension * generators)
		# 	# | SetComp(expr elt, comprehension * generators)
		# 	# | GeneratorExp(expr elt, comprehension * generators)
		# 	return self.isConstantExpr(expr.elt) and all(isConstComprehension(c) for c in expr.generators)
		# elif isinstance(expr, ast.DictComp):
		# 	# | DictComp(expr key, expr value, comprehension * generators)
		# 	return self.isConstantExpr(expr.key) and self.isConstantExpr(expr.value) and all(isConstComprehension(c) for c in expr.generators)

		return False

	def isCallArgumentsConst(self, call):
		assert isinstance(call, ast.Call)
		if any(not self.isConstantExpr(arg) for arg in call.args):
			return False

		if any(not self.isConstantExpr(kw.value) for kw in call.keywords):
			return False

		if call.starargs and not self.isConstantExpr(call.starargs):
			return False

		if call.kwargs and not self.isConstantExpr(call.kwargs):
			return False

		return True

	def isConstToConstFunc(self, expr):
		# print 'isConstToConstFunc', ast.dump(expr), isinstance(expr, ast.Name), expr.id in consts.CONST_TO_CONST_BUILTIN_FUNCS, self.isBuiltinName(expr.id )
		if not isinstance(expr, ast.Name): return False
		funcName = expr.id
		return funcName in consts.CONST_TO_CONST_BUILTIN_FUNCS and self.isBuiltinName(funcName)

	def isLocalName(self, name):
		assert isinstance(name, str)
		return name in self.locals

	def isGlobalName(self, name):
		assert isinstance(name, str)
		scope = self
		while scope:
			if name in scope.locals:
				return self.isGlobalScope()
			elif name in scope.globals:
				return True

			scope = scope.parent

	def isBuiltinName(self, name):
		assert isinstance(name, str)
		scope = self
		while scope:
			if name in scope.locals:
				return scope.isBuiltinsScope()
			elif name in scope.globals:
				return False
			scope = scope.parent

		return False

builtinsNameScope = NameScope(None, None)
builtinsNameScope.locals |= set(consts.BUILTIN_NAMES)

def newGlobalNameScope(module):
	assert isinstance(module, ast.Module)
	scope = NameScope(module, builtinsNameScope)
	scope.locals |= set(['__builtins__', '__doc__', '__name__', '__package__'])
	return scope
