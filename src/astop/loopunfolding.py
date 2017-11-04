import ast
import sys
import astutils
from collections import Counter
from BaseASTOptimizer import BaseASTOptimizer


class LoopUnfoldingASTOptimizer(BaseASTOptimizer):

	CONST_FOLDABLE_BUILTIN_FUNCS = ('xrange', 'frozenset', 'reversed')
	RequireNameScope = True

	def __init__(self):
		super(LoopUnfoldingASTOptimizer, self).__init__()

	def optimize(self, node):
		if not isinstance(node, ast.For):
			return node, False

		optNode = self.optimizeFor(node)
		if not optNode:
			return node, False

		return optNode, True

	def optimizeFor(self, node):
		# ast.For
		# if node.orelse is not None:
		if node.orelse: # if For has orelse, we can not optimize it
			return

		if self.containsStmt(lambda x: self.isBreakStmt(x) or self.isContinueStmt(x), node.body ):
			# can not optimize if For body contains continue or break
			return

		expandIter, ok = self.expandIterExpr(node.iter)

		if not ok:
			return

		# print [ast.dump(it) for it in expandIter]
		if len(expandIter) > 10:
			return

		newBody = []
		for iterVal in expandIter:
			# print >>sys.stderr, 'assigning', iterVal
			assign = self.makeAssignStmt(node.target, iterVal)
			newBody.append(assign)
			newBody += node.body

		return newBody

	def expandIterExpr(self, iter):
		# print 'expandIterExpr', ast.dump(iter)
		# self.dump(iter)
		if isinstance(iter, ast.Call):
			func = iter.func
			if isinstance(func, ast.Name) and func.id in LoopUnfoldingASTOptimizer.CONST_FOLDABLE_BUILTIN_FUNCS and self.currentScope.isBuiltinName(func.id) and self.currentScope.isCallArgumentsConst(iter):
				# xrange, frozenset, reversed
				estIterLen, ok = self.estimateIterLen(iter)
				if ok and estIterLen > 10: # estimate the length of xrange, so as to avoid unnecessary calculating list(xrange(...))
					return None, False

				_list = self.evalConstExpr(ast.Call(self.makeName('list'), [iter], [], None, None))
				return _list.elts, True

		elif isinstance(iter, (ast.List, ast.Tuple, ast.Set)):
			return iter.elts, True
		elif isinstance(iter, ast.Dict):
			return iter.keys, True
		elif isinstance(iter, ast.Str):
			return [ast.Str(c) for c in iter.s], True

		return None, False

	def estimateIterLen(self, iter):
		if isinstance(iter, ast.Call):
			func = iter.func
			if func.id == 'xrange':
				return self.estimateXrangeLen(iter)
			elif func.id == 'reversed':
				arg0, ok = astutils.getcallarg0(iter)
				if ok and arg0 is not None:
					return self.estimateIterLen(arg0)  # len(reversed(...)) == len(...)
			elif func.id == 'frozenset':
				arg0, ok = astutils.getcallarg0(iter)
				if ok:
					if arg0 is None:
						return 0 # frozenset()
					else:
						return self.estimateIterLen(arg0) # len(frozenset(...)) <= len(...)
			else:
				assert False, ast.dump(iter)
		elif isinstance(iter, (ast.List, ast.Tuple, ast.Set)):
			return len(iter.elts), True
		elif isinstance(iter, ast.Dict):
			return len(iter.keys), True
		elif isinstance(iter, ast.Str):
			return len(iter.s), True

		# estimate iter len failed
		return None, False

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


