# -*- coding: utf8 -*-

"""
Helper to generate a new set of article test files for breadability.

Usage:
    breadability_test --name <name> <url>
    breadability_test --version
    breadability_test --help

Arguments:
  <url>                   The url of content to fetch for the article.html

Options:
  -n <name>, --name=<name>  Name of the test directory.
  --version                 Show program's version number and exit.
  -h, --help                Show this help message and exit.
"""

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

from os import mkdir
from os.path import join, dirname, pardir, exists as path_exists
from docopt import docopt
from .. import __version__
from .._compat import to_unicode, urllib


TEST_PATH = join(
    dirname(__file__),
    pardir, pardir,
    "tests/test_articles"
)

TEST_TEMPLATE = '''# -*- coding: utf8 -*-

"""
Test the scoring and parsing of the article from URL below:
%(source_url)s
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os

import pytest

from breadability.readable import Article


@pytest.fixture(scope="module")
def article():
    """Load up the article for us"""
    article_path = os.path.join(os.path.dirname(__file__), "article.html")
    with open(article_path, "rb") as file:
        return Article(file.read(), "%(source_url)s")


def test_parses(article):
    """Verify we can parse the document."""
    assert 'id="readabilityBody"' in article.readable


def test_content_exists(article):
    """Verify that some content exists."""
    assert "#&@#&@#&@" in article.readable


def test_content_does_not_exist(article):
    """Verify we cleaned out some content that shouldn't exist."""
    assert "" not in article.readable
'''


def parse_args():
    return docopt(__doc__, version=__version__)


def make_test_directory(name):
    """Generates a new directory for tests."""
    directory_name = "test_" + name.replace(" ", "_")
    directory_path = join(TEST_PATH, directory_name)

    if not path_exists(directory_path):
        mkdir(directory_path)

    return directory_path


def make_test_files(directory_path, url):
    init_file = join(directory_path, "__init__.py")
    open(init_file, "a").close()

    data = TEST_TEMPLATE % {
        "source_url": to_unicode(url)
    }

    test_file = join(directory_path, "test_article.py")
    with open(test_file, "w") as file:
        file.write(data)


def fetch_article(directory_path, url):
    """Get the content of the url and make it the article.html"""
    opener = urllib.build_opener()
    opener.addheaders = [("Accept-Charset", "utf-8")]

    response = opener.open(url)
    html_data = response.read()
    response.close()

    path = join(directory_path, "article.html")
    with open(path, "wb") as file:
        file.write(html_data)


def main():
    """Run the script."""
    args = parse_args()
    directory = make_test_directory(args["--name"])
    make_test_files(directory, args["<url>"])
    fetch_article(directory, args["<url>"])


if __name__ == "__main__":
    main()
