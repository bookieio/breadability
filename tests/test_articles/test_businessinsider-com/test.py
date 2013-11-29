import os
try:
    # Python < 2.7
    import unittest2 as unittest
except ImportError:
    import unittest

from breadability.readable import Article


class TestBusinessInsiderArticle(unittest.TestCase):
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

    def test_images_preserved(self):
        """The div with the comments should be removed."""
        doc = Article(self.article)
        self.assertTrue('bharath-kumar-a-co-founder-at-pugmarksme-suggests-working-on-a-sunday-late-night.jpg' in doc.readable)
        self.assertTrue('bryan-guido-hassin-a-university-professor-and-startup-junkie-uses-airplane-days.jpg' in doc.readable)
