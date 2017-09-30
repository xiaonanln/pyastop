import sys
import ast
import time
import py_compile
import codegen
import marshal
from itertools import izip
from collections import Counter

import compileutils

def astoptimize(sources):
	print >>sys.stderr, 'ast optimizeing %d sources ...' % len(sources)
	moduleASTs = [compileutils.compileModuleAST(src) for src in sources]

	print >>sys.stderr, 'All sources compiled, start optimizing ...'
	moduleASTs = [optimizeModuleAST( moduleAST ) for moduleAST in moduleASTs] # optimize module

	optimizeCounter = 0
	for src, (moduleAST, optimized) in izip( sources, moduleASTs ):
		if not optimized: continue

		optimizeCounter += 1
		print >>sys.stderr, "%s is optimized!" % src

		# print 'compile AST to code:', code
		optCode = codegen.to_source(moduleAST)
		optCode = '# code optimized by pyastop\n' + optCode
		with open(src  + 'astop', 'wb') as outputfd:
			outputfd.write(optCode)

		code = compile(moduleAST, src, "exec")
		compileutils.writeCodeToPyc(code, src + 'c')

	print >>sys.stderr, 'astop optimized %d sources' % optimizeCounter

def optimizeModuleAST(moduleAST):
	optimizer = ModuleASTOptimizer()
	optModuleAST = optimizer.visit(moduleAST)
	return optModuleAST if optimizer.optimized else moduleAST, optimizer.optimized


class ModuleASTOptimizer(ast.NodeTransformer):

	def __init__(self):
		super(ModuleASTOptimizer, self).__init__()
		self.currentPos = None
		self.optimizeCounter = Counter()

	@property
	def optimized(self):
		return len(self.optimizeCounter) > 0

	def visit(self, node):
		"""Visit a node."""
		if hasattr(node, 'lineno'):
			self.currentPos = node

		return super(ModuleASTOptimizer, self).visit(node)

	def visit_For(self, node):
		# print >>sys.stderr, 'For', 'target', node.target, 'iter', node.iter, 'orelse', node.orelse
		optNode = self.optimizeFor(node)
		if optNode:
			self.optimizeCounter['For'] += 1
		return optNode or node

	def optimizeFor(self, node):
		# ast.For
		# if node.orelse is not None:
		if node.orelse: # if For has orelse, we can not optimize it
			return

		if self.containsStmt(lambda x: self.isBreakStmt(x) or self.isContinueStmt(x), node.body ):
			# can not optimize if For body contains continue or break
			return

		expandIter = self.expandIterExpr(node.iter)
		if expandIter is None:
			return

		if len(expandIter) > 10:
			return

		print >>sys.stderr, 'Itering on %s' % expandIter
		newBody = []
		for iterVal in expandIter:
			# print >>sys.stderr, 'assigning', iterVal
			assign = self.makeAssignStmt(node.target, iterVal)
			newBody.append(assign)
			newBody += node.body
		return newBody

	def makeExpr(self, pyval):
		if hasattr(pyval, 'lineno') and hasattr(pyval, 'col_offset'):
			return pyval

		if isinstance(pyval, (int, float)):
			return self._setCurrentPos(ast.Num(n=pyval))

		assert False, (pyval, dir(pyval))

	def dump(self, node):
		print >>sys.stderr, '>>> DUMP', node, ', '.join('%s=%s' % (f, getattr(node, f)) for f in node._fields)

	def expandIterExpr(self, iter):
		# self.dump(iter)
		if isinstance(iter, ast.Call):
			# self.dump(iter.func)
			if self.isNameEquals(iter.func, 'range') or self.isNameEquals(iter.func, 'xrange'):
				iter = self.tryEvalExpr(iter)
				if iter is None: # can we eval iter?
					return
				return [self.makeExpr(v) for v in iter]

		elif isinstance(iter, (ast.List, ast.Tuple, ast.Set)):
			return iter.elts
		elif isinstance(iter, ast.Dict):
			return iter.keys

		return None

	def visit_stmt(self, stmt):
		print >>sys.stderr, 'current stmt:', stmt

	def tryEvalExpr(self, expr):
		setStmt = self.makeAssignStmt('_', expr)
		module = ast.Module(body=[setStmt])
		code = compile(module, '<evalExpr>', 'exec')

		G, L = {}, {}
		try:
			exec(code, G, L)
		except NameError:
			return None # can not resolve names in expression
		except:
			print >>sys.stderr, 'Eval expr failed: %s' % expr
			raise

		return L['_']

	def makeAssignStmt(self, name, expr):
		if isinstance(name, str):
			name = self.makeName(name, ast.Store())

		assignStmt = ast.Assign(targets=[name], value=expr)
		return self._setCurrentPos(assignStmt)

	def makeName(self, id, ctx):
		assert isinstance(id, str)
		name = ast.Name(id=id, ctx=ctx)
		return self._setCurrentPos(name)

	def isNameEquals(self, node, name):
		if isinstance(name, ast.Name):
			name = name.id

		return isinstance(node, ast.Name) and node.id == name

	def _setCurrentPos(self, node):
		if self.currentPos is not None:
			node.lineno = self.currentPos.lineno
			node.col_offset = self.currentPos.col_offset
		else:
			node.lineno = node.col_offset = 0

		return node

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

