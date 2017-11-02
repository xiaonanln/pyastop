
class Class1(object):
    pass

    class Class1A(object):
        pass

def foo1(x):
    def foo1a(x):
        len = lambda x: x
        bool = lambda x: False
        a=  1+1
        a = len("abc")
        a = bool("abc")

    foo1a(1)
    a = len("abc")
    a = bool("abc")

def foo2(a, b, *c):
    pass


def foo3(a, b, c=list()):
    print a
    pass

def foo4():
    len = lambda x: 3
    print len("abcd")
    print len("abcd")
    bool = 1
    bool += 1

foo4()