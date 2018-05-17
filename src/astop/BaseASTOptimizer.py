import ast
import sys
import astutils
import codegen
import namescope


class BaseASTOptimizer(ast.NodeTransformer):

	RequireNameScope = False # if set to True, will analyze Name Scope before optimize
	RequireTypeInference = False # if set to True, will do type inferences
	RequireResolveExprOptimizeWithStmts = False

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

		if not self.shouldOptimize(node):
			return node

		self.beforeOptimizeNode(node)

		self.optimizeChildren(node) # optimize children before optimizing parent node
		# print 'optimizing ', self.node2src(node),
		origNode = node
		optnode, optimized = self.optimize(node)
		# assert not isinstance(optnode, list), self.node2src(optnode)
		# assert optnode is not None
		if optimized:
			print >>sys.stderr, """%s: File "%s", line %d, %s ==> %s""" % (self.__class__.__name__, self.source, self.currentLineno(), self.node2src(node), self.node2src(optnode))
			self._optimized += 1
			node = optnode

		if node:
			self.fixEmptyStmtList(node)
			if self.RequireResolveExprOptimizeWithStmts:
				if isinstance(node, ast.stmt):
					node = self._resolveExprOptimizeWithStmts_stmt(node)

			assert node is not None

		self.afterOptimizeNode(node, origNode)
		return node

	def currentLineno(self):
		return self._currentNode.lineno if self._currentNode else 0

	def shouldOptimize(self, node):
		return True

	def fixEmptyStmtList(self, node):

		if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.For, ast.While, ast.If, ast.TryExcept, ast.TryFinally)):
			if not node.body:
				print 'fixEmptyStmtList', node, node.body
				node.body.append( self.setCurrentLocation(ast.Pass()) )

		if isinstance(node, ast.TryExcept):
			for handler in node.handlers:
				# ExceptHandler(expr? type, expr? name, stmt* body)
				if not handler.body:
					node.body.append(self.setCurrentLocation(ast.Pass()))

		if isinstance(node, ast.TryFinally):
			if not node.finalbody:
				node.finalbody.append( self.setCurrentLocation(ast.Pass()) )


	# def resolveExprOptimizeWithStmts(self, node):
	# 	# print 'resolveSubExprOptimizeWithStmts', node
	# 	if isinstance(node, ast.expr):
	# 		for subnode in astutils.subexprs(node):
	# 			assert not hasattr(subnode, '_optimize_expr_with_stmts'), self.node2src(node)
	# 		return self._resolveExprOptimizeWithStmts_expr(node)
	# 	elif isinstance(node, ast.stmt):
	# 		return self._resolveExprOptimizeWithStmts_stmt(node)
	# 	# elif isinstance(node, list):
	# 	# 	newstmts = []
	# 	# 	for stmt in node:
	# 	# 		stmt = self.resolveStmtSubExprOptimizeWithStmts(stmt)
	# 	# 		if isinstance(stmt, ast.stmt):
	# 	# 			newstmts.append(stmt)
	# 	# 		else:
	# 	# 			assert isinstance(stmt, list)
	# 	# 			newstmts.extend(stmt)
	# 	#
	# 	# 	return newstmts
	# 	else:
	# 		return node


	def _resolveExprOptimizeWithStmts_stmt(self, stmt):
		assert isinstance(stmt, ast.stmt), ast.dump(stmt)
		if isinstance(stmt, (ast.FunctionDef, ast.ClassDef)): # these statements are unsolvable
			return self._resolveExprOptimizeWithStmts_clearsubexprs(stmt)

		if isinstance(stmt, (ast.Raise, ast.TryExcept)): # todo: these statements should be solvable, but not solved yet
			return self._resolveExprOptimizeWithStmts_clearsubexprs(stmt)

		if isinstance(stmt, (ast.TryFinally, ast.ImportFrom, ast.Import, ast.Global, ast.Pass, ast.Break, ast.Continue)): # these statements has no sub exprs
			return stmt

		prevStmts = []
		if isinstance(stmt, (ast.Return, )): # exprs with only value as sub-expr
			stmt.value = self._resolveExprOptimizeWithStmts_expr(stmt.value, prevStmts)

		elif isinstance(stmt, ast.Delete):
			stmt.targets = self._resolveExprOptimizeWithStmts_exprlist(stmt.targets, prevStmts)
		elif isinstance(stmt, ast.Assign):
			stmt.value = self._resolveExprOptimizeWithStmts_expr(stmt.value, prevStmts) # resolve value first
			stmt.targets = self._resolveExprOptimizeWithStmts_exprlist(stmt.targets, prevStmts) # resolve
		elif isinstance(stmt, ast.AugAssign):
			stmt.value = self._resolveExprOptimizeWithStmts_expr(stmt.value, prevStmts) # resolve value first
			stmt.target = self._resolveExprOptimizeWithStmts_expr(stmt.target, prevStmts)  # resolve value first
		elif isinstance(stmt, ast.Print):
			stmt.dest = self._resolveExprOptimizeWithStmts_expr(stmt.dest, prevStmts)  # resolve value first
			stmt.values = self._resolveExprOptimizeWithStmts_exprlist(stmt.values, prevStmts)  # resolve value first
		elif isinstance(stmt, ast.For): # For(expr target, expr iter, stmt* body, stmt* orelse)
			stmt.iter = self._resolveExprOptimizeWithStmts_expr(stmt.iter, prevStmts)
			stmt.target = self._resolveExprOptimizeWithStmts_ignore(stmt.target) # we do not support optimized target ...
		elif isinstance(stmt, ast.While): # While(expr test, stmt* body, stmt* orelse)
			stmt.test = self._resolveExprOptimizeWithStmts_ignore(stmt.test)
		elif isinstance(stmt, ast.If): # If(expr test, stmt* body, stmt* orelse)
			stmt.test = self._resolveExprOptimizeWithStmts_expr(stmt.test, prevStmts)
		elif isinstance(stmt, ast.With): # With(expr context_expr, expr? optional_vars, stmt* body)
			stmt.context_expr = self._resolveExprOptimizeWithStmts_expr(stmt.context_expr, prevStmts)
			stmt.optional_vars = self._resolveExprOptimizeWithStmts_expr(stmt.optional_vars, prevStmts)
		elif isinstance(stmt, ast.Assert): # Assert(expr test, expr? msg)
			stmt.test = self._resolveExprOptimizeWithStmts_expr(stmt.test, prevStmts)
			stmt.msg = self._resolveExprOptimizeWithStmts_ignore(stmt.msg) # todo: msg not resolved yet
		elif isinstance(stmt, ast.Exec): #Exec(expr body, expr? globals, expr? locals)
			stmt.body = self._resolveExprOptimizeWithStmts_expr(stmt.body, prevStmts)
			stmt.globals = self._resolveExprOptimizeWithStmts_expr(stmt.globals, prevStmts)
			stmt.locals = self._resolveExprOptimizeWithStmts_expr(stmt.locals, prevStmts)
		elif isinstance(stmt, ast.Expr): # Expr(expr value)
			stmt.value = self._resolveExprOptimizeWithStmts_expr(stmt.value, prevStmts)
		else:
			assert False, ast.dump(stmt)

		if not prevStmts:
			return stmt
		else:
			return prevStmts + [stmt]

	def _resolveExprOptimizeWithStmts_expr(self, expr, prevStmts):
		if expr is None:
			return None

		assert isinstance(expr, ast.expr)
		if hasattr(expr, '_optimize_expr_with_stmts'):
			self._resolveExprOptimizeWithStmts_clearsubexprs(expr)
			# print '_optimize_expr_with_stmts', expr._optimize_expr_with_stmts
			optexpr, optstmts = expr._optimize_expr_with_stmts
			assert optstmts, 'at least 1 stmt'
			del expr._optimize_expr_with_stmts
			prevStmts.extend(optstmts)

			optExprName = self.currentScope.newLocalName("expr")
			if not astutils.isSideEffectFreeExpr(optexpr):
				stmt = self.makeAssign(self.makeName(optExprName, ast.Store()), optexpr)
				prevStmts.append(self.setCurrentLocation(stmt))
				optexpr = self.makeName(optExprName)

			return optexpr

		if isinstance(expr, (ast.Num, ast.Str, ast.Name)): # these expr needs no further process
			pass
		elif isinstance(expr, ast.BoolOp): # BoolOp(boolop op, expr* values)
			values = expr.values
			boolop = expr.op

			for i, val in enumerate(values):
				boolopPrevStmts = []
				values[i] = val = self._resolveExprOptimizeWithStmts_expr(val, boolopPrevStmts)
				if boolopPrevStmts: # prev expr is optimized with stmts
					if i > 0 and not astutils.isSideEffectFreeExpr(ast.BoolOp(boolop, values[:i])):
						prevVar = self.currentScope.newLocalName("boolop")
						prevExpr = ast.BoolOp(boolop, values[:i])
						leftExpr = self._resolveExprOptimizeWithStmts_expr(ast.BoolOp(boolop, values[i:]), boolopPrevStmts)
						if isinstance(boolop, ast.And):
							test = self.makeName(prevVar)
						else:
							test = ast.UnaryOp(ast.Not(), self.makeName(prevVar))
						boolopPrevStmts = [
							self.makeAssign(self.makeName(prevVar, ast.Store()), prevExpr),
							ast.If(test, boolopPrevStmts + [
								self.makeAssign(self.makeName(prevVar, ast.Store()), leftExpr)
							], []),
						]
						self.setCurrentLocation(boolopPrevStmts)
						prevStmts.extend(boolopPrevStmts)
						expr = self.makeName(prevVar)
						break
					else: # i == 0 or prev exprs are all side-effect free
						prevStmts.extend(boolopPrevStmts)
						continue
		elif isinstance(expr, ast.BinOp): # BinOp(expr left, operator op, expr right)
			expr.left = self._resolveExprOptimizeWithStmts_expr(expr.left, prevStmts)
			expr.right = self._resolveExprOptimizeWithStmts_expr(expr.right, prevStmts)
		elif isinstance(expr, ast.UnaryOp):
			expr.operand = self._resolveExprOptimizeWithStmts_expr(expr.operand, prevStmts)
		elif isinstance(expr, ast.Lambda): # can not resolve lambda
			self._resolveExprOptimizeWithStmts_clearsubexprs(expr)
		elif isinstance(expr, ast.IfExp):
			expr.test = self._resolveExprOptimizeWithStmts_expr(expr.test, prevStmts) # eval test first
			bodyPrevStmts = []
			orelsePrevStmts = []
			body = self._resolveExprOptimizeWithStmts_expr(expr.body, bodyPrevStmts)
			orelse = self._resolveExprOptimizeWithStmts_expr(expr.orelse, orelsePrevStmts)
			if bodyPrevStmts or orelsePrevStmts:
				# body or orelse is optimized with stmts, we need to convert IfExp to If statement
				resVar = self.currentScope.newLocalName("ifexp")
				ifstmt = ast.If(expr.test, bodyPrevStmts + [ self.makeAssign(self.makeName(resVar, ast.Store()), body) ],
				       orelsePrevStmts + [ self.makeAssign(self.makeName(resVar, ast.Store()), orelse) ])
				self.setCurrentLocation(ifstmt)
				prevStmts.append(ifstmt)
				expr = self.makeName(resVar)
		elif isinstance(expr, (ast.Set, ast.List, ast.Tuple)):
			expr.elts = self._resolveExprOptimizeWithStmts_exprlist(expr.elts, prevStmts)
		elif isinstance(expr, ast.Dict):
			# the evaluation order is v1, k2, v2, k2, v3, k3 ...
			for i, k in enumerate(expr.keys): # for each key-value pair
				expr.values[i] = self._resolveExprOptimizeWithStmts_expr(expr.values[i], prevStmts) # eval value first
				expr.keys[i] = self._resolveExprOptimizeWithStmts_expr(k, prevStmts)  # then eval key
		elif isinstance(expr, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.Yield)): # can not resolve these exprs
			self._resolveExprOptimizeWithStmts_clearsubexprs(expr)
		elif isinstance(expr, ast.Compare): # Compare(expr left, cmpop* ops, expr* comparators)
			expr.left = self._resolveExprOptimizeWithStmts_expr(expr.left, prevStmts)
			expr.comparators = self._resolveExprOptimizeWithStmts_exprlist(expr.comparators, prevStmts)
		elif isinstance(expr, ast.Call): # Call(expr func, expr* args, keyword* keywords, #  expr? starargs, expr? kwargs)
			expr.func = self._resolveExprOptimizeWithStmts_expr(expr.func, prevStmts)
			expr.args = self._resolveExprOptimizeWithStmts_exprlist(expr.args, prevStmts)
			expr.keywords = self._resolveExprOptimizeWithStmts_keywords(expr.keywords, prevStmts)
			expr.starargs = self._resolveExprOptimizeWithStmts_expr(expr.starargs, prevStmts)
			expr.kwargs = self._resolveExprOptimizeWithStmts_expr(expr.kwargs, prevStmts)
		elif isinstance(expr, (ast.Attribute, ast.Repr)): # Attribute(expr value, identifier attr, expr_context ctx)
			expr.value = self._resolveExprOptimizeWithStmts_expr(expr.value, prevStmts)
		elif isinstance(expr, ast.Subscript): # Subscript(expr value, slice slice, expr_context ctx)
			expr.value = self._resolveExprOptimizeWithStmts_expr(expr.value, prevStmts)
			expr.slice = self._resolveExprOptimizeWithStmts_slice(expr.slice, prevStmts)
		else:
			assert False, ('not an expr', ast.dump(expr))

		return expr

	def _resolveExprOptimizeWithStmts_ignore(self, expr):
		if expr is None: return None
		assert isinstance(expr, ast.expr)
		self._resolveExprOptimizeWithStmts_clearsubexprs(expr)
		if hasattr(expr, '_optimize_expr_with_stmts'):
			del expr._optimize_expr_with_stmts
		return expr

	def _resolveExprOptimizeWithStmts_exprlist(self, exprs, prevStmts):
		assert isinstance(exprs, list)
		for i, expr in enumerate(exprs):
			exprs[i] = self._resolveExprOptimizeWithStmts_expr(expr, prevStmts)
		return exprs

	def _resolveExprOptimizeWithStmts_clearsubexprs(self, node):
		assert isinstance(node, (ast.stmt, ast.expr))
		for subnode in astutils.subexprs(node):
			if isinstance(subnode, ast.expr) and hasattr(subnode, '_optimize_expr_with_stmts'):
				del subnode._optimize_expr_with_stmts
				self._resolveExprOptimizeWithStmts_clearsubexprs(subnode)

		return node

	def _resolveExprOptimizeWithStmts_slice(self, slice, prevStmts):
		assert isinstance(slice, ast.slice)
		# slice = Ellipsis | Slice(expr? lower, expr? upper, expr? step)
      # | ExtSlice(slice* dims)
      # | Index(expr value)
		if isinstance(slice, ast.Ellipsis):
			return slice
		elif isinstance(slice, ast.Slice):
			slice.lower = self._resolveExprOptimizeWithStmts_expr(slice.lower, prevStmts)
			slice.upper = self._resolveExprOptimizeWithStmts_expr(slice.upper, prevStmts)
			slice.step = self._resolveExprOptimizeWithStmts_expr(slice.step, prevStmts)
		elif isinstance(slice, ast.ExtSlice):
			for i, ss in enumerate(slice.dims):
				slice.dims[i] = self._resolveExprOptimizeWithStmts_slice(ss, prevStmts)
		elif isinstance(slice, ast.Index):
			slice.value = self._resolveExprOptimizeWithStmts_expr(slice.value, prevStmts)

		return slice

	def _resolveExprOptimizeWithStmts_keywords(self, keywords, prevStmts):
		for kw in keywords:
			kw.value = self._resolveExprOptimizeWithStmts_expr(kw.value, prevStmts)
		return keywords

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

	def afterOptimizeNode(self, node, origNode):
		if self.requireNameScopes():
			if isinstance(origNode, ast.Module):
				self.currentScope = self.currentScope.parent
			elif isinstance(origNode, ast.ClassDef):
				self.currentScope = self.currentScope.parent
			elif isinstance(origNode, ast.FunctionDef):
				self.currentScope = self.currentScope.parent

	def isOnStack(self, node):
		assert isinstance(node, (ast.FunctionDef, ast.Module, ast.ClassDef))
		scope = self.currentScope
		while scope and scope.node is not node:
			scope = scope.parent

		return scope is not None

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
			setStmt = self.makeAssign('_', expr)
			module = ast.Module(body=[setStmt])
			code = compile(module, '<evalExpr>', 'exec')
			G, L = {}, {}
			exec(code, G, L)
			v = L['_']
			# print 'evalConstExpr', type(v), repr(v)
			return self.py2ast(v, ctx=ast.Load())
		except:
			self.info('eval const expr failed: %s', self.node2src(expr))
			raise


	def makeAssign(self, name, expr):
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
		elif isinstance(v, (basestring)):
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
		elif isinstance(v, frozenset):
			return ast.Call( ast.Name('frozenset', ctx), [BaseASTOptimizer._py2ast(list(v), ctx), ], [], None, None)
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

	def node2src(self, node):
		if isinstance(node, list):
			return "[" + ", ".join(map(self.node2src, node)) + "]"
		elif node is None:
			return '<none>'

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

	def fatal(self, format, *args):
		import traceback
		traceback.print_stack()
		msg = format % args
		print >>sys.stderr, 'File "%s", line %d: %s' % (self.source, self.currentLineno(), msg)
		print >>sys.stderr, 'fatal error occurred, quit ...'
		exit(1)

	def error(self, format, *args):
		msg = format % args
		print >>sys.stderr, 'File "%s", line %d: %s' % (self.source, self.currentLineno(), msg)

	def info(self, format, *args):
		msg = format % args
		print >>sys.stderr, 'File "%s", line %d: %s' % (self.source, self.currentLineno(), msg)

	def debug(self, format, *args):
		msg = format % args
		print >>sys.stderr, 'File "%s", line %d: %s' % (self.source, self.currentLineno(), msg)

