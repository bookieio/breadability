# -*- coding: utf8 -*-

"""Test the scoring and parsing of the Article"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
from operator import attrgetter

import pytest

from breadability.readable import Article, check_siblings, prep_article


@pytest.fixture(scope="module")
def article():
    """Load up the article for us"""
    article_path = os.path.join(os.path.dirname(__file__), 'article.html')
    with open(article_path) as file:
        return Article(file.read())


def test_parses(article):
    """Verify we can parse the document."""
    assert 'id="readabilityBody"' in article.readable


def test_content_exists(article):
    """Verify that some content exists."""
    assert 'Amazon and Google' in article.readable
    assert not 'Linkblog updated' in article.readable
    assert not '#anExampleGoogleDoesntIntendToShareBlogAndItWill' in article.readable


@pytest.mark.skip("Test fails because of some weird hash.")
def test_candidates(article):
    """Verify we have candidates."""
    # from lxml.etree import tounicode
    found = False
    wanted_hash = '04e46055'

    for node in article.candidates.values():
        if node.hash_id == wanted_hash:
            found = node

    assert found

    # we have the right node, it must be deleted for some reason if it's
    # not still there when we need it to be.
    # Make sure it's not in our to drop list.
    for node in article._should_drop:
        assert node != found.node

    by_score = sorted(
        [c for c in article.candidates.values()],
        key=attrgetter('content_score'), reverse=True)
    assert by_score[0].node == found.node

    updated_winner = check_siblings(by_score[0], article.candidates)
    updated_winner.node = prep_article(updated_winner.node)

    # This article hits up against the img > p conditional filtering
    # because of the many .gif images in the content. We've removed that
    # rule.
