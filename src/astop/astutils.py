import ast
from collections import Counter

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

def subexprs(node):
	for subnode in ast.iter_child_nodes(node):
		if isinstance(subnode, ast.expr):
			yield subnode

def isexpr(node):
	return isinstance(node, ast.expr)

def isSideEffectFreeExpr(expr):
	assert isinstance(expr, ast.expr)
	if isinstance(expr, (ast.Name, ast.Num, ast.Str)): # these expr is side-affect free
		return True

	if isinstance(expr, (ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.IfExp, ast.Dict, ast.Set, ast.Compare, ast.Repr, ast.List, ast.Tuple)):
		# these exprs are side-affect free if sub-exprs are all side-effect free
		for subexpr in subexprs(expr):
			if not isSideEffectFreeExpr(subexpr):
				return False
		return True

	return False

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
	if isinstance(stmt, list):
		for ss in stmt:
			yield ss

	if isinstance(stmt, (ast.Module, ast.Interactive, ast.Suite, ast.ClassDef, ast.FunctionDef, ast.For, ast.While, ast.If, ast.TryExcept, ast.TryFinally)):
		for ss in stmt.body:
			yield ss

	if isinstance(stmt, ast.TryExcept):
		for handler in stmt.handlers:
			# ExceptHandler(expr? type, expr? name, stmt* body)
			for ss in handler.body:
				yield ss

	if isinstance(stmt, (ast.For, ast.While, ast.If, ast.TryExcept)):
		for ss in stmt.orelse:
			yield ss

	if isinstance(stmt, ast.TryFinally):
		for ss in stmt.finalbody:
			yield ss

	return

def substmtlists(stmt):
	assert isinstance(stmt, ast.stmt)

	if isinstance(stmt, (ast.Module, ast.Interactive, ast.Suite, ast.ClassDef, ast.FunctionDef, ast.For, ast.While, ast.If, ast.TryExcept, ast.TryFinally)):
		yield stmt.body

	if isinstance(stmt, ast.TryExcept):
		for handler in stmt.handlers:
			# ExceptHandler(expr? type, expr? name, stmt* body)
			yield handler.body

	if isinstance(stmt, (ast.For, ast.While, ast.If, ast.TryExcept)):
		yield stmt.orelse

	if isinstance(stmt, ast.TryFinally):
		yield stmt.finalbody

	return

def substmts_recursive(body):
	for ss in substmts(body):
		for _ss in substmts_recursive(ss):
			yield _ss
		yield ss

def subnodes_recursive(node):
	if isinstance(node, list):
		for sn in node:
			for ssn in ast.iter_child_nodes(sn):
				yield ssn
			yield sn

		return

	for sn in ast.iter_child_nodes(node):
		for ssn in subnodes_recursive(sn):
			yield ssn
		yield sn

def getcallarg0(call):
	assert isinstance(call, ast.Call)
	if call.args:
		return call.args[0], True
	elif call.starargs: # can not parse starargs yet
		return None, False
	elif not call.keywords and not call.kwargs:
		# call has no argument
		return None, True

def copy_node(node):
	fields = tuple(getattr(node, k) for k in node._fields)
	newnode = node.__class__(*fields)
	ast.copy_location(newnode, node)
	return newnode

def getAssignedNames(expr):
	if isinstance(expr, ast.Name):
		yield expr
	elif isinstance(expr, (ast.List, ast.Tuple)):
		for subexp in expr.elts:
			for name in getAssignedNames(subexp):
				yield name

def check_missing_lineno(node):
	if not isinstance(node, ast.AST):
		return

	if isinstance(node, (ast.expr, ast.stmt, ast.excepthandler)):
		assert hasattr(node, 'lineno') and hasattr(node, 'col_offset'), ast.dump(node)

	for child in ast.iter_child_nodes(node):
		check_missing_lineno(child)

def analyzeStmtNameUsage(stmt):
	assert isinstance(stmt, ast.stmt)

	C1, C2 = Counter(), Counter()
	if isinstance(stmt, ast.Assign):
		for target in stmt.targets:
			# c1, c2 = analyzeExprNameUsage(expr)
			pass

	elif isinstance(stmt, ast.AugAssign):
		pass
	else:
		# for other stmts, just analyze all subexprs
		for expr in subexprs(stmt):
			c1, c2 = analyzeExprNameUsage(expr)
			C1 += c1
			C2 += c2

def analyzeExprNameUsage(expr):
	assert isinstance(expr, ast.expr)

def isNameReferenced(name, node):
	assert isinstance(name, basestring)
	if isinstance(node, ast.Name) and node.id == name:
		return True

	for subnode in subnodes_recursive(node):
		if isinstance(subnode, ast.Name) and subnode.id == name:
			return True

	return False
