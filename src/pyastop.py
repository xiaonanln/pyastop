# -*- coding: utf8 -*-

import argparse
import sys
import astop
import os
import ast
from astop import codegen

# c = ast.parse("with a as b: print b", "noname")
# print dir(c)
# print ast.dump(c)

print codegen.to_source(ast.Repr(ast.Num(1)))

def main():
	args = parseArgs(sys.argv[1:])
	# convert directories to filenames
	sources = list(args.sources)
	directories = set (os.path.abspath(dir) for dir in args.directory or ())
	exclude_directories = set (os.path.abspath(dir) for dir in args.exclude_directory or ())
	if directories:
		print >>sys.stderr, 'Directory: %s' % (os.path.pathsep.join(directories) or 'NONE')
	if exclude_directories:
		print >>sys.stderr, 'Exclude Directories: %s' % (os.path.pathsep.join(exclude_directories) or 'NONE')

	for dir in directories:
		if dir in exclude_directories:
			raise RuntimeError("Should not both include and exclude directory '%s'" % dir)

	for dir in args.directory or []:
		sources += getSourcesInDirectory(dir, exclude_directories=exclude_directories)

	if args.listfiles:
		for src in sources:
			print src
		exit(0)

	astop.astoptimize( sources, replace_py=args.replace_py )



def parseArgs(args):
	parser = argparse.ArgumentParser(
		prog="pyastop.py",
		description="Python AST Optimizer by Nan Lin @NeteaseGames",
		# usage='%(prog)s [options]'
	)

	# parser.add_argument('-o', '--output', nargs=1, metavar="<file>", type=str, required=True, help="specify the output source file")
	parser.add_argument('-d', '--directory', metavar="<dir>", type=str, nargs='*', help="specify input source directory")
	parser.add_argument('-xd', '--exclude-directory', metavar="<exc_dir>", type=str, nargs='*', help="specify source directory to exclude")
	parser.add_argument('--listfiles', '-listfiles', action='store_true', help='just list files to be optimized, but not optimize it')
	parser.add_argument('--replace-py', action='store_true', help='replace *.py with optimized version (DANGEROUS!)')
	parser.add_argument('sources', metavar="<sources>", type=str, nargs='*', help="input source files")
	return parser.parse_args(args)

def getSourcesInDirectory(srcdir, ignore_dirs=('.svn', '.git'), exclude_directories=()):
	sources = []

	def check_exclude(path, dir):
		if dir in ignore_dirs:
			return True

		# print 'check_exclude', os.path.join(path, dir), exclude_directories
		return os.path.join(path, dir) in exclude_directories

	for path, dirs, files in os.walk(srcdir):
		dirs[:] = [dir for dir in dirs if not check_exclude(path, dir)]

		for fn in files:
			if fn.endswith('.py'):
				sources.append(os.path.join(path, fn))

	return sources

if __name__ == '__main__':
	main()
