from lxml.etree import tounicode
from lxml.html import document_fromstring
from unittest import TestCase

from breadability.readable import Article
from breadability.readable import transform_misused_divs_into_paragraphs
from breadability.tests import load_snippet


class TestReadableDocument(TestCase):
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
        self.assertEqual(doc.readable.get('id'), 'readabilityBody')

    def test_body_doesnt_exist(self):
        """If we can't find a body, then we create one.

        We build our doc around the rest of the html we parsed.

        """
        doc = Article(load_snippet('document_no_body.html'))
        self.assertEqual(doc.readable.tag, 'body')
        self.assertEqual(doc.readable.get('id'), 'readabilityBody')

    def test_bare_content(self):
        """If the document is just pure content, no html tags we should be ok

        We build our doc around the rest of the html we parsed.

        """
        doc = Article(load_snippet('document_only_content.html'))
        self.assertEqual(doc.readable.tag, 'body')
        self.assertEqual(doc.readable.get('id'), 'readabilityBody')


class TestCleaning(TestCase):
    """Test out our cleaning processing we do."""

    def test_unlikely_hits(self):
        """Verify we wipe out things from our unlikely list."""
        doc = Article(load_snippet('test_readable_unlikely.html'))
        readable = doc.readable
        must_not_appear = ['comment', 'community', 'disqus', 'extra', 'foot',
                'header', 'menu', 'remark', 'rss', 'shoutbox', 'sidebar',
                'sponsor', 'ad-break', 'agegate', 'pagination' '', 'pager',
                'popup', 'tweet', 'twitter']

        want_to_appear = ['and', 'article', 'body', 'column', 'main', 'shadow']

        for i in must_not_appear:
            # we cannot find any class or id with this value
            by_class = readable.find_class(i)

            for test in by_class:
                # if it's here it cannot have the must not class without the
                # want to appear class
                found = False
                for cls in test.get('class').split():
                    if cls in want_to_appear:
                        found = True
                self.assertTrue(found)

            by_ids = readable.get_element_by_id(i, False)
            if by_ids is not False:
                found = False
                for ids in test.get('id').split():
                    if ids in want_to_appear:
                        found = True
                self.assertTrue(found)

    def test_misused_divs_transform(self):
        """Verify we replace leaf node divs with p's

        They should have the same content, just be a p vs a div

        """
        test_html = "<html><body><div>simple</div></body></html>"
        test_doc = document_fromstring(test_html)
        self.assertEqual(
            tounicode(
                transform_misused_divs_into_paragraphs(test_doc)),
            u"<html><body><p>simple</p></body></html>"
        )

        test_html2 = '<html><body><div>simple<a href="">link</a></div></body></html>'
        test_doc2 = document_fromstring(test_html2)
        self.assertEqual(
            tounicode(
                transform_misused_divs_into_paragraphs(test_doc2)),
                u'<html><body><p>simple<a href="">link</a></p></body></html>'
        )
