
a, b = 1, 2



def funcargsunfolding_1(a, b, c=1, d=2, e=3):
	print a, b, c, d, e

funcargsunfolding_1(1, 2)
funcargsunfolding_1(1,2,3)
funcargsunfolding_1(1, 2, c=1, d=3)
funcargsunfolding_1(1, 2, *[3,4,5])


class A(object):
	def __init__(self):
		pass

	def funcargsunfolding_2(self, a, b, *c):
		pass

	def funcargsunfolding_3(self, a, b=1, c=[], **kwargs):
		pass

	def funcargsunfolding_4(self):
		self.funcargsunfolding_2(1, 2, *[3])
		self.funcargsunfolding_3(a, c=[], d=1, e=1)

a = A()
a.funcargsunfolding_2(1,2,3,4,5)