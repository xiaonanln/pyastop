import time

a = 1

def foo(x, y):
	global len
	len = len
	print len
	global a
	a = 1
	xxx

foo(1,2)
print locals()
print a
xxx
#xxx
#
#
# def f(a, b, c, d):
# 	pass
#
# t0 = time.time()
# for i in xrange(1000000):
# 	f(1, 2, 3, 4)
#
#
# print time.time() - t0; t0 = time.time()
#
# args = [1,2,3,4]
# for i in xrange(1000000):
# 	f(*args)
#
#
# print time.time() - t0; t0 = time.time()
#
# for i in xrange(1000000):
# 	f(1, b=2, c=3, d=4)
#
#
# print time.time() - t0; t0 = time.time()
#
# kwargs= {'b':2, 'c': 3, 'd': 4}
# for i in xrange(1000000):
# 	f(1, **kwargs)
#
# print time.time() - t0; t0 = time.time()
#
