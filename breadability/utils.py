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


MULTIPLE_WHITESPACE_PATTERN = re.compile(r"\s+", re.UNICODE)


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
    If there is at least one new line character chunk is replaced
    by single LF (Unix new line) character.
    """
    return MULTIPLE_WHITESPACE_PATTERN.sub(_replace_whitespace, text)


def _replace_whitespace(match):
    text = match.group()

    if "\n" in text or "\r" in text:
        return "\n"
    else:
        return " "


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
