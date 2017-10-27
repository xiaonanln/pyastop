import ast

def isnode(node):
	return hasattr(node, '_fields')

def children(node):
	for f in node._fields:
		c = getattr(node, f)
		if isnode(c):
			yield c
		elif isinstance(c, list):
			for x in c:
				yield x
		else:
			yield c

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

def isexpr(node):
	return isinstance(node, (ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Lambda, ast.IfExp, ast.Dict, ast.Set,
	                         ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.Yield, ast.Compare, ast.Call,
	                         ast.Repr, ast.Num, ast.Str, ast.Attribute, ast.Subscript, ast.Name, ast.List, ast.Tuple
	                         ))

def isConstantExpr(expr):
	if isinstance(expr, ast.Num):
		return True
	elif isinstance(expr, ast.Str):
		return True
	elif isinstance(expr, ast.BoolOp):
		return all( isConstantExpr(e) for e in expr.values )
	elif isinstance(expr, ast.BinOp):
		return all( isConstantExpr(e) for e in (expr.left, expr.right) )
	elif isinstance(expr, ast.UnaryOp):
		return isConstantExpr(expr.operand)
	elif isinstance(expr, ast.IfExp):
		return all(isConstantExpr(e) for e in (expr.test, expr.body, expr.orelse))
	elif isinstance(expr, ast.Dict):
		return all(isConstantExpr(e) for e in (expr.keys + expr.values))
	elif isinstance(expr, ast.Set):
		return all(isConstantExpr(e) for e in expr.elts)
	elif isinstance(expr, ast.Compare):
		return all(isConstantExpr(e) for e in [expr.left] + expr.comparators)
	elif isinstance(expr, (ast.List, ast.Tuple)):
		return all(isConstantExpr(e) for e in expr.elts)
	# elif isinstance(expr, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
	# 	# | ListComp(expr elt, comprehension * generators)
	# 	# | SetComp(expr elt, comprehension * generators)
	# 	# | GeneratorExp(expr elt, comprehension * generators)
	# 	return isConstantExpr(expr.elt) and all(isConstComprehension(c) for c in expr.generators)
	# elif isinstance(expr, ast.DictComp):
	# 	# | DictComp(expr key, expr value, comprehension * generators)
	# 	return isConstantExpr(expr.key) and isConstantExpr(expr.value) and all(isConstComprehension(c) for c in expr.generators)

	return False

def isConstComprehension(comp):
	return all(isConstantExpr(e) for e in [comp.target, comp.iter] + comp.ifs)

