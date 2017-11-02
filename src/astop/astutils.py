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

_emptySet = frozenset()
def nameUsageInStmt(stmt):
	if isinstance(stmt, ast.FunctionDef):
		return set([stmt.identifier.id]), namesUsedInExprs(stmt.decorator_list)
	elif isinstance(stmt, ast.ClassDef):
		return set([stmt.identifier.id]), namesUsedInExprs(stmt.bases + stmt.decorator_list)
	elif isinstance(stmt, ast.Return):
		return _emptySet, namesUsedInExpr(stmt.value) if stmt.value is not None else set()
	elif isinstance(stmt, ast.Delete):
		return _emptySet, namesUsedInExprs(stmt.targets)
	elif isinstance(stmt, ast.Assign):
		pass

def namesAssigned(expr):
	pass

def namesUsedInExpr(expr):
	if isinstance(expr, ast.BoolOp):
		return namesUsedInExprs(expr.values)
	elif isinstance(ast.BinOp):
		return namesUsedInExprs([expr.left, expr.right])
	elif isinstance(ast.UnaryOp):
		pass

def namesUsedInExprs(exprs):
	names = set()
	for expr in exprs:
		names |= namesUsedInExpr(expr)
	return names


	# stmt = FunctionDef(identifier name, arguments args,
     #                        stmt* body, expr* decorator_list)
	#       | ClassDef(identifier name, expr* bases, stmt* body, expr* decorator_list)
	#       | Return(expr? value)
    #
	#       | Delete(expr* targets)
	#       | Assign(expr* targets, expr value)
	#       | AugAssign(expr target, operator op, expr value)
    #
	#       -- not sure if bool is allowed, can always use int
 	#       | Print(expr? dest, expr* values, bool nl)
    #
	#       -- use 'orelse' because else is a keyword in target languages
	#       | For(expr target, expr iter, stmt* body, stmt* orelse)
	#       | While(expr test, stmt* body, stmt* orelse)
	#       | If(expr test, stmt* body, stmt* orelse)
	#       | With(expr context_expr, expr? optional_vars, stmt* body)
    #
	#       -- 'type' is a bad name
	#       | Raise(expr? type, expr? inst, expr? tback)
	#       | TryExcept(stmt* body, excepthandler* handlers, stmt* orelse)
	#       | TryFinally(stmt* body, stmt* finalbody)
	#       | Assert(expr test, expr? msg)
    #
	#       | Import(alias* names)
	#       | ImportFrom(identifier? module, alias* names, int? level)
    #
	#       -- Doesn't capture requirement that locals must be
	#       -- defined if globals is
	#       -- still supports use as a function!
	#       | Exec(expr body, expr? globals, expr? locals)
    #
	#       | Global(identifier* names)
	#       | Expr(expr value)
	#       | Pass | Break | Continue
