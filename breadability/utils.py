# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import re

try:
    from contextlib import ignored
except ImportError:
    from contextlib import contextmanager

    @contextmanager
    def ignored(*exceptions):
        try:
            yield
        except tuple(exceptions):
            pass


def is_blank(text):
    """
    Returns ``True`` if string contains only whitespace characters
    or is empty. Otherwise ``False`` is returned.
    """
    return not text or text.isspace()


def shrink_text(text):
    return normalize_whitespace(text.strip())


def normalize_whitespace(text):
    """
    Translates multiple whitespace into single space character.
    """
    return ' '.join(text.split())


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
