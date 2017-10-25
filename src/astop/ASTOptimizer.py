import ast
import sys

class ASTOptimizer(ast.NodeTransformer):

	def __init__(self):
		super(ASTOptimizer, self).__init__()
		self._optimized = False

	def visit(self, node):
		"""Visit a node."""
		if hasattr(node, 'lineno'):
			self.currentPos = node

		return super(ASTOptimizer, self).visit(node)

	@property
	def optimized(self):
		return self._optimized

	@optimized.setter
	def optimized(self, v):
		self._optimized = v

	@staticmethod
	def node2str(node):
		if hasattr(node, '_fields'):
			name = node.__class__.__name__
			return name + '<' + ', '.join('%s=%s' % (f, ASTOptimizer.node2str(getattr(node, f))) for f in node._fields) + '>'
		elif isinstance(node, list):
			return [ASTOptimizer.node2str(n) for n in node]
		else:
			return str(node)

	def evalConstExpr(self, expr):
		setStmt = self.makeAssignStmt('_', expr)
		module = ast.Module(body=[setStmt])
		code = compile(module, '<evalExpr>', 'exec')
		G, L = {}, {}
		exec(code, G, L)
		v = L['_']
		# print 'evalConstExpr', type(v), repr(v)
		if isinstance(v, int):
			return self.makeNum(v)
		else:
			assert False, (type(v), v)

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
