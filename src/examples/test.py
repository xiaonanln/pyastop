
import time

def f(*args, **kwargs):
	print 'f', args, kwargs
	pass

def E(v, e=None):
	print 'E', v
	return e if e is not None else v

E("target", [0])[0] += 1


class A(object):
	eval  = 1

	class B(object):
		eval = 2
		def B(self):
			def C():
				print eval
				pass
			C()

A.B().B()