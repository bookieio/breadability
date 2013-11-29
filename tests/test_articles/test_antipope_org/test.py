# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import os

from breadability.readable import Article
from ...compat import unittest


class TestAntipopeBlog(unittest.TestCase):
    """Test the scoring and parsing of the Blog Post"""

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

    def test_comments_cleaned(self):
        """The div with the comments should be removed."""
        doc = Article(self.article)
        self.assertTrue('class="comments"' not in doc.readable)

    def test_beta_removed(self):
        """The id=beta element should be removed

        It's link heavy and causing a lot of garbage content. This should be
        removed.

        """
        doc = Article(self.article)
        self.assertTrue('id="beta"' not in doc.readable)
