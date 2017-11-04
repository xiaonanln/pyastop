# coding: utf8

GEN_N = 5

def gen():
	for i in xrange(GEN_N):
		yield i

def test1():
	for a in reversed([1,2,3]): # should expand
		print a

	for a in xrange(3): # should expand
		print a

	for a in reversed(xrange(3)): # should expand
		print a

	for a in xrange(1000000): # should not expand, and should not slow down pyastop
		print a

	for a in reversed(xrange(1000000)): # should not expand, and should not slow down pyastop
		print a

	# for i in gen():
	# 	print i
	#
	# N = 100
	# for i in xrange(N):
	# 	print i
	#
	# for i in (1,2,3):
	# 	print i
	#
	# for i in {1:1, 2:2, 3:3}:
	# 	print i
	#
	# for i in set([1,2,3]):
	# 	print i
	#
	# for i in [1,2,3]:
	# 	print i

def eval0():
	return 100

class ExampleClass1(object):

	def __init__(self):
		pass

	def exampleInlineMethod1(self):
		pass
