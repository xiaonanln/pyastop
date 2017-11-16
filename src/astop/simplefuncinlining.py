
import ast
import astutils
import consts
import namescope
from BaseASTOptimizer import BaseASTOptimizer

class SimpleFuncInliningASTOptimizer(BaseASTOptimizer):

	RequireTypeInference = True
	RequireResolveExprOptimizeWithStmts = True

	def optimize(self, node):
		if not isinstance(node, ast.Call):
			return node, False

		# Call(expr func, expr * args, keyword * keywords, expr? starargs, expr? kwargs)
		node, opted = self.tryOptimizeCall(node)
		assert isinstance(node, ast.expr), ast.dump(node)
		return node, opted

	def tryOptimizeStmt(self, stmt):
		if isinstance(stmt, ast.Expr):
			if hasattr(stmt.value, '_optimize_expr_with_stmts'):
				# value is optimized, so pass optimization to this stmt
				optval, optstmts = stmt.value._optimize_expr_with_stmts
				print 'optval', ast.dump(optval)
				print 'optstmts', self.node2src(optstmts)
				newstmt = ast.Expr(optval)
				ast.copy_location(newstmt, stmt)
				return optstmts + [newstmt]

		return stmt, False

	def tryOptimizeCall(self, call):
		assert isinstance(call, ast.Call)
		# Call(expr func, expr * args, keyword * keywords, expr? starargs, expr? kwargs)

		func, bounded = self.tryDetermineFunction(call.func)
		if isinstance(call.func, ast.Name) and call.func.id == 'eval':
			print self.node2src(call), func, bounded
		if not func:
			return call, False

		if self.isOnStack(func): # recursive call ?
			return call, False

		assert isinstance(func, ast.FunctionDef)

		# determine for all arguments it's value
		# arguments = (expr * args, identifier? vararg, identifier? kwarg, expr * defaults)
		if not self.canOptimizeFunc(func):
			return call, False

		argstart = 1 if bounded else 0
		argname2index = {}
		for i, arg in enumerate(func.args.args):
			if i < argstart: continue
			if isinstance(arg, ast.Name):
				argname2index[arg.id] = i

		callargs = []
		if bounded:
			assert isinstance(call.func, ast.Attribute), 'should be Attribute'
			callargs.append(call.func.value)

		callargs += list(call.args)
		if call.starargs:
			if not isinstance(call.starargs, (ast.List, ast.Tuple, ast.Set) ):
				return call, False

			callargs = callargs + call.starargs.elts # call.starargs must be list, tuple, ...

		assert len(callargs) <= len(func.args.args), ('too many arguments', self.node2src(call))
		callargs += [None] * (len(func.args.args) - len(callargs))

		keys = []
		values = []
		# keyword = (identifier arg, expr value)
		if call.keywords:
			keys += [kw.arg for kw in call.keywords]
			values += [kw.value for kw in call.keywords]

		if call.kwargs:
			if not isinstance(call.kwargs, ast.Dict):
				return call, False

			for k in call.kwargs.keys:
				if not isinstance(k, ast.Name):
					return call, False

			keys += [k.id for k in call.kwargs.keys]
			values += call.kwargs.values

		assert len(keys) == len(values)
		for key, val in zip(keys, values):
			assert key in argname2index, 'argument %s is not valid' % key
			argindex = argname2index[key]
			assert callargs[argindex] is None, 'duplicate argument %s' % key
			callargs[argindex] = val

		for i, arg in enumerate(callargs):
			if arg is None:
				defaultindex = i - (len(func.args.args) - len(func.args.defaults))
				assert defaultindex >= 0, '%s: default index is %d, args=%s, defaults=%s' % (self.node2src(call), defaultindex, self.node2src(func.args.args), self.node2src(func.args.defaults))
				defaultval = func.args.defaults[defaultindex]
				if not self.isImmutableDefaultArg(defaultval):
					return call, False

				callargs[i] = astutils.copy_node(defaultval)

		assert len(func.args.args) == len(callargs), (func.args.args, callargs)
		# start inlining ...

		retexpr, stmts = self._inlineFunction(call, func, callargs)
		self.debug( 'SimpleFuncInliningASTOptimizer: inlining %s, arguments: %s, func locals: %s ==> %s', self.node2src(call), self.node2src(callargs), func.scope.locals.keys(),
		            self.node2src(stmts))

		call._optimize_expr_with_stmts = (retexpr, stmts)
		return call, True

	def _inlineFunction(self, call, func, callargs):
		# step 1: generate new local name for return value
		returnName = self.currentScope.newLocalName("inl")
		# inline the target function body
		# replace all locals in target function
		replaceNames = {}
		assignparams = []
		for localName in func.scope.locals:
			newLocalName = self.currentScope.newLocalName("inl")
			replaceNames[localName] = newLocalName

		assignargs = []
		for arg, argval in zip( func.args.args, callargs ):
			assignargs.append(self.makeAssign(self._inlineNode(arg, replaceNames, returnName), argval))

		# step 1: replace all locals in called function
		# replace all names in stmts
		newbody = [self._inlineNode(stmt, replaceNames, returnName) for stmt in func.body]
		for stmt in newbody:
			astutils.check_missing_lineno(stmt)
		return self.makeName(returnName, ast.Load()), assignargs + newbody

	def _inlineNode(self, node, replaceNames, returnName):
		if isinstance(node, ast.Name) and node.id in replaceNames:
			ctx = node.ctx
			if isinstance(ctx, ast.Param):
				ctx = ast.Store()
			newname = ast.Name(replaceNames[node.id], ctx)
			ast.copy_location(newname, node)
			# astutils.check_missing_lineno(newname)
			return newname

		if isinstance(node, list):
			return [self._inlineNode(subnode, replaceNames, returnName) for subnode in node]

		if isinstance(node, ast.AST):
			# this is a node
			fields = tuple( self._inlineNode(getattr(node, k), replaceNames, returnName) for k in node._fields)
			assert 'lineno' not in node._fields
			newnode = node.__class__(*fields)
			ast.copy_location(newnode, node)
			# astutils.check_missing_lineno(newnode)

			if isinstance(newnode, ast.Return):
				retval = newnode.value or self.makeName('None')
				newnode = self.makeAssign(returnName, retval)

			return newnode
		else: # python types
			return node

	def canOptimizeFunc(self, func):
		if hasattr(func, '_simplefuncinlining_can_optimize'):
			return func._simplefuncinlining_can_optimize

		canopt = self._canOptimizeFunc(func)
		func._simplefuncinlining_can_optimize = canopt
		return canopt

	def _canOptimizeFunc(self, func):
		assert isinstance(func, ast.FunctionDef)
		if len(func.body) > 10: # too long, ignore
			return False

		if func.args.vararg or func.args.kwarg: # todo: can support vararg and kwargs?
			return False

		for arg in func.args.args:
			if not isinstance(arg, ast.Name): # todo: support pattern matching in arguments
				return False

		if func.decorator_list: # do not support decorators
			return False

		for node in astutils.subnodes_recursive(func.body):
			# todo: support global stmt ?
			if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Lambda, ast.Yield, ast.Global)): # these statements are not supported
				return False

		if not self.isReturnLastStmt(func.body):
			return False

		return True


	def isReturnLastStmt(self, body):
		for i, stmt in enumerate(body):
			if i < len(body)-1:
				if isinstance(stmt, ast.Return) or any(isinstance(ss, ast.Return) for ss in astutils.substmts_recursive(stmt)):
					return False # found Return, but not last stmt
			else:
				# this is the last stmt
				if isinstance(stmt, (ast.For, ast.While, ast.TryExcept, ast.TryFinally)):
					# todo: support 1-level For, While
					return False
				elif isinstance(stmt, ast.If):
					return self.isReturnLastStmt(stmt.body) and self.isReturnLastStmt(stmt.orelse)
				else:
					return True

	def tryDetermineFunction(self, func):
		pvs = self.currentScope.getPotentialValuesOfExpr(func)
		if isinstance(pvs, namescope.FunctionValues):
			funcdef = pvs.getSingleValue()
			if funcdef:
				return funcdef, isinstance(pvs, namescope.BoundedMethodValues)

		return None, False

	def isImmutableDefaultArg(self, expr):
		if isinstance(expr, (ast.Num, ast.Str, ast.Tuple)):
			return True
		elif isinstance(expr, ast.Name):
			return expr.id in consts.CONST_BUILTIN_NAMES
		else:
			return False


