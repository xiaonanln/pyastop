
import time

_f = [0]
def f(n):
	print 'f', n
	return _f

def E(v, e=None):
	print 'E', v
	return e if e is not None else v

exec(E(1, "1"), E(2, {}), E(3, {}))


class A(object):

    def __init__(self):
        self.val = 1

    def inlineMethod1(self, a):
        self.val += a
        return self.val

    def inlineMethod2(self, a):
        self.val += a
        return

    def testInline1(self):
        self.val += 1
        self.val

    def testInline2(self):
	    self.inlineMethod1(1)

a = A()
t0 = time.time()
for i in xrange(1000000):
	a.testInline1()

print time.time() - t0; t0 = time.time()
for i in xrange(1000000):
	a.testInline2()
print time.time() - t0; t0 = time.time()
