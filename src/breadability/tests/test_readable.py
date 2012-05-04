from collections import defaultdict
from unittest import TestCase

from breadability.readable import Article
from breadability.tests import load_snippet


class TestOriginalDocument(TestCase):
    """Verify we can process html into a document to work off of."""

    def test_load_doc(self):
        """We get back an element tree from our original doc"""
        doc = Article(load_snippet('document_min.html'))
        # We get back the document as a body tag currently by default.
        self.assertEqual(doc.readable.tag, 'body')

    def test_doc_no_scripts_styles(self):
        """Step #1 remove all scripts from the document"""
        doc = Article(load_snippet('document_scripts.html'))
        readable = doc.readable
        self.assertEqual(readable.findall(".//script"), [])
        self.assertEqual(readable.findall(".//style"), [])
        self.assertEqual(readable.findall(".//link"), [])

    def test_find_body_exists(self):
        """If the document has a body, we store that as the readable html

        No sense processing anything other than the body content.

        """
        doc = Article(load_snippet('document_min.html'))
        self.assertEqual(doc.readable.tag, 'body')
        self.assertEqual(doc.readable.get('class'), 'readabilityBody')

    def test_body_doesnt_exist(self):
        """If we can't find a body, then we create one.

        We build our doc around the rest of the html we parsed.

        """
        doc = Article(load_snippet('document_no_body.html'))
        self.assertEqual(doc.readable.tag, 'body')
        self.assertEqual(doc.readable.get('class'), 'readabilityBody')

    def test_bare_content(self):
        """If the document is just pure content, no html tags we should be ok

        We build our doc around the rest of the html we parsed.

        """
        doc = Article(load_snippet('document_only_content.html'))
        self.assertEqual(doc.readable.tag, 'body')
        self.assertEqual(doc.readable.get('class'), 'readabilityBody')
