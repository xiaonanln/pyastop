import ast
import astutils
import consts
import __builtin__

class PotentialValues(object):
	def __init__(self, *values):
		if values:
			self.values = set(values)
			self.canBeAnyValue = False
		else:
			self.values = None
			self.canBeAnyValue = True

	def setCanBeAnyValue(self):
		self.canBeAnyValue = True
		self.values = None # values not useful anymore

	def getSingleValue(self):
		if self.canBeAnyValue: return None
		if len(self.values) != 1: return None
		return list(self.values)[0]

	def merge(self, otherValues):
		if isinstance(self, AnyValue):
			return self # AnyValue merge other => AnyValue
		elif isinstance(otherValues, AnyValue):
			return otherValues # ... merge AnyValue => AnyValue
		elif isinstance(self, MultipleTypeValues):
			self.addValues(otherValues)
			return self
		elif isinstance(otherValues, MultipleTypeValues):
			otherValues.addValues(self)
			return otherValues
		elif self.__class__ is otherValues.__class__:
			# values of same class, merge them
			if self.canBeAnyValue or otherValues.canBeAnyValue:
				return self.__class__() # any value + ... = any value
			else:
				return self.__class__(*(self.values | otherValues.values))
		else:
			return MultipleTypeValues( self, otherValues )

	def __str__(self):
		return "%s<%s>" % (
			self.__class__.__name__,
			"any" if self.canBeAnyValue else "|".join(map(str, self.values))
		)

class MultipleTypeValues(PotentialValues):
	def __init__(self, *values):
		assert values, 'values should not be empty'
		for value in values:
			assert isinstance(value, PotentialValues) and not isinstance(value, MultipleTypeValues) # do not be recursive
		self.values = values

	def addValues(self, values):
		assert isinstance(values, PotentialValues)
		if isinstance(values, MultipleTypeValues):
			for _values in values.values:
				self.addValues(_values)
		else:
			for existingValues in self.values:
				foundSameClass = False
				if existingValues.__class__ is values.__clas__: # merge same type
					self.values.remove(existingValues)
					self.values.add( existingValues.merge(values) )
					foundSameClass = True
					break

				if not foundSameClass:
					self.values.add( values )

class AnyValue(PotentialValues): pass
anyValue = AnyValue()

class UnresolvedName(PotentialValues): pass
unresolvedName = UnresolvedName

class NumValues(PotentialValues): pass
class StrValues(PotentialValues): pass
class TupleValues(PotentialValues): pass
class ListValues(PotentialValues): pass
class SetValues(PotentialValues): pass
class DictValues(PotentialValues): pass
class ModuleValues(PotentialValues):
	def __init__(self):
		super(ModuleValues, self).__init__()

anyModule = ModuleValues()

class BuiltinValues(PotentialValues): pass

class FunctionValues(PotentialValues):
	def __init__(self, node):
		assert isinstance(node, ast.FunctionDef)
		super(FunctionValues, self).__init__(node)

class UnboundedMethodValues(FunctionValues): pass
class BoundedMethodValues(FunctionValues): pass

class ClassValues(PotentialValues):
	def __init__(self, node):
		assert isinstance(node, ast.ClassDef)
		super(ClassValues, self).__init__(node)

class ClassInstanceValues(PotentialValues):
	def __init__(self, classnode, *values):
		assert isinstance(classnode, ast.ClassDef)
		self.classnode = classnode
		super(ClassInstanceValues, self).__init__(*values)

	def __str__(self):
		return "%s<%s:%s>" % (
			self.__class__.__name__,
			self.classnode.name,
			"any" if self.canBeAnyValue else "|".join(map(str, self.values))
		)

class NameScope(object):
	def __init__(self, node, parent):
		if node is not None:
			assert isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))

		self.node = node
		if node is not None:
			node.scope = self # ndoe -> scope
		self.parent = parent
		self.globals = set()
		self.locals = {}

	def isNameResolved(self, name):
		if name in self.globals:
			globalScope = self.getGlobalScope()
			return globalScope and globalScope.isNameResolved(name)

		while self:
			if name in self.locals:
				return True

	def addGlobalName(self, name):
		assert isinstance(name, str), name
		assert name not in self.locals, 'SyntaxError: %s is local and global' % name
		self.globals.add(name)

	def isGlobalScope(self):
		return self.parent == builtinsNameScope

	def isBuiltinsScope(self):
		return self == builtinsNameScope

	def getGlobalScope(self):
		while self and not self.isGlobalScope():
			self = self.parent

		return self # find the global scope or None if not found

	def visitModuleBody(self, node, res):
		assert node, ast.Module
		# let all stmts add names to the local scope
		for stmt in node.body:
			self.visitStmt(stmt, res)

	def visitStmt(self, stmt, res):
		if isinstance(stmt, ast.FunctionDef):
			self.onAssignName(stmt.name, FunctionValues(stmt)) # value can be a FucntionDef
			funcScope = NameScope(stmt, self)
			res[stmt] = funcScope
			funcScope.visitFunctionBody(stmt, res)

		elif isinstance(stmt, ast.ClassDef):
			self.onAssignName(stmt.name, ClassValues(stmt))  # value can be a ClassDef
			classScope = NameScope(stmt, self)
			res[stmt] = classScope
			classScope.visitClassBody(stmt, res )

		elif isinstance(stmt, ast.Assign):
			if len(stmt.targets) == 1:
				self.visitAssignedNameInExpr(stmt.targets[0], stmt.value)
			else:
				assert False, "I don't know what kind of code compiles to this AST node"
				self.visitAssignedNameInExpr(ast.Tuple(stmt.targets, ast.Store()), stmt.value) # convert to tuple assign ... is it correct ?
		elif isinstance(stmt, ast.Delete):
			for expr in stmt.targets:
				self.visitAssignedNameInExpr(expr, unresolvedName)
		elif isinstance(stmt, ast.AugAssign):
			self.visitAssignedNameInExpr(stmt.target, ast.BinOp(stmt.target, stmt.op, stmt.value)) # target op= value ==> target = target op value
		elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
			for alias in stmt.names:
				self.visitAssignedNamesInAlias(alias, anyModule)

	def visitAssignedNameInExpr(self, expr, value):
		if isinstance(expr, (ast.Attribute, ast.Subscript)):
			pass
		elif isinstance(expr, (ast.List, ast.Tuple)):
			if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
				for i, exp in enumerate(expr.elts):
					self.visitAssignedNameInExpr(exp, value.elts[i])
			else:
				for exp in expr.elts:
					self.visitAssignedNameInExpr(exp, anyValue)
		elif isinstance(expr, ast.Name):
			if not isinstance(value, PotentialValues):
				pv = self.expr2pvs(value)
				# print 'potential value of %s ==> %s' % (ast.dump(value), pv)
			else:
				pv = value # if value is PotentialValues, just keep it
			self.onAssignName(expr, pv)
		else:
			assert False, ('should not assign', ast.dump(expr))

	def visitAssignedNamesInAlias(self, alias, value):
		assert isinstance(alias, ast.alias), repr(alias)
		if alias.asname:
			self.onAssignName(alias.asname, value)

	def expr2pvs(self, expr):
		if isinstance(expr, ast.Num):
			return NumValues(expr.n)
		elif isinstance(expr, ast.Str):
			return StrValues(expr.s)
		elif isinstance(expr, (ast.List, ast.ListComp)):
			return ListValues()
		elif isinstance(expr, (ast.Set, ast.SetComp)):
			return SetValues()
		elif isinstance(expr, (ast.Dict, ast.DictComp)):
			return DictValues()
		elif isinstance(expr, ast.Tuple):
			return TupleValues()
		elif isinstance(expr, ast.Name):
			# assigning name will transfer values of this name, but since names can be assigned
			return anyValue # todo: implement the transfer of values of name
		else:
			return anyValue # others are not supported yet

		return anyValue

	def visitGlobalStmt(self, stmt):
		if isinstance(stmt, ast.Global):
			for name in stmt.names:
				self.addGlobalName(name)

	def visitFunctionBody(self, node, res):
		assert node, ast.FunctionDef

		# print 'visitFunctionBody', node.name,  ast.dump(node.args)
		# arguments = (expr * args, identifier? vararg, identifier? kwarg, expr * defaults)
		# parse arguments first, and arguments are treated as locals
		for i, arg in enumerate(node.args.args):
			argValues = anyValue
			if i == 0 and isinstance(self.parent.node, ast.ClassDef):
				functype = self.parent.getFunctionType(node)
				if functype == 'instancemethod':
					# first argument of a instancemethod is self
					argValues = ClassInstanceValues(self.parent.node) # self can be any instance of this class
				elif functype == 'classmethod':
					# first argument of a classmethod is the class
					argValues = ClassValues(self.parent.node)
			self.visitAssignedNameInExpr(arg, argValues)

		if node.args.vararg: # f(*args)
			self.onAssignName(node.args.vararg, TupleValues()) # args can be any tuple

		if node.args.kwarg:
			self.onAssignName(node.args.kwarg, DictValues()) # kwarg can be any dict

		# find all global names first
		for stmt in node.body:
			self.visitGlobalStmt(stmt)

		# print 'globals of %s is %s' % (node.name, self.globals)

		# let all stmts add names to the local scope
		for stmt in node.body:
			self.visitStmt(stmt, res)

	def getFunctionType(self, node):
		"""Get the type of a function, which can be function | instancemethod | classmethod | staticmethod"""
		assert isinstance(node, ast.FunctionDef)
		if self.isGlobalScope():
			return 'function'

		for deco in node.decorator_list:
			if isinstance(deco, ast.Name):
				if deco.id == 'staticmethod' and self.isBuiltinName(deco):
					return 'staticmethod'
				elif deco.id == 'classmethod' and self.isBuiltinName(deco):
					return 'classmethod'

		return 'instancemethod'

	def visitClassBody(self, node, res):
		assert node, ast.ClassDef
		# let all stmts add names to the local scope
		for stmt in node.body:
			self.visitStmt(stmt, res)

	def onAssignName(self, name, value):
		"""called when name is assigned"""
		assert isinstance(name, (ast.Name, str)), repr(name)
		if isinstance(name, ast.Name):
			assert isinstance(name.ctx, (ast.Store, ast.Del, ast.Param)), (name.id, name.ctx)
			name = name.id

		if name in self.globals:
			# assign to global ...
			globalScope = self.getGlobalScope()
			assert globalScope, 'can not get global scope'
			globalScope.onAssignName(name, value)
			return

		assert isinstance(value, PotentialValues)
		if name not in self.locals:
			self.locals[name] = value
		else:
			oldValues = self.locals[name]
			self.locals[name] = oldValues.merge(value)
			# print 'merge %s, %s => %s' % (oldValues, value, self.locals[name])

		# if not (name.startswith('__') and name.endswith('__')):
			# print 'name %s can be %s' % (name, self.locals[name])

	def isConstantExpr(self, expr):
		if isinstance(expr, ast.Num):
			return True
		elif isinstance(expr, ast.Str):
			return True
		elif isinstance(expr, ast.BoolOp):
			return all( self.isConstantExpr(e) for e in expr.values )
		elif isinstance(expr, ast.BinOp):
			return all( self.isConstantExpr(e) for e in (expr.left, expr.right) )
		elif isinstance(expr, ast.UnaryOp):
			return self.isConstantExpr(expr.operand)
		elif isinstance(expr, ast.IfExp):
			return all(self.isConstantExpr(e) for e in (expr.test, expr.body, expr.orelse))
		elif isinstance(expr, ast.Dict):
			return all(self.isConstantExpr(e) for e in (expr.keys + expr.values))
		elif isinstance(expr, ast.Set):
			return all(self.isConstantExpr(e) for e in expr.elts)
		elif isinstance(expr, ast.Compare):
			return all(self.isConstantExpr(e) for e in [expr.left] + expr.comparators)
		elif isinstance(expr, (ast.List, ast.Tuple)):
			return all(self.isConstantExpr(e) for e in expr.elts)
		elif isinstance(expr, ast.Call):
			# Call(expr func, expr * args, keyword * keywords, expr? starargs, expr? kwargs)
			# keyword = (identifier arg, expr value)
			return self.isCallArgumentsConst(expr) and self.isConstToConstFunc(expr.func)
		elif isinstance(expr, ast.Name):
			return expr.id in  consts.CONST_BUILTIN_NAMES

		# elif isinstance(expr, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
		# 	# | ListComp(expr elt, comprehension * generators)
		# 	# | SetComp(expr elt, comprehension * generators)
		# 	# | GeneratorExp(expr elt, comprehension * generators)
		# 	return self.isConstantExpr(expr.elt) and all(isConstComprehension(c) for c in expr.generators)
		# elif isinstance(expr, ast.DictComp):
		# 	# | DictComp(expr key, expr value, comprehension * generators)
		# 	return self.isConstantExpr(expr.key) and self.isConstantExpr(expr.value) and all(isConstComprehension(c) for c in expr.generators)

		return False

	def isCallArgumentsConst(self, call):
		assert isinstance(call, ast.Call)
		if any(not self.isConstantExpr(arg) for arg in call.args):
			return False

		if any(not self.isConstantExpr(kw.value) for kw in call.keywords):
			return False

		if call.starargs and not self.isConstantExpr(call.starargs):
			return False

		if call.kwargs and not self.isConstantExpr(call.kwargs):
			return False

		return True

	def isConstToConstFunc(self, expr):
		# print 'isConstToConstFunc', ast.dump(expr), isinstance(expr, ast.Name), expr.id in consts.CONST_TO_CONST_BUILTIN_FUNCS, self.isBuiltinName(expr.id )
		if not isinstance(expr, ast.Name): return False
		funcName = expr.id
		return funcName in consts.CONST_TO_CONST_BUILTIN_FUNCS and self.isBuiltinName(funcName)

	def isLocalName(self, name):
		assert isinstance(name, str)
		return name in self.locals

	def isGlobalName(self, name):
		assert isinstance(name, str)
		scope = self
		while scope:
			if name in scope.locals:
				return self.isGlobalScope()
			elif name in scope.globals:
				return True

			scope = scope.parent

	def isBuiltinName(self, name):
		assert isinstance(name, str)
		scope = self
		while scope:
			if name in scope.locals:
				return scope.isBuiltinsScope()
			elif name in scope.globals:
				return False
			scope = scope.parent

		return False

	def getPotentialValuesOfExpr(self, expr):
		if isinstance(expr, ast.Name):
			return self.getPotentialValues(expr.id)
		elif isinstance(expr, ast.Attribute):
			valuePvs = self.getPotentialValuesOfExpr(expr.value)
			# now calculate value.attr
			# print 'getPotentialValuesOfExpr', ast.dump(expr.value), valuePvs, expr.attr
			if isinstance(valuePvs, ClassInstanceValues):
				# value is an instance of a class, so value.attr can be a function
				classdef = valuePvs.classnode
				pvs = classdef.scope.getPotentialValues(expr.attr)
				if isinstance(pvs, FunctionValues):
					funcdef  = pvs.getSingleValue()
					if funcdef:
						functype = self.getFunctionType(funcdef)
						if functype == 'instancemethod':
							return BoundedMethodValues(funcdef)
						elif functype == 'classmethod':
							return BoundedMethodValues(funcdef)
						else:
							return FunctionValues(funcdef)
			# get the method ?
			elif isinstance(valuePvs, ClassValues) and valuePvs.canBeAnyValue and len(valuePvs.values) == 1:
				classdef = list(valuePvs.values)[0]
				pvs = classdef.scope.getPotentialValues(expr.attr)
				if isinstance(pvs, FunctionValues):
					funcdef  = pvs.getSingleValue()
					if funcdef:
						functype = self.getFunctionType(funcdef)
						if functype == 'instancemethod':
							return UnboundedMethodValues(funcdef)
						elif functype == 'classmethod':
							return BoundedMethodValues(funcdef)
						else:
							return FunctionValues(funcdef)

		return anyValue

	def getPotentialValues(self, name):
		if isinstance(name, ast.Name):
			name = name.id
		assert isinstance(name, str), repr(name)

		if name in self.globals:
			globalScope = self.getGlobalScope()
			return globalScope.getPotentialValues(name)

		while self:
			if name in self.locals:
				return self.locals[name]

		# name not found ? that should not be happening
		assert False, 'name %s not defined' % name

builtinsNameScope = NameScope(None, None)
for k in consts.BUILTIN_NAMES:
	if k.startswith('_'):
		builtinsNameScope.onAssignName(k, anyValue)
	else:
		builtinsNameScope.onAssignName(k, BuiltinValues(getattr(__builtin__, k)))

for k, v in builtinsNameScope.locals.iteritems():
	print "BUILTIN %s = %s" % (k, v)

def newGlobalNameScope(module):
	assert isinstance(module, ast.Module)
	scope = NameScope(module, builtinsNameScope)
	for k in ['__builtins__', '__doc__', '__name__', '__package__']:
		scope.onAssignName(k, anyValue)
	return scope

def genNameScopes(node):
	assert isinstance(node, ast.Module)
	nameScopes = {}
	globalScope = newGlobalNameScope(node)
	nameScopes[node] = globalScope
	globalScope.visitModuleBody(node, nameScopes)
	return nameScopes




