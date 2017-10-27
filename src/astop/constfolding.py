
import ast
import astutils
from ASTOptimizer import ASTOptimizer

class ConstFoldingOptimizer(ASTOptimizer):
	def __init__(self):
		super(ConstFoldingOptimizer, self).__init__()

	def optimize(self, node):
		# print 'optimize', ast.dump(node)
		if not astutils.isexpr(node):
			return node, False

		if astutils.isConstantExpr(node) and self.isConstFoldableExpr(node):
			node = self.evalConstExpr(node, ctx=getattr(node, 'ctx', None))
			return node, True
		else:
			return node, False

	def isConstFoldableExpr(self, node):
			return isinstance(node, (ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.IfExp, ast.Compare, ast.Call))

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
