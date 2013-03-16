# -*- coding: utf8 -*-


def cached_property(getter):
    """
    Decorator that converts a method into memoized property.
    The decorator works as expected only for classes with
    attribute '__dict__' and immutable properties.
    """
    def decorator(self):
        key = "_cached_property_" + getter.__name__

        if not hasattr(self, key):
            setattr(self, key, getter(self))

        return getattr(self, key)

    decorator.__name__ = getter.__name__
    decorator.__module__ = getter.__module__
    decorator.__doc__ = getter.__doc__

    return property(decorator)
