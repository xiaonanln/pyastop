import sys
from itertools import izip

import compileutils
from astop import codegen
from constfolding import ConstFoldingASTOptimizer
from funcargsunfolding import FuncArgsUnfoldingASTOptimizer
from inlining import InliningASTOptimizer
from loopunfolding import LoopUnfoldingASTOptimizer


def astoptimize(sources):
	print >>sys.stderr, 'ast optimizeing %d sources ...' % len(sources)
	moduleASTs = [compileutils.compileModuleAST(src) for src in sources]

	print >>sys.stderr, 'All sources compiled, start optimizing ...'
	moduleASTs = [optimizeModuleAST( moduleAST ) for moduleAST in moduleASTs] # optimize module

	optimizeCounter = 0
	for src, (moduleAST, optimizeCount) in izip( sources, moduleASTs ):
		if not optimizeCount: continue

		optimizeCounter += optimizeCount
		print >>sys.stderr, "%s is optimized in %d places" % (src, optimizeCount)

		# print 'compile AST to code:', code
		optCode = codegen.to_source(moduleAST)
		optCode = '# code optimized by pyastop\n' + optCode
		with open(src  + 'ao', 'wb') as outputfd:
			outputfd.write(optCode)

		code = compile(moduleAST, src, "exec")
		compileutils.writeCodeToPyc(code, src + 'c')

	print >>sys.stderr, 'astop optimized %d sources' % optimizeCounter

def optimizeModuleAST(moduleAST):
	totalOptimizeCount = 0
	for optimizerClass in (ConstFoldingASTOptimizer,
	                  LoopUnfoldingASTOptimizer,
	                  FuncArgsUnfoldingASTOptimizer,
	                  InliningASTOptimizer):

		optimizer = optimizerClass()
		optModuleAST = optimizer.visit(moduleAST)
		if optimizer.optimized:
			moduleAST = optModuleAST
			totalOptimizeCount += optimizer.optimized

	return moduleAST, totalOptimizeCount
