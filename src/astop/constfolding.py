
import ast
from ASTOptimizer import ASTOptimizer

class ConstFoldingOptimizer(ASTOptimizer):
	def __init__(self):
		super(ConstFoldingOptimizer, self).__init__()

	def visit_BoolOp(self, node):
		print 'const folding BoolOp:', self.node2str(node)
		return self.constFoldingBoolOp(node)

	def visit_BinOp(self, node):
		print 'const folding BinOp:', self.node2str(node)
		return self.constFoldingBinOp(node)

	def visit_Num(self, node):
		return node

	def visit_Str(self, node):
		return node

	def constFoldingBoolOp(self, node):
		# BoolOp(boolop op, expr* values)
		node.values = [self.constFoldingExpr(expr) for expr in node.values]
		for expr in node.values:
			if not self.isConstant(expr):
				return node # const folding fialed

		self.optimized = True
		return self.evalConstExpr(node)

	def constFoldingBinOp(self, node):
		# BinOp(expr left, operator op, expr right)
		node.left = self.constFoldingExpr(node.left)
		node.right = self.constFoldingExpr(node.right)
		if not self.isConstant(node.left) or not self.isConstant(node.right):
			return node
		self.optimized = True
		return self.evalConstExpr(node)

	def constFoldingNum(self, node):
		return node

	def constFoldingExpr(self, node):
		type = node.__class__.__name__
		return getattr(self, 'constFolding' + type)(node)

	def isConstant(self, expr):
		if isinstance(expr, ast.Num):
			return True
		elif isinstance(expr, ast.Str):
			return True

		return False

	# expr = BoolOp(boolop op, expr* values)
	#      | BinOp(expr left, operator op, expr right)
	#      | UnaryOp(unaryop op, expr operand)
	#      | Lambda(arguments args, expr body)
	#      | IfExp(expr test, expr body, expr orelse)
	#      | Dict(expr* keys, expr* values)
	#      | Set(expr* elts)
	#      | ListComp(expr elt, comprehension* generators)
	#      | SetComp(expr elt, comprehension* generators)
	#      | DictComp(expr key, expr value, comprehension* generators)
	#      | GeneratorExp(expr elt, comprehension* generators)
	#      -- the grammar constrains where yield expressions can occur
	#      | Yield(expr? value)
	#      -- need sequences for compare to distinguish between
	#      -- x < 4 < 3 and (x < 4) < 3
	#      | Compare(expr left, cmpop* ops, expr* comparators)
	#      | Call(expr func, expr* args, keyword* keywords,
	# 		 expr? starargs, expr? kwargs)
	#      | Repr(expr value)
	#      | Num(object n) -- a number as a PyObject.
	#      | Str(string s) -- need to specify raw, unicode, etc?
	#      -- other literals? bools?
	#
	#      -- the following expression can appear in assignment context
	#      | Attribute(expr value, identifier attr, expr_context ctx)
	#      | Subscript(expr value, slice slice, expr_context ctx)
	#      | Name(identifier id, expr_context ctx)
	#      | List(expr* elts, expr_context ctx)
	#      | Tuple(expr* elts, expr_context ctx)
	#
	#       -- col_offset is the byte offset in the utf8 string the parser uses
	#       attributes (int lineno, int col_offset)
