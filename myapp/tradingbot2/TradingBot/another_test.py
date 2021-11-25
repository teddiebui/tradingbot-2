class A:
    def __init__(self):
        
        print("class A")
        super().__init__()
        self.a = "a"


class B:
    def __init__(self):
        print("class B")
        super().__init__()
        self.b="b"

class C:
    def __init__(self):
        print("class C")
        self.c="c"

class D(A, B, C):
    def __init__(self):
        super().__init__()
        self.d="d"
        print("class D")

o = D()


print(o.a)
print(o.b)
print(o.c)
print(o.d)
print(D.__mro__)
