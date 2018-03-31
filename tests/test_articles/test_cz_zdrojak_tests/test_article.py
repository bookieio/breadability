# -*- coding: utf8 -*-

"""
Test the scoring and parsing of the article from URL below:
http://www.zdrojak.cz/clanky/jeste-k-testovani/
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os

import pytest

from breadability._compat import unicode
from breadability.readable import Article


@pytest.fixture(scope="module")
def article():
    """Load up the article for us"""
    article_path = os.path.join(os.path.dirname(__file__), 'article.html')
    with open(article_path, "rb") as file:
        return Article(file.read(), "http://www.zdrojak.cz/clanky/jeste-k-testovani/")


def test_parses(article):
    """Verify we can parse the document."""
    assert 'id="readabilityBody"' in article.readable


def test_content_exists(article):
    """Verify that some content exists."""
    assert isinstance(article.readable, unicode)

    text = "S automatizovaným testováním kódu (a ve zbytku článku budu mít na mysli právě to) jsem se setkal v několika firmách."
    assert text in article.readable

    text = "Ke čtení naleznete mnoho různých materiálů, od teoretických po praktické ukázky."
    assert text in article.readable


def test_content_does_not_exist(article):
    """Verify we cleaned out some content that shouldn't exist."""
    assert "Pokud vás problematika zajímá, využijte možnosti navštívit školení" not in article.readable
