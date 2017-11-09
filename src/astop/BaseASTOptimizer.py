import ast
import sys
import astutils
import codegen
import namescope


class BaseASTOptimizer(ast.NodeTransformer):

	RequireNameScope = False # if set to True, will analyze Name Scope before optimize
	RequireTypeInference = False # if set to True, will do type inferences

	def __init__(self):
		super(BaseASTOptimizer, self).__init__()
		self._optimized = 0
		self.source = ""
		if self.requireNameScopes():
			self.currentScope = namescope.builtinsNameScope
			self.nameScopes = {}

	def requireNameScopes(self):
		return self.RequireNameScope or self.RequireTypeInference

	def visit(self, node):
		"""Visit a node."""
		if isinstance(node, ast.Module):
			self.source = node.source
			if self.requireNameScopes():
				# visiting this module
				self.nameScopes = namescope.genNameScopes(node)

		if isinstance(node, ast.AST) and hasattr(node, 'lineno'):
			self._currentNode = node

		self.beforeOptimizeNode(node)

		self.optimizeChildren(node) # optimize children before optimizing parent node
		# print 'optimizing ', self.node2src(node),
		optnode, optimized = self.optimize(node)
		# assert not isinstance(optnode, list), self.node2src(optnode)
		assert optnode is not None
		if optimized:
			print >>sys.stderr, """File "%s", line %d, %s ==> %s""" % (self.source, self.currentLineno(), self.node2src(node), self.node2src(optnode))
			self._optimized += 1
			node = optnode

		for subnode in astutils.subnodes_recursive(node):
			if isinstance(subnode, (ast.stmt, ast.expr)):
				assert not hasattr(subnode, '_optimize_expr_with_stmts'), ast.dump(subnode)

		self.afterOptimizeNode(node)
		return node

	def currentLineno(self):
		return self._currentNode.lineno if self._currentNode else 0

	def beforeOptimizeNode(self, node):
		if self.requireNameScopes():
			if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
				self.currentScope = self.nameScopes[node] # node should exists in name scopes

			# 	self.currentScope = namescope.newGlobalNameScope(node)
			# 	self.currentScope.visitModuleBody(node)
			# elif isinstance(node, ast.ClassDef):
			# 	self.currentScope = namescope.NameScope(node, self.currentScope)
			# 	self.currentScope.visitClassBody(node)
			# elif isinstance(node, ast.FunctionDef):
			# 	self.currentScope = namescope.NameScope(node, self.currentScope)
			# 	self.currentScope.visitFunctionBody(node)

	def afterOptimizeNode(self, node):
		if self.requireNameScopes():
			if isinstance(node, ast.Module):
				self.currentScope = self.currentScope.parent
			elif isinstance(node, ast.ClassDef):
				self.currentScope = self.currentScope.parent
			elif isinstance(node, ast.FunctionDef):
				self.currentScope = self.currentScope.parent

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
			return ast.dump(node)
		elif isinstance(node, list):
			return [BaseASTOptimizer.node2str(n) for n in node]
		else:
			return str(node)

	def evalConstExpr(self, expr):
		try:
			setStmt = self.makeAssignStmt('_', expr)
			module = ast.Module(body=[setStmt])
			code = compile(module, '<evalExpr>', 'exec')
			G, L = {}, {}
			exec(code, G, L)
			v = L['_']
			# print 'evalConstExpr', type(v), repr(v)
			return self.py2ast(v, ctx=ast.Load())
		except:
			print >>sys.stderr, 'eval const expr failed:', ast.dump(expr)
			raise


	def makeAssignStmt(self, name, expr):
		if isinstance(name, str):
			name = self.makeName(name, ast.Store())

		assignStmt = ast.Assign(targets=[name], value=expr)
		return self.setCurrentLocation(assignStmt)

	def makeName(self, id, ctx=None):
		assert isinstance(id, str)
		name = ast.Name(id=id, ctx=ctx or ast.Load())
		return self.setCurrentLocation(name)

	def makeNum(self, n):
		assert isinstance(n, int)
		num = ast.Num(n)
		return self.setCurrentLocation(num)

	# def makeCall(self, func, args):
	# 	assert isinstance(func, str)

	def isNameEquals(self, node, name):
		if isinstance(name, ast.Name):
			name = name.id

		return isinstance(node, ast.Name) and node.id == name

	def setCurrentLocation(self, node):
		if isinstance(node, list):
			for _node in node:
				self.setCurrentLocation(_node)
			return

		if self._currentNode is not None:
			return self.copyLocation(node, self._currentNode)
		else:
			node.lineno = node.col_offset = 0

		return node

	def copyLocation(self, newnode, oldnode):
		ast.copy_location(newnode, oldnode)
		ast.fix_missing_locations(newnode)
		return newnode

	def py2ast(self, v, ctx=None):
		node = BaseASTOptimizer._py2ast(v, ctx)
		return self.setCurrentLocation(node)

	@staticmethod
	def _py2ast(v, ctx):
		if isinstance(v, (int, long, float)):
			return ast.Num(v)
		elif isinstance(v, str):
			return ast.Str(v)
		elif isinstance(v, list):
			return ast.List([BaseASTOptimizer._py2ast(x, ctx) for x in v], ctx)
		elif isinstance(v, dict):
			items = v.items()
			keys = [BaseASTOptimizer._py2ast(k, ctx) for k, v in items]
			vals = [BaseASTOptimizer._py2ast(v, ctx) for k, v in items]
			return ast.Dict( keys, vals )
		elif isinstance(v, tuple):
			return ast.Tuple([BaseASTOptimizer._py2ast(x, ctx) for x in v], ctx)
		elif isinstance(v, set):
			assert isinstance(ctx, ast.Load)
			return ast.Set([BaseASTOptimizer._py2ast(x, ctx) for x in v])
		elif v is None:
			assert isinstance(ctx, ast.Load)
			return ast.Name('None', ctx)
		elif v is True:
			assert isinstance(ctx, ast.Load)
			return ast.Name('True', ctx)
		elif v is False:
			assert isinstance(ctx, ast.Load)
			return ast.Name('False', ctx)
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

	def node2src(self, node):
		if isinstance(node, list):
			return "[" + ", ".join(map(self.node2src, node)) + "]"

		return codegen.to_source(node)

	def estimateXrangeLen(self, iter):
		assert isinstance(iter, ast.Call), ast.dump(iter)
		if iter.starargs: # call xrange using starargs? can not solve this yet
			return None, False

		args = iter.args
		start, stop, step = 0, None, 1
		if len(args) == 1:
			expr = self.evalConstExpr(args[0])
			assert isinstance(expr, ast.Num)
			stop = expr.n
		elif len(args) == 2:
			expr = self.evalConstExpr(args[0])
			assert isinstance(expr, ast.Num)
			start = expr.n
			expr = self.evalConstExpr(args[1])
			assert isinstance(expr, ast.Num)
			stop = expr.n
		elif len(args) == 3:
			expr = self.evalConstExpr(args[0])
			assert isinstance(expr, ast.Num)
			start = expr.n
			expr = self.evalConstExpr(args[1])
			assert isinstance(expr, ast.Num)
			stop = expr.n
			expr = self.evalConstExpr(args[2])
			assert isinstance(expr, ast.Num)
			step = expr.n
		else:
			assert False, 'xrange() requires 1~3 arguments'

		assert step != 0, 'step should be nonzero'
		if step > 0:
			stop = max(stop, start) # make stop >= start if step > 0
		elif step < 0:
			stop = min(stop, start) # make stop <= start if step < 0

		n = (stop - start + step - 1) // step
		return n, True

	def info(self, format, *args):
		msg = format % args
		print >>sys.stderr, 'File "%s", line %d: %s' % (self.source, self.currentLineno(), msg)

	def debug(self, format, *args):
		msg = format % args
		print >>sys.stderr, 'File "%s", line %d: %s' % (self.source, self.currentLineno(), msg)

