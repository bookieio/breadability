# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

from collections import defaultdict
from breadability._compat import to_unicode, to_bytes
from breadability.document import (
    convert_breaks_to_paragraphs,
    determine_encoding,
    OriginalDocument,
)
from .compat import unittest
from .utils import load_snippet


class TestOriginalDocument(unittest.TestCase):
    """Verify we can process html into a document to work off of."""

    def test_convert_br_tags_to_paragraphs(self):
        returned = convert_breaks_to_paragraphs(
            "<div>HI<br><br>How are you?<br><br> \t \n  <br>Fine\n I guess</div>")

        self.assertEqual(
            returned,
            "<div>HI</p><p>How are you?</p><p>Fine\n I guess</div>")

    def test_convert_hr_tags_to_paragraphs(self):
        returned = convert_breaks_to_paragraphs(
            "<div>HI<br><br>How are you?<hr/> \t \n  <br>Fine\n I guess</div>")

        self.assertEqual(
            returned,
            "<div>HI</p><p>How are you?</p><p>Fine\n I guess</div>")

    def test_readin_min_document(self):
        """Verify we can read in a min html document"""
        doc = OriginalDocument(load_snippet('document_min.html'))
        self.assertTrue(to_unicode(doc).startswith('<html>'))
        self.assertEqual(doc.title, 'Min Document Title')

    def test_readin_with_base_url(self):
        """Passing a url should update links to be absolute links"""
        doc = OriginalDocument(
            load_snippet('document_absolute_url.html'),
            url="http://blog.mitechie.com/test.html")
        self.assertTrue(to_unicode(doc).startswith('<html>'))

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
        self.assertIsNone(doc.dom.find('.//br'))

    def test_empty_title(self):
        """We convert all <br/> tags to <p> tags"""
        document = OriginalDocument("<html><head><title></title></head><body></body></html>")
        self.assertEqual(document.title, "")

    def test_title_only_with_tags(self):
        """We convert all <br/> tags to <p> tags"""
        document = OriginalDocument("<html><head><title><em></em></title></head><body></body></html>")
        self.assertEqual(document.title, "")

    def test_no_title(self):
        """We convert all <br/> tags to <p> tags"""
        document = OriginalDocument("<html><head></head><body></body></html>")
        self.assertEqual(document.title, "")

    def test_encoding(self):
        text = "ľščťžýáíéäúňôůě".encode("iso-8859-2")
        determine_encoding(text)

    def test_encoding_short(self):
        text = "ľščťžýáíé".encode("iso-8859-2")
        encoding = determine_encoding(text)
        self.assertEqual(encoding, "utf8")

        text = to_bytes("ľščťžýáíé")
        encoding = determine_encoding(text)
        self.assertEqual(encoding, "utf8")
