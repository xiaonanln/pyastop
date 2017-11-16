
import time

def f(*args, **kwargs):
	print 'f', args, kwargs
	pass

def E(v, e=None):
	print 'E', v
	return e if e is not None else v


# E("func", f)( E("arg1"), E("arg2"), *E("starargs", []), a=E("keyward"), **E("kwargs", {}) )

print E("value", [1,2,3])[E("lower"):E("upper"):E("step")]
