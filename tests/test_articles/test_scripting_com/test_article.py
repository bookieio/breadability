# -*- coding: utf8 -*-

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

import os

from operator import attrgetter
from breadability.readable import Article
from breadability.readable import check_siblings
from breadability.readable import prep_article
from ...compat import unittest


class TestArticle(unittest.TestCase):
    """Test the scoring and parsing of the Article"""

    def setUp(self):
        """Load up the article for us"""
        article_path = os.path.join(os.path.dirname(__file__), 'article.html')
        self.article = open(article_path).read()

    def tearDown(self):
        """Drop the article"""
        self.article = None

    def test_parses(self):
        """Verify we can parse the document."""
        doc = Article(self.article)
        self.assertTrue('id="readabilityBody"' in doc.readable)

    def test_content_exists(self):
        """Verify that some content exists."""
        doc = Article(self.article)
        self.assertTrue('Amazon and Google' in doc.readable)
        self.assertFalse('Linkblog updated' in doc.readable)
        self.assertFalse(
            '#anExampleGoogleDoesntIntendToShareBlogAndItWill' in doc.readable)

    @unittest.skip("Test fails because of some weird hash.")
    def test_candidates(self):
        """Verify we have candidates."""
        doc = Article(self.article)
        # from lxml.etree import tounicode
        found = False
        wanted_hash = '04e46055'

        for node in doc.candidates.values():
            if node.hash_id == wanted_hash:
                found = node

        self.assertTrue(found)

        # we have the right node, it must be deleted for some reason if it's
        # not still there when we need it to be.
        # Make sure it's not in our to drop list.
        for node in doc._should_drop:
            self.assertFalse(node == found.node)

        by_score = sorted(
            [c for c in doc.candidates.values()],
            key=attrgetter('content_score'), reverse=True)
        self.assertTrue(by_score[0].node == found.node)

        updated_winner = check_siblings(by_score[0], doc.candidates)
        updated_winner.node = prep_article(updated_winner.node)

        # This article hits up against the img > p conditional filtering
        # because of the many .gif images in the content. We've removed that
        # rule.
