
def class_view_decorator(function_decorator):

    def decorate_method(unbound_method):

        def method_proxy(self, *args, **kwargs):
            def f(*a, **kw):
                return unbound_method(self, *a, **kw)

            return function_decorator(f)(*args, **kwargs)

        return method_proxy

    return decorate_method

