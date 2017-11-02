#
a = (1+1) + (1-1) + (1*1) + (1/1)
a = 1 and 2 and 3 or 4 and 5
a = ([1,2,3]) and  1 or 5

a = [1 for i in xrange(3)]
a = len("123")
a = bool(100)
# a = [3.1416 * i for i in (1,2,3)]
# a = [3.1416 * a for (a, b) in ((1,1), (2,2), (3,3))]
# a = 123
# a = "abc"

def foo1():
	len = lambda x: x
	print len("abc")
#
def foo2():
	global bool
	bool = lambda x: False
	print bool(100)