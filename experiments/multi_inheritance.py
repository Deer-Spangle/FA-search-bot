

class A:

    def __init__(self):
        print("A calling super:")
        print("A")


class B(A):

    def __init__(self):
        print("B calling super:")
        super().__init__()
        print("B")


class C(A):

    def __init__(self):
        print("C calling super:")
        super().__init__()
        print("C")


class D(B, C):

    def __init__(self):
        print("D calling super:")
        super().__init__()
        print("D")

d = D()
