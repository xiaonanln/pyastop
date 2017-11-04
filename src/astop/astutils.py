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

def subexprs(expr):
	if isinstance(expr, ast.BoolOp):
		return expr.values
	elif isinstance(expr, ast.BinOp):
		return [expr.left, expr.right]
	elif isinstance(expr, ast.UnaryOp):
		return [expr.operand]
	elif isinstance(ast.Lambda):
		pass

def isexpr(node):
	return isinstance(node, (ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Lambda, ast.IfExp, ast.Dict, ast.Set,
	                         ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.Yield, ast.Compare, ast.Call,
	                         ast.Repr, ast.Num, ast.Str, ast.Attribute, ast.Subscript, ast.Name, ast.List, ast.Tuple
	                         ))

# def isConstComprehension(comp):
# 	return all(isConstantExpr(e) for e in [comp.target, comp.iter] + comp.ifs)

def evalLen(expr):
	if isinstance(expr, (ast.List, ast.Tuple, ast.Set)):
		return len(expr.elts), True
	elif isinstance(expr, ast.Dict):
		return len(expr.keys), True

	return None, False

def substmts(stmt):
	"""Get all direct sub statements"""
	if isinstance(stmt, (ast.Module, ast.Interactive, ast.Suite, ast.ClassDef, ast.For, ast.While, ast.If, ast.TryExcept, ast.TryFinally, ast.ExceptHandler)):
		for ss in stmt.body:
			yield ss

	if isinstance(stmt, (ast.For, ast.While, ast.If, ast.TryExcept)):
		for ss in stmt.orelse:
			yield ss

	if isinstance(stmt, ast.TryFinally):
		for ss in stmt.finalbody:
			yield ss

	return

def getcallarg0(call):
	assert isinstance(call, ast.Call)
	if call.args:
		return call.args[0], True
	elif call.starargs: # can not parse starargs yet
		return None, False
	elif not call.keywords and not call.kwargs:
		# call has no argument
		return None, True
