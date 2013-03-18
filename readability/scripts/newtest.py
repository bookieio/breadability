# -*- coding: utf8 -*-

"""
Helper to generate a new set of article test files for readability.

Usage:
    readability_newtest -n <name> <url>
    readability_newtest --version
    readability_newtest --help

Arguments:
  <url>                   The url of content to fetch for the article.html

Options:
  -n <name>, --name=<name>  Name of the test directory.
  --version                 Show program's version number and exit.
  -h, --help                Show this help message and exit.
"""

from __future__ import absolute_import

import io

from os import mkdir
from os.path import join, dirname, pardir
from docopt import docopt
from .._version import VERSION
from .._py3k import urllib


TEST_PATH = join(
    dirname(__file__),
    pardir,
    "tests",
    "test_articles"
)

TEST_TEMPLATE = """
import os

try:
    # Python < 2.7
    import unittest2 as unittest
except ImportError:
    import unittest

from readability.readable import Article


class TestArticle(unittest.TestCase):
    '''Test the scoring and parsing of the Article'''

    def setUp(self):
        '''Load up the article for us'''
        article_path = os.path.join(os.path.dirname(__file__), 'article.html')
        self.article = open(article_path).read()

    def tearDown(self):
        '''Drop the article'''
        self.article = None

    def test_parses(self):
        '''Verify we can parse the document.'''
        doc = Article(self.article)
        self.assertTrue('id="readabilityBody"' in doc.readable)

    def test_content_exists(self):
        '''Verify that some content exists.'''
        raise NotImplementedError()

    def test_content_does_not_exist(self):
        '''Verify we cleaned out some content that shouldn't exist.'''
        raise NotImplementedError()
"""


def parse_args():
    return docopt(__doc__, version=VERSION)


def make_test_directory(name):
    """Generates a new directory for tests."""
    directory_name = "test_" + name.replace(" ", "_")
    directory_path = join(TEST_PATH, directory_name)
    mkdir(directory_path)

    return directory_path


def make_test_files(directory_path):
    init_file = join(directory_path, "__init__.py")
    open(init_file, "a").close()

    test_file = join(directory_path, "test.py")
    with open(test_file, "w") as file:
        file.write(TEST_TEMPLATE)


def fetch_article(directory_path, url):
    """Get the content of the url and make it the article.html"""
    opener = urllib.build_opener()
    opener.addheaders = [('Accept-Charset', 'utf-8')]

    response = opener.open(url)
    html = response.read().decode("utf-8")
    response.close()

    path = join(directory_path, "article.html")
    file = io.open(path, "w", encoding="utf8")
    file.write(html)
    file.close()


def main():
    """Run the script."""
    args = parse_args()
    directory = make_test_directory(args["<name>"])
    make_test_files(directory)
    fetch_article(directory, args["<url>"])


if __name__ == '__main__':
    main()
