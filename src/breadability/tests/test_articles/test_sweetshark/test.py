import os
try:
    # Python < 2.7
    import unittest2 as unittest
except ImportError:
    import unittest

from breadability.readable import Article


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

    def test_content_after_video(self):
        """The div with the comments should be removed."""
        doc = Article(self.article)
        self.assertTrue('Stay hungry, Stay foolish' in doc.readable)
