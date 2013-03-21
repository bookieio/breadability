# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

from lxml.etree import tounicode
from lxml.html import document_fromstring
from lxml.html import fragment_fromstring
from readability._py3k import to_unicode
from readability.readable import Article
from readability.readable import get_class_weight
from readability.readable import get_link_density
from readability.readable import is_bad_link
from readability.readable import score_candidates
from readability.readable import leaf_div_elements_into_paragraphs
from readability.scoring import ScoredNode
from .compat import unittest
from .utils import load_snippet, load_article


class TestReadableDocument(unittest.TestCase):
    """Verify we can process html into a document to work off of."""

    def test_load_doc(self):
        """We get back an element tree from our original doc"""
        doc = Article(load_snippet('document_min.html'))
        # We get back the document as a div tag currently by default.
        self.assertEqual(doc.readable_dom.tag, 'div')

    def test_doc_no_scripts_styles(self):
        """Step #1 remove all scripts from the document"""
        doc = Article(load_snippet('document_scripts.html'))
        readable = doc.readable_dom
        self.assertEqual(readable.findall(".//script"), [])
        self.assertEqual(readable.findall(".//style"), [])
        self.assertEqual(readable.findall(".//link"), [])

    def test_find_body_exists(self):
        """If the document has a body, we store that as the readable html

        No sense processing anything other than the body content.

        """
        doc = Article(load_snippet('document_min.html'))
        self.assertEqual(doc.readable_dom.tag, 'div')
        self.assertEqual(doc.readable_dom.get('id'), 'readabilityBody')

    def test_body_doesnt_exist(self):
        """If we can't find a body, then we create one.

        We build our doc around the rest of the html we parsed.

        """
        doc = Article(load_snippet('document_no_body.html'))
        self.assertEqual(doc.readable_dom.tag, 'div')
        self.assertEqual(doc.readable_dom.get('id'), 'readabilityBody')

    def test_bare_content(self):
        """If the document is just pure content, no html tags we should be ok

        We build our doc around the rest of the html we parsed.

        """
        doc = Article(load_snippet('document_only_content.html'))
        self.assertEqual(doc.readable_dom.tag, 'div')
        self.assertEqual(doc.readable_dom.get('id'), 'readabilityBody')


    def test_no_content(self):
        """Without content we supply an empty unparsed doc."""
        doc = Article('')
        self.assertEqual(doc.readable_dom.tag, 'div')
        self.assertEqual(doc.readable_dom.get('id'), 'readabilityBody')
        self.assertEqual(doc.readable_dom.get('class'), 'parsing-error')


class TestCleaning(unittest.TestCase):
    """Test out our cleaning processing we do."""

    def test_unlikely_hits(self):
        """Verify we wipe out things from our unlikely list."""
        doc = Article(load_snippet('test_readable_unlikely.html'))
        readable = doc.readable_dom
        must_not_appear = ['comment', 'community', 'disqus', 'extra', 'foot',
                'header', 'menu', 'remark', 'rss', 'shoutbox', 'sidebar',
                'sponsor', 'ad-break', 'agegate', 'pagination' '', 'pager',
                'popup', 'tweet', 'twitter', 'imgBlogpostPermalink']

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
                leaf_div_elements_into_paragraphs(test_doc)),
            to_unicode("<html><body><p>simple</p></body></html>")
        )

        test_html2 = ('<html><body><div>simple<a href="">link</a>'
                      '</div></body></html>')
        test_doc2 = document_fromstring(test_html2)
        self.assertEqual(
            tounicode(
                leaf_div_elements_into_paragraphs(test_doc2)),
                to_unicode('<html><body><p>simple<a href="">link</a></p></body></html>')
        )

    def test_dont_transform_div_with_div(self):
        """Verify that only child <div> element is replaced by <p>."""
        dom = document_fromstring(
            "<html><body><div>text<div>child</div>aftertext</div></body></html>")

        self.assertEqual(
            tounicode(leaf_div_elements_into_paragraphs(dom)),
            to_unicode("<html><body><div>text<p>child</p>aftertext</div></body></html>")
        )

    def test_bad_links(self):
        """Some links should just not belong."""
        bad_links = [
            '<a name="amazonAndGoogleHaveMadeAnAudaciousGrabOfNamespaceOnTheInternetAsFarAsICanSeeTheresBeenNoMentionOfThisInTheTechPress">&nbsp;</a>',
            '<a href="#amazonAndGoogleHaveMadeAnAudaciousGrabOfNamespaceOnTheInternetAsFarAsICanSeeTheresBeenNoMentionOfThisInTheTechPress"><img src="http://scripting.com/images/2001/09/20/sharpPermaLink3.gif" class="imgBlogpostPermalink" width="6" height="9" border="0" alt="permalink"></a>',
            '<a href="http://scripting.com/stories/2012/06/15/theTechPressIsOutToLunch.html#anExampleGoogleDoesntIntendToShareBlogAndItWillOnlyBeUsedToPointToBloggerSitesIfYouHaveATumblrOrWordpressBlogYouCantHaveABlogDomainHereIsTheAHrefhttpgtldresulticannorgapplicationresultapplicationstatusapplicationdetails527publicListingaOfGooglesAHrefhttpdropboxscriptingcomdavemiscgoogleblogapplicationhtmlapplicationa"><img src="http://scripting.com/images/2001/09/20/sharpPermaLink3.gif" class="imgBlogpostPermalink" width="6" height="9" border="0" alt="permalink"></a>'
        ]

        for l in bad_links:
            link = fragment_fromstring(l)
            self.assertTrue(is_bad_link(link))


class TestCandidateNodes(unittest.TestCase):
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

    def test_article_enables_candidate_access(self):
        """Candidates are accessible after document processing."""
        doc = Article(load_article('ars.001.html'))
        self.assertTrue(hasattr(doc, 'candidates'))


class TestClassWeights(unittest.TestCase):
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


class TestScoringNodes(unittest.TestCase):
    """We take out list of potential nodes and score them up."""

    def test_we_get_candidates(self):
        """Processing candidates should get us a list of nodes to try out."""
        # we'll start out using our first real test document
        test_nodes = []
        doc = document_fromstring(load_article('ars.001.html'))
        for node in doc.iter('p', 'td', 'pre'):
            test_nodes.append(node)

        candidates = score_candidates(test_nodes)

        # this might change as we tweak our algorithm, but if it does change,
        # it signifies we need to look at what we changed.
        self.assertEqual(len(candidates.keys()), 6)

        # one of these should have a decent score
        scores = sorted([c.content_score for c in candidates.values()])
        self.assertTrue(scores[-1] > 100)

    def test_bonus_score_per_100_chars_in_p(self):
        """Nodes get 1pt per 100 characters up to 3 max points"""
        def build_doc(length):
            div = '<div id="content" class=""><p>{0}</p></div>'
            document_str = '<html><body>{0}</body></html>'
            content = 'c' * length
            test_div = div.format(content)
            doc = document_fromstring(document_str.format(test_div))
            test_nodes = []
            for node in doc.iter('p'):
                test_nodes.append(node)

            return test_nodes

        test_nodes = build_doc(400)
        candidates = score_candidates(test_nodes)
        pscore_400 = max([c.content_score for c in candidates.values()])

        test_nodes = build_doc(100)
        candidates = score_candidates(test_nodes)
        pscore_100 = max([c.content_score for c in candidates.values()])

        test_nodes = build_doc(50)
        candidates = score_candidates(test_nodes)
        pscore_50 = max([c.content_score for c in candidates.values()])

        self.assertEqual(pscore_100, pscore_50 + 1)
        self.assertEqual(pscore_400, pscore_50 + 3)


class TestLinkDensityScoring(unittest.TestCase):
    """Link density will adjust out candidate scoresself."""

    def test_link_density(self):
        """Test that we get a link density"""
        doc = document_fromstring(load_article('ars.001.html'))
        for node in doc.iter('p', 'td', 'pre'):
            density = get_link_density(node)

            # the density must be between 0, 1
            self.assertTrue(density >= 0.0 and density <= 1.0)


class TestSiblings(unittest.TestCase):
    """Siblings will be included if their content is related."""

    @unittest.skip("Not implemented yet.")
    def test_bad_siblings_not_counted(self):
        raise NotImplementedError()

    @unittest.skip("Not implemented yet.")
    def test_good_siblings_counted(self):
        raise NotImplementedError()


class TestAnnotatedText(unittest.TestCase):
    def test_empty(self):
        article = Article("")
        dom = article.readable_annotated_text
        self.assertEqual(tounicode(dom),
            '<div id="readabilityBody" class="parsing-error"/>')

    def test_no_annotations(self):
        article = Article("<div><p>This is text with no annotations</p></div>")
        dom = article.readable_annotated_text
        self.assertEqual(tounicode(dom),
            '<div id="readabilityBody"><p>This is text with no annotations</p></div>')

    def test_one_annotation(self):
        article = Article("<div><p>This is text with <del>no</del> annotations</p></div>")
        dom = article.readable_annotated_text
        self.assertEqual(tounicode(dom),
            '<div id="readabilityBody"><p>This is text with <del>no</del> annotations</p></div>')

    def test_simple_document(self):
        article = Article(load_snippet("annotated_1.html"))
        dom = article.readable_annotated_text

        self.assertIn("Paragraph is more better", dom.text_content())
        self.assertIn("This is not crap so readability me :)", dom.text_content())

        self.assertNotIn("not so good", dom.text_content())
