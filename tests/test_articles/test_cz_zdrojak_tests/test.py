# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

from os.path import join, dirname
from breadability.readable import Article
from breadability._compat import unicode
from ...compat import unittest


class TestArticle(unittest.TestCase):
    """
    Test the scoring and parsing of the article from URL below:
    http://www.zdrojak.cz/clanky/jeste-k-testovani/
    """

    def setUp(self):
        """Load up the article for us"""
        article_path = join(dirname(__file__), "article.html")
        with open(article_path, "rb") as file:
            self.document = Article(file.read(), "http://www.zdrojak.cz/clanky/jeste-k-testovani/")

    def tearDown(self):
        """Drop the article"""
        self.document = None

    def test_parses(self):
        """Verify we can parse the document."""
        self.assertIn('id="readabilityBody"', self.document.readable)

    def test_content_exists(self):
        """Verify that some content exists."""
        self.assertIsInstance(self.document.readable, unicode)

        text = "S automatizovaným testováním kódu (a ve zbytku článku budu mít na mysli právě to) jsem se setkal v několika firmách."
        self.assertIn(text, self.document.readable)

        text = "Ke čtení naleznete mnoho různých materiálů, od teoretických po praktické ukázky."
        self.assertIn(text, self.document.readable)

    def test_content_does_not_exist(self):
        """Verify we cleaned out some content that shouldn't exist."""
        self.assertNotIn("Pokud vás problematika zajímá, využijte možnosti navštívit školení", self.document.readable)
