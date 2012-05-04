from collections import defaultdict
from unittest import TestCase

from breadability.document import OriginalDocument
from breadability.tests import load_snippet


class TestOriginalDocument(TestCase):

    """Verify we can process html into a document to work off of."""

    def test_readin_min_document(self):
        """Verify we can read in a min html document"""
        doc = OriginalDocument(load_snippet('document_min.html'))
        self.assertTrue(str(doc).startswith(u'<html>'))
        self.assertEqual(doc.title, 'Min Document Title')

    def test_readin_with_base_url(self):
        """Passing a url should update links to be absolute links"""
        doc = OriginalDocument(
            load_snippet('document_absolute_url.html'),
            url="http://blog.mitechie.com/test.html")
        self.assertTrue(str(doc).startswith(u'<html>'))

        # find the links on the page and make sure each one starts with out
        # base url we told it to use.
        links = doc.links
        self.assertEqual(len(links), 3)
        # we should have two links that start with our blog url
        # and one link that starts with amazon
        link_counts = defaultdict(int)
        for link in links:
            if link.get('href').startswith('http://blog.mitechie.com'):
                link_counts['blog'] += 1
            else:
                link_counts['other'] += 1

        self.assertEqual(link_counts['blog'], 2)
        self.assertEqual(link_counts['other'], 1)

    def test_no_br_allowed(self):
        """We convert all <br/> tags to <p> tags"""
        doc = OriginalDocument(load_snippet('document_min.html'))
        self.assertIsNone(doc.html.find('.//br'))
