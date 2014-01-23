# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

from os.path import join, dirname
from breadability.readable import Article
from ...compat import unittest


class TestSweetsharkBlog(unittest.TestCase):
    """
    Test the scoring and parsing of the article from URL below:
    http://sweetshark.livejournal.com/11564.html
    """

    def setUp(self):
        """Load up the article for us"""
        article_path = join(dirname(__file__), "article.html")
        with open(article_path, "rb") as file:
            self.document = Article(file.read(), "http://sweetshark.livejournal.com/11564.html")

    def tearDown(self):
        """Drop the article"""
        self.document = None

    def test_parses(self):
        """Verify we can parse the document."""
        self.assertIn('id="readabilityBody"', self.document.readable)

    def test_content_after_video(self):
        """The div with the comments should be removed."""
        self.assertIn('Stay hungry, Stay foolish', self.document.readable)
