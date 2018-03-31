# -*- coding: utf8 -*-

"""
Test the scoring and parsing of the article from URL below:
http://sweetshark.livejournal.com/11564.html
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os

import pytest

from breadability.readable import Article


@pytest.fixture(scope="module")
def article():
    """Load up the article for us"""
    article_path = os.path.join(os.path.dirname(__file__), 'article.html')
    with open(article_path, "rb") as file:
        return Article(file.read(), "http://sweetshark.livejournal.com/11564.html")


def test_parses(article):
    """Verify we can parse the document."""
    assert 'id="readabilityBody"' in article.readable


def test_content_after_video(article):
    """The div with the comments should be removed."""
    assert 'Stay hungry, Stay foolish' in article.readable
