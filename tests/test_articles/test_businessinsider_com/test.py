# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

from os.path import join, dirname
from breadability.readable import Article
from ...compat import unittest


class TestArticle(unittest.TestCase):
    """
    Test the scoring and parsing of the article from URL below:
    http://www.businessinsider.com/tech-ceos-favorite-productivity-hacks-2013-8
    """

    def setUp(self):
        """Load up the article for us"""
        article_path = join(dirname(__file__), "article.html")
        with open(article_path, "rb") as file:
            self.document = Article(file.read(), "http://www.businessinsider.com/tech-ceos-favorite-productivity-hacks-2013-8")

    def tearDown(self):
        """Drop the article"""
        self.document = None

    def test_parses(self):
        """Verify we can parse the document."""
        self.assertIn('id="readabilityBody"', self.document.readable)

    def test_images_preserved(self):
        """The div with the comments should be removed."""
        images = [
            'bharath-kumar-a-co-founder-at-pugmarksme-suggests-working-on-a-sunday-late-night.jpg',
            'bryan-guido-hassin-a-university-professor-and-startup-junkie-uses-airplane-days.jpg',
        ]

        for image in images:
            self.assertIn(image, self.document.readable, image)
