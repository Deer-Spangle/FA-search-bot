

class MockMethod:

    def __init__(self, value=None):
        self.called = False
        self.value = value

    def call(self, arg1 = None, arg2 = None, arg3 = None):
        self.called = True
        return self.value
