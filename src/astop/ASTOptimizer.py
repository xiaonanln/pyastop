import ast
import sys
import astutils

class ASTOptimizer(ast.NodeTransformer):

	def __init__(self):
		super(ASTOptimizer, self).__init__()
		self._optimized = 0

	def visit(self, node):
		"""Visit a node."""
		assert node is not None, node
		self.currentPos = node

		self.generic_visit(node)
		node, optimized = self.optimize(node)
		assert node is not None
		if optimized: self._optimized += 1
		return node

	def optimize(self, node):
		return node, False

	@property
	def optimized(self):
		return self._optimized

	@staticmethod
	def node2str(node):
		if hasattr(node, '_fields'):
			name = node.__class__.__name__
			return name + '<' + ', '.join('%s=%s' % (f, ASTOptimizer.node2str(getattr(node, f))) for f in node._fields) + '>'
		elif isinstance(node, list):
			return [ASTOptimizer.node2str(n) for n in node]
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
		else:
			node.lineno = node.col_offset = 0

		return node

	def py2ast(self, v, ctx=None):
		node = ASTOptimizer._py2ast(v, ctx)
		self._setCurrentPos(node)
		ast.fix_missing_locations(node)
		return node

	@staticmethod
	def _py2ast(v, ctx):
		if isinstance(v, (int, long, float)):
			return ast.Num(v)
		elif isinstance(v, str):
			return ast.Str(v)
		elif isinstance(v, list):
			return ast.List([ASTOptimizer._py2ast(x, ctx) for x in v], ctx)
		else:
			assert False, ('_py2ast', v)
