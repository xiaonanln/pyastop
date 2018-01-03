

def inlineFunc1(a, b):
	return a + b

def f():
	return 1

def testInline():
	# a = inlineFunc1(1, 2)
	a = inlineFunc1(9,10) if inlineFunc1(9,10) else inlineFunc1(11,12)


	c = {inlineFunc1(1, 2): inlineFunc1(3, 4), 2:inlineFunc1(5, 6)}
	# b = inlineFunc1(1, 2) + inlineFunc1(3, 4)

	print a, c
#
# class A(object):
# 	def __init__(self):
# 		self.val = 1
#
# 	def inlineMethod1(self, a):
# 		self.val += a
# 		return self.val
#
# 	def inlineMethod2(self, a):
# 		self.val += a
# 		return
#
# 	def testInline1(self):
# 		self.inlineMethod1(1)
#
# 	def testInline2(self):
# 		self.inlineMethod2(1)
