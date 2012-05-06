from lxml.etree import tounicode
from lxml.html import document_fromstring
from lxml.html import fragment_fromstring
from unittest import TestCase

from breadability.readable import Article
from breadability.readable import get_class_weight
from breadability.readable import get_link_density
from breadability.readable import score_candidates
from breadability.readable import transform_misused_divs_into_paragraphs
from breadability.scoring import ScoredNode
from breadability.tests import load_snippet
from breadability.tests import load_article


class TestReadableDocument(TestCase):
    """Verify we can process html into a document to work off of."""

    def test_load_doc(self):
        """We get back an element tree from our original doc"""
        doc = Article(load_snippet('document_min.html'))
        # We get back the document as a div tag currently by default.
        self.assertEqual(doc.readable.tag, 'div')

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
        self.assertEqual(doc.readable.tag, 'div')
        self.assertEqual(doc.readable.get('id'), 'readabilityBody')

    def test_body_doesnt_exist(self):
        """If we can't find a body, then we create one.

        We build our doc around the rest of the html we parsed.

        """
        doc = Article(load_snippet('document_no_body.html'))
        self.assertEqual(doc.readable.tag, 'div')
        self.assertEqual(doc.readable.get('id'), 'readabilityBody')

    def test_bare_content(self):
        """If the document is just pure content, no html tags we should be ok

        We build our doc around the rest of the html we parsed.

        """
        doc = Article(load_snippet('document_only_content.html'))
        self.assertEqual(doc.readable.tag, 'div')
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

class TestCandidateNodes(TestCase):
    """Candidate nodes are scoring containers we use."""

    def test_candidate_scores(self):
        """We should be getting back objects with some scores."""
        fives = ['<div/>']
        threes = ['<pre/>', '<td/>', '<blockquote/>']
        neg_threes = ['<address/>', '<ol/>']
        neg_fives = ['<h1/>', '<h2/>', '<h3/>', '<h4/>']

        for n in fives:
            doc = fragment_fromstring(n)
            self.assertEqual(ScoredNode(doc).content_score, 5)

        for n in threes:
            doc = fragment_fromstring(n)
            self.assertEqual(ScoredNode(doc).content_score, 3)

        for n in neg_threes:
            doc = fragment_fromstring(n)
            self.assertEqual(ScoredNode(doc).content_score, -3)

        for n in neg_fives:
            doc = fragment_fromstring(n)
            self.assertEqual(ScoredNode(doc).content_score, -5)


class TestClassWeights(TestCase):
    """Certain ids and classes get us bonus points."""

    def test_positive_class(self):
        """Some classes get us bonus points."""
        node = fragment_fromstring('<p class="article">')
        self.assertEqual(get_class_weight(node), 25)

    def test_positive_ids(self):
        """Some ids get us bonus points."""
        node = fragment_fromstring('<p id="content">')
        self.assertEqual(get_class_weight(node), 25)

    def test_negative_class(self):
        """Some classes get us negative points."""
        node = fragment_fromstring('<p class="comment">')
        self.assertEqual(get_class_weight(node), -25)

    def test_negative_ids(self):
        """Some ids get us negative points."""
        node = fragment_fromstring('<p id="media">')
        self.assertEqual(get_class_weight(node), -25)


class TestScoringNodes(TestCase):
    """We take out list of potential nodes and score them up."""

    def test_we_get_candidates(self):
        """Processing candidates should get us a list of nodes to try out."""
        # we'll start out using our first real test document
        test_nodes = []
        doc = document_fromstring(load_article('ars/ars.001.html'))
        for node in doc.getiterator():
            if node.tag in ['p', 'td', 'pre']:
                test_nodes.append(node)

        candidates = score_candidates(test_nodes)

        # this might change as we tweak our algorithm, but if it does change,
        # it signifies we need to look at what we changed.
        self.assertEqual(len(candidates.keys()), 8)

        # one of these should have a decent score
        scores = sorted([c.content_score for c in candidates.values()])
        self.assertTrue(scores[-1] > 100)

class TestLinkDensityScoring(TestCase):
    """Link density will adjust out candidate scoresself."""

    def test_link_density(self):
        """Test that we get a link density"""
        doc = document_fromstring(load_article('ars/ars.001.html'))
        for node in doc.getiterator():
            if node.tag in ['p', 'td', 'pre']:
                density = get_link_density(node)

                # the density must be between 0, 1
                self.assertTrue(density >= 0.0 and density <= 1.0)


class TestSiblings(TestCase):
    """Siblings will be included if their content is related."""

    def test_bad_siblings_not_counted(self):
        """"""

        assert False, "TBD"

    def test_good_siblings_counted(self):
        """"""

        assert False, "TBD"
