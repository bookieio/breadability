# -*- coding: utf8 -*-

"""Test the scoring and parsing of the Blog Post"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os

import pytest

from breadability.readable import Article


@pytest.fixture(scope="module")
def article():
    """Load up the article for us"""
    article_path = os.path.join(os.path.dirname(__file__), 'article.html')
    with open(article_path) as file:
        return file.read()


def test_parses(article):
    """Verify we can parse the document."""
    doc = Article(article)

    assert 'id="readabilityBody"' in doc.readable


def test_comments_cleaned(article):
    """The div with the comments should be removed."""
    doc = Article(article)

    assert 'class="comments"' not in doc.readable


def test_beta_removed(article):
    """The id=beta element should be removed

    It's link heavy and causing a lot of garbage content. This should be
    removed.

    """
    doc = Article(article)

    assert 'id="beta"' not in doc.readable
