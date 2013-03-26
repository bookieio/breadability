# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

from os.path import abspath, dirname, join


TEST_DIR = abspath(dirname(__file__))


def load_snippet(file_name):
    """Helper to fetch in the content of a test snippet."""
    file_path = join(TEST_DIR, "data/snippets", file_name)
    with open(file_path, "rb") as file:
        return file.read()


def load_article(file_name):
    """Helper to fetch in the content of a test article."""
    file_path = join(TEST_DIR, "data/articles", file_name)
    with open(file_path, "rb") as file:
        return file.read()
