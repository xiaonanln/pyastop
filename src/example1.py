# coding: utf8

GEN_N = 5

def gen():
	for i in xrange(GEN_N):
		yield i

def test1():
	for i in xrange(3): # astop: expand
		print 1

	for i in xrange(3): # astop: expand
		print i

	for i in gen():
		print i

	N = 100
	for i in xrange(N):
		print i


def eval0():
	return 100