import sys
import ast
import astutils
from itertools import izip

import compileutils
from astop import codegen
from collections import Counter
# from globalanalyze import GlobalAnalyzeVisitor
from constfolding import ConstFoldingASTOptimizer
from funcargsunfolding import FuncArgsUnfoldingASTOptimizer
from simplefuncinlining import SimpleFuncInliningASTOptimizer
from loopunfolding import LoopUnfoldingASTOptimizer
from deadcodeeliminating import DeadCodeEliminatingASTOptimizer


def astoptimize(sources):
	print >>sys.stderr, 'ast optimizeing %d sources ...' % len(sources)
	moduleASTs = [compileutils.compileModuleAST(src) for src in sources]
	for src, module in zip(sources, moduleASTs):
		module.source = src

	print >>sys.stderr, 'All sources compiled, start analyzing ...'
	for moduleAST in moduleASTs:
		analyzeModuleAST(moduleAST)

	print >>sys.stderr, 'Optimizing ASTs ...'
	C = Counter()
	moduleASTs = [optimizeModuleAST( moduleAST, C ) for moduleAST in moduleASTs] # optimize module

	for src, (moduleAST, optimized) in izip( sources, moduleASTs ):
		if not optimized: continue

		# print >>sys.stderr, "%s is optimized in %d places" % (src, optimizeCount)

		# print 'compile AST to code:', code
		optCode = codegen.to_source(moduleAST)
		optCode = '# code optimized by pyastop\n' + optCode

		with open(src  + 'ao', 'wb') as outputfd:
			outputfd.write(optCode)

		checkExprContext(moduleAST)
		astutils.check_missing_lineno(moduleAST)
		code = compile(moduleAST, src, "exec")
		compileutils.writeCodeToPyc(code, src + 'c')

	print >>sys.stderr, "=" * 80
	print >>sys.stderr, 'astop optimized %d places in sources' % sum(C.itervalues())
	for name, c in sorted(C.items()):
		print >>sys.stderr, '\t%s x %d' % (name[:-12], c )

def analyzeModuleAST(moduleAST):
	pass
	# analyzer = GlobalAnalyzeVisitor()
	# analyzer.visit(moduleAST)

def optimizeModuleAST(moduleAST, C):
	optimized = False
	for optimizerClass in (
			ConstFoldingASTOptimizer,
			LoopUnfoldingASTOptimizer,
			FuncArgsUnfoldingASTOptimizer,
			DeadCodeEliminatingASTOptimizer,
			# SimpleFuncInliningASTOptimizer,
	):

		optimizer = optimizerClass()
		print >>sys.stderr, 'Running %s on %s ...' % (optimizerClass.__name__, moduleAST.source)
		optModuleAST = optimizer.visit(moduleAST)
		if optimizer.optimized:
			moduleAST = optModuleAST
			C[optimizerClass.__name__] += optimizer.optimized
			optimized = True

	return moduleAST, optimized

def checkExprContext(node):
	if 'ctx' in node._fields:
		assert node.ctx is not None, ast.dump(node)

	for child in ast.iter_child_nodes(node):
		checkExprContext(child )