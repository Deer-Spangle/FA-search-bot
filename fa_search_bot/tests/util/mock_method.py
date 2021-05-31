class MockMethod:

    def __init__(self, value=None):
        self.called = False
        self.value = value
        self.args = None
        self.kwargs = None

    def call(self, *args, **kwargs):
        self.called = True
        self.args = args
        self.kwargs = kwargs
        return self.value

    async def async_call(self, *args, **kwargs):
        return self.call(*args, **kwargs)


class MockMultiMethod:

    def __init__(self, values=None):
        self.calls = 0
        self.values = values
        self.args = []
        self.kwargs = []

    def call(self, *args, **kwargs):
        self.calls += 1
        self.args.append(args)
        self.kwargs.append(kwargs)
        if self.values is None:
            return None
        return self.values[self.calls - 1]

    async def async_call(self, *args, **kwargs):
        return self.call(*args, **kwargs)
