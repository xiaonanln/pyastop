# -*- coding: utf8 -*-

import sys
import ast
import time
import marshal
import py_compile

def compileModuleAST(filename):
	print >>sys.stderr, 'compiling %s ...' % filename
	with open(filename) as srcfd:
		srcCode = srcfd.read()

	moduleAST = ast.parse(srcCode, filename)
	return moduleAST

def writeCodeToPyc(codeobj, outputFilename):
	with open(outputFilename, 'wb') as fc:
		fc.write('\0\0\0\0')
		py_compile.wr_long(fc, long(time.time()))
		marshal.dump(codeobj, fc)
		fc.flush()
		fc.seek(0, 0)
		fc.write(py_compile.MAGIC)
