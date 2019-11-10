

class MockMethod:

    def __init__(self, value=None):
        self.called = False
        self.value = value
        self.args = None

    def call(self, *args):
        self.called = True
        self.args = args
        return self.value
