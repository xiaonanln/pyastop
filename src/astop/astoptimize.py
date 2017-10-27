import sys
import ast
import time
import py_compile
import codegen
import marshal
from itertools import izip
from collections import Counter

from constfolding import ConstFoldingASTOptimizer
from loopunfolding import LoopUnfoldingASTOptimizer
from inlining import InliningASTOptimizer

import compileutils

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
	cfopter = ConstFoldingASTOptimizer()
	optModuleAST = cfopter.visit(moduleAST)
	moduleAST = optModuleAST if cfopter.optimized else moduleAST

	maopter = LoopUnfoldingASTOptimizer()
	optModuleAST = maopter.visit(moduleAST)
	moduleAST = optModuleAST if maopter.optimized else moduleAST

	inopter = InliningASTOptimizer()
	optModuleAST = inopter.visit(moduleAST)
	moduleAST = optModuleAST if inopter.optimized else moduleAST

	return moduleAST, cfopter.optimized + maopter.optimized + inopter.optimized
