
a, b = 1, 2



def f(a, b, c=1, d=2, e=3):
	print a, b, c, d, e

f(1, 2)
f(1,2,3)

class A(object):
	def __init__(self):
		pass

	def vararg(self, a, b, *c):
		pass

	def foo(self, a, b=1, c=[], **kwargs):
		pass