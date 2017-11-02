
import os as abc
from os import open as open2

g = 1

def f1():
	global g
	a = 1
	def f2():
		a = 2
		print a

	f2()

	def f3():
		a = 1
		b = 2
		print a, b
		del a, b

	f3()
	print  a

	def f4():
		g

	f4()
	print g
	g = 100
	print g


f1()

print g
