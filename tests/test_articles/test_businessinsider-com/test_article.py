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


def test_images_preserved(article):
    """The div with the comments should be removed."""
    doc = Article(article)

    assert 'bharath-kumar-a-co-founder-at-pugmarksme-suggests-working-on-a-sunday-late-night.jpg' in doc.readable
    assert 'bryan-guido-hassin-a-university-professor-and-startup-junkie-uses-airplane-days.jpg' in doc.readable
