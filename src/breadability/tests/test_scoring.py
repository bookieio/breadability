import re
from lxml.html import document_fromstring
from lxml.html import fragment_fromstring
from operator import attrgetter
from unittest import TestCase

from breadability.readable import Article
from breadability.scoring import check_node_attr
from breadability.scoring import get_class_weight
from breadability.scoring import ScoredNode
from breadability.scoring import score_candidates
from breadability.readable import get_link_density
from breadability.readable import is_unlikely_node
from breadability.tests import load_snippet


class TestCheckNodeAttr(TestCase):
    """Verify a node has a class/id in the given set.

    The idea is that we have sets of known good/bad ids and classes and need
    to verify the given node does/doesn't have those classes/ids.

    """
    def test_has_class(self):
        """Verify that a node has a class in our set."""
        test_re = re.compile('test1|test2', re.I)
        test_node = fragment_fromstring('<div/>')
        test_node.set('class', 'test2 comment')

        self.assertTrue(check_node_attr(test_node, 'class', test_re))

    def test_has_id(self):
        """Verify that a node has an id in our set."""
        test_re = re.compile('test1|test2', re.I)
        test_node = fragment_fromstring('<div/>')
        test_node.set('id', 'test2')

        self.assertTrue(check_node_attr(test_node, 'id', test_re))

    def test_lacks_class(self):
        """Verify that a node does not have a class in our set."""
        test_re = re.compile('test1|test2', re.I)
        test_node = fragment_fromstring('<div/>')
        test_node.set('class', 'test4 comment')
        self.assertFalse(check_node_attr(test_node, 'class', test_re))

    def test_lacks_id(self):
        """Verify that a node does not have an id in our set."""
        test_re = re.compile('test1|test2', re.I)
        test_node = fragment_fromstring('<div/>')
        test_node.set('id', 'test4')
        self.assertFalse(check_node_attr(test_node, 'id', test_re))


class TestLinkDensity(TestCase):
    """Verify we calc our link density correctly."""

    def test_empty_node(self):
        """An empty node doesn't have much of a link density"""
        empty_div = u"<div></div>"
        doc = Article(empty_div)
        assert 0 == get_link_density(doc._readable), "Link density is nadda"

    def test_small_doc_no_links(self):
        doc = Article(load_snippet('document_min.html'))
        assert 0 == get_link_density(doc._readable), "Still no link density"

    def test_several_links(self):
        """This doc has a 3 links with the majority of content."""
        doc = Article(load_snippet('document_absolute_url.html'))
        self.assertAlmostEqual(
                get_link_density(doc._readable), 0.349,
                places=3)


class TestClassWeight(TestCase):
    """Verify we score nodes correctly based on their class/id attributes."""

    def test_no_matches_zero(self):
        """If you don't have the attribute then you get a weight of 0"""
        empty_div = u"<div></div>"
        node = fragment_fromstring(empty_div)

        self.assertEqual(get_class_weight(node), 0)

    def test_id_hits(self):
        """If the id is in the list then it gets a weight"""
        test_div = '<div id="post">Content</div>'
        node = fragment_fromstring(test_div)
        self.assertEqual(get_class_weight(node), 25)

        test_div = '<div id="comments">Content</div>'
        node = fragment_fromstring(test_div)
        self.assertEqual(get_class_weight(node), -25)

    def test_class_hits(self):
        """If the class is in the list then it gets a weight"""
        test_div = '<div class="something post">Content</div>'
        node = fragment_fromstring(test_div)
        self.assertEqual(get_class_weight(node), 25)

        test_div = '<div class="something comments">Content</div>'
        node = fragment_fromstring(test_div)
        self.assertEqual(get_class_weight(node), -25)

    def test_scores_collide(self):
        """We might hit both positive and negative scores.

        Positive and negative scoring is done independently so it's possible
        to hit both positive and negative scores and cancel each other out.

        """
        test_div = '<div id="post" class="something comment">Content</div>'
        node = fragment_fromstring(test_div)
        self.assertEqual(get_class_weight(node), 0)

        test_div = '<div id="post" class="post comment">Content</div>'
        node = fragment_fromstring(test_div)
        self.assertEqual(get_class_weight(node), 25)

    def test_scores_only_once(self):
        """Scoring is not cumulative within a class hit."""
        test_div = '<div class="post main">Content</div>'
        node = fragment_fromstring(test_div)
        self.assertEqual(get_class_weight(node), 25)


class TestUnlikelyNode(TestCase):
    """is_unlikely_node should help verify our node is good/bad."""

    def test_body_is_always_likely(self):
        """The body tag is always a likely node."""
        test_div = '<body class="comment"><div>Content</div></body>'
        node = fragment_fromstring(test_div)
        self.assertFalse(is_unlikely_node(node))

    def test_is_unlikely(self):
        "Keywords in the class/id will make us believe this is unlikely."
        test_div = '<div class="something comments">Content</div>'
        node = fragment_fromstring(test_div)
        self.assertTrue(is_unlikely_node(node))

        test_div = '<div id="comments">Content</div>'
        node = fragment_fromstring(test_div)
        self.assertTrue(is_unlikely_node(node))

    def test_not_unlikely(self):
        """Suck it double negatives."""
        test_div = '<div id="post">Content</div>'
        node = fragment_fromstring(test_div)
        self.assertFalse(is_unlikely_node(node))

        test_div = '<div class="something post">Content</div>'
        node = fragment_fromstring(test_div)
        self.assertFalse(is_unlikely_node(node))

    def test_maybe_hits(self):
        """We've got some maybes that will overrule an unlikely node."""
        test_div = '<div id="comments" class="article">Content</div>'
        node = fragment_fromstring(test_div)
        self.assertFalse(is_unlikely_node(node))


class TestScoredNode(TestCase):
    """ScoredNodes constructed have initial content_scores, etc."""

    def test_hash_id(self):
        """ScoredNodes have a hash_id based on their content

        Since this is based on the html there are chances for collisions, but
        it helps us follow and identify nodes through the scoring process. Two
        identical nodes would score the same, so meh all good.

        """
        test_div = '<div id="comments" class="article">Content</div>'
        node = fragment_fromstring(test_div)
        snode = ScoredNode(node)
        self.assertEqual(snode.hash_id, 'ffa4c519')

    def test_div_content_score(self):
        """A div starts out with a score of 5 and modifies from there"""
        test_div = '<div id="" class="">Content</div>'
        node = fragment_fromstring(test_div)
        snode = ScoredNode(node)
        self.assertEqual(snode.content_score, 5)

        test_div = '<div id="article" class="">Content</div>'
        node = fragment_fromstring(test_div)
        snode = ScoredNode(node)
        self.assertEqual(snode.content_score, 30)

        test_div = '<div id="comments" class="">Content</div>'
        node = fragment_fromstring(test_div)
        snode = ScoredNode(node)
        self.assertEqual(snode.content_score, -20)

    def test_headings_score(self):
        """Heading tags aren't likely candidates, hurt their scores."""
        test_div = '<h2>Heading</h2>'
        node = fragment_fromstring(test_div)
        snode = ScoredNode(node)
        self.assertEqual(snode.content_score, -5)

    def test_list_items(self):
        """Heading tags aren't likely candidates, hurt their scores."""
        test_div = '<li>list item</li>'
        node = fragment_fromstring(test_div)
        snode = ScoredNode(node)
        self.assertEqual(snode.content_score, -3)


class TestScoreCandidates(TestCase):
    """The grand daddy of tests to make sure our scoring works

    Now scoring details will change over time, so the most important thing is
    to make sure candidates come out in the right order, not necessarily how
    they scored. Make sure to keep this in mind while getting tests going.

    """

    def test_simple_candidate_set(self):
        """Tests a simple case of two candidate nodes"""
        doc = """
            <html>
            <body>
                <div class="content">
                    <p>This is a great amount of info</p>
                    <p>And more content <a href="/index">Home</a>
                </div>
                <div class="footer">
                    <p>This is a footer</p>
                    <p>And more content <a href="/index">Home</a>
                </div>
            </body>
            </html>
        """
        d_elem = document_fromstring(doc)
        divs = d_elem.findall(".//div")
        f_elem = divs[0]
        s_elem = divs[1]

        res = score_candidates([f_elem, s_elem])
        ordered = sorted([c for c in res.values()],
                          key=attrgetter('content_score'),
                          reverse=True)

        # the body element should have a higher score
        self.assertTrue(ordered[0].node.tag == 'body')

        # the html element is the outer should come in second
        self.assertTrue(ordered[1].node.tag == 'html')
