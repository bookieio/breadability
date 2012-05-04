from collections import defaultdict
from unittest import TestCase

from breadability.readable import Article
from breadability.tests import load_snippet


class TestOriginalDocument(TestCase):
    """Verify we can process html into a document to work off of."""

    def test_load_doc(self):
        """We get back an element tree from our original doc"""
        doc = Article(load_snippet('document_min.html'))
        self.assertEqual(doc.readable.tag, 'html')

    def test_doc_no_scripts_styles(self):
        """Step #1 remove all scripts from the document"""
        doc = Article(load_snippet('document_scripts.html'))
        readable = doc.readable
        self.assertEqual(readable.findall(".//script"), [])
        self.assertEqual(readable.findall(".//style"), [])
        self.assertEqual(readable.findall(".//link"), [])
