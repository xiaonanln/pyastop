import ast
import sys
import astutils

import namescope


class BaseASTOptimizer(ast.NodeTransformer):

	RequireNameScope = False # if set to True, will analyze Name Scope before optimize

	def __init__(self):
		super(BaseASTOptimizer, self).__init__()
		self._optimized = 0
		if self.RequireNameScope:
			self.currentScope = namescope.builtinsNameScope

	def visit(self, node):
		"""Visit a node."""
		if isinstance(node, ast.AST) and hasattr(node, 'lineno'):
			self.currentPos = node

		if self.RequireNameScope:
			if isinstance(node, ast.Module):
				self.currentScope = namescope.newGlobalNameScope()
				self.currentScope.visitModuleBody(node)
			elif isinstance(node, ast.ClassDef):
				self.currentScope = namescope.NameScope(self.currentScope)
				self.currentScope.visitClassBody(node)
			elif isinstance(node, ast.FunctionDef):
				self.currentScope = namescope.NameScope(self.currentScope)
				self.currentScope.visitFunctionBody(node)

		self.optimizeChildren(node) # optimize children before optimizing parent node
		node, optimized = self.optimize(node)
		assert node is not None
		if optimized: self._optimized += 1

		if self.RequireNameScope:
			if isinstance(node, ast.Module):
				self.currentScope = self.currentScope.parent
			elif isinstance(node, ast.ClassDef):
				self.currentScope = self.currentScope.parent
			elif isinstance(node, ast.FunctionDef):
				self.currentScope = self.currentScope.parent

		return node

	def optimizeChildren(self, node):
		self.generic_visit(node)

	def optimize(self, node):
		return node, False

	@property
	def optimized(self):
		return self._optimized

	@staticmethod
	def node2str(node):
		if hasattr(node, '_fields'):
			name = node.__class__.__name__
			return name + '<' + ', '.join('%s=%s' % (f, BaseASTOptimizer.node2str(getattr(node, f))) for f in node._fields) + '>'
		elif isinstance(node, list):
			return [BaseASTOptimizer.node2str(n) for n in node]
		else:
			return str(node)

	def evalConstExpr(self, expr, ctx=None):
		setStmt = self.makeAssignStmt('_', expr)
		module = ast.Module(body=[setStmt])
		code = compile(module, '<evalExpr>', 'exec')
		G, L = {}, {}
		exec(code, G, L)
		v = L['_']
		# print 'evalConstExpr', type(v), repr(v)
		return self.py2ast(v, ctx=ctx)

	def makeAssignStmt(self, name, expr):
		if isinstance(name, str):
			name = self.makeName(name, ast.Store())

		assignStmt = ast.Assign(targets=[name], value=expr)
		return self._setCurrentPos(assignStmt)

	def makeName(self, id, ctx):
		assert isinstance(id, str)
		name = ast.Name(id=id, ctx=ctx)
		return self._setCurrentPos(name)

	def makeNum(self, n):
		assert isinstance(n, int)
		num = ast.Num(n)
		return self._setCurrentPos(num)

	def isNameEquals(self, node, name):
		if isinstance(name, ast.Name):
			name = name.id

		return isinstance(node, ast.Name) and node.id == name

	def _setCurrentPos(self, node):
		if self.currentPos is not None:
			node.lineno = self.currentPos.lineno
			node.col_offset = self.currentPos.col_offset
			ast.fix_missing_locations(node)
		else:
			node.lineno = node.col_offset = 0

		return node

	def py2ast(self, v, ctx=None):
		node = BaseASTOptimizer._py2ast(v, ctx)
		return self._setCurrentPos(node)

	@staticmethod
	def _py2ast(v, ctx):
		if isinstance(v, (int, long, float)):
			return ast.Num(v)
		elif isinstance(v, str):
			return ast.Str(v)
		elif isinstance(v, list):
			return ast.List([BaseASTOptimizer._py2ast(x, ctx) for x in v], ctx)
		else:
			assert False, ('_py2ast', v)

	def isContinueStmt(self, stmt):
		return isinstance(stmt, ast.Continue)

	def isBreakStmt(self, stmt):
		return isinstance(stmt, ast.Break)

	def containsStmt(self, filter, stmts):
		if isinstance(stmts, list):
			for stmt in stmts:
				if self.containsStmt(filter, stmt):
					return True

			return False

		stmt = stmts
		if filter(stmt):
			return True

		for f in getattr(stmt, '_fields', ()):
			if self.containsStmt(filter, getattr(stmt, f)):
				return True

		return False

	def isNameReferencedBy(self, name, node):
		if isinstance(name, ast.Name):
			name = name.id

		assert isinstance(name, str), name

		if isinstance(node, list):
			for _stmt in node:
				if self.isNameReferencedBy(name, _stmt):
					return True
			return False

		if isinstance(node, ast.Name) and node.id == name:
			return True

		for f in getattr(node, '_fields', ()):
			if self.containsStmt(filter, getattr(node, f)):
				return True

		return False
