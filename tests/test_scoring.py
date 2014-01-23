# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import re

from operator import attrgetter
from lxml.html import document_fromstring
from lxml.html import fragment_fromstring
from breadability.readable import Article
from breadability.scoring import (
    check_node_attributes,
    generate_hash_id,
    get_class_weight,
    score_candidates,
    ScoredNode,
)
from breadability.readable import (
    get_link_density,
    is_unlikely_node,
)
from .compat import unittest
from .utils import load_snippet


class TestHashId(unittest.TestCase):
    def test_generate_hash(self):
        dom = fragment_fromstring("<div>ľščťžýáí</div>")
        generate_hash_id(dom)

    def test_hash_from_id_on_exception(self):
        generate_hash_id(None)

    def test_different_hashes(self):
        dom = fragment_fromstring("<div>ľščťžýáí</div>")
        hash_dom = generate_hash_id(dom)
        hash_none = generate_hash_id(None)

        self.assertNotEqual(hash_dom, hash_none)

    def test_equal_hashes(self):
        dom1 = fragment_fromstring("<div>ľščťžýáí</div>")
        dom2 = fragment_fromstring("<div>ľščťžýáí</div>")
        hash_dom1 = generate_hash_id(dom1)
        hash_dom2 = generate_hash_id(dom2)
        self.assertEqual(hash_dom1, hash_dom2)

        hash_none1 = generate_hash_id(None)
        hash_none2 = generate_hash_id(None)
        self.assertEqual(hash_none1, hash_none2)


class TestCheckNodeAttr(unittest.TestCase):
    """Verify a node has a class/id in the given set.

    The idea is that we have sets of known good/bad ids and classes and need
    to verify the given node does/doesn't have those classes/ids.

    """
    def test_has_class(self):
        """Verify that a node has a class in our set."""
        test_pattern = re.compile('test1|test2', re.I)
        test_node = fragment_fromstring('<div/>')
        test_node.set('class', 'test2 comment')

        self.assertTrue(
            check_node_attributes(test_pattern, test_node, 'class'))

    def test_has_id(self):
        """Verify that a node has an id in our set."""
        test_pattern = re.compile('test1|test2', re.I)
        test_node = fragment_fromstring('<div/>')
        test_node.set('id', 'test2')

        self.assertTrue(check_node_attributes(test_pattern, test_node, 'id'))

    def test_lacks_class(self):
        """Verify that a node does not have a class in our set."""
        test_pattern = re.compile('test1|test2', re.I)
        test_node = fragment_fromstring('<div/>')
        test_node.set('class', 'test4 comment')
        self.assertFalse(
            check_node_attributes(test_pattern, test_node, 'class'))

    def test_lacks_id(self):
        """Verify that a node does not have an id in our set."""
        test_pattern = re.compile('test1|test2', re.I)
        test_node = fragment_fromstring('<div/>')
        test_node.set('id', 'test4')
        self.assertFalse(check_node_attributes(test_pattern, test_node, 'id'))


class TestLinkDensity(unittest.TestCase):
    """Verify we calc our link density correctly."""

    def test_empty_node(self):
        """An empty node doesn't have much of a link density"""
        doc = Article("<div></div>")
        self.assertEqual(get_link_density(doc.readable_dom), 0.0)

    def test_small_doc_no_links(self):
        doc = Article(load_snippet('document_min.html'))
        self.assertEqual(get_link_density(doc.readable_dom), 0.0)

    def test_several_links(self):
        """This doc has a 3 links with the majority of content."""
        doc = Article(load_snippet('document_absolute_url.html'))
        self.assertAlmostEqual(get_link_density(doc.readable_dom), 22/37)


class TestClassWeight(unittest.TestCase):
    """Verify we score nodes correctly based on their class/id attributes."""

    def test_no_matches_zero(self):
        """If you don't have the attribute then you get a weight of 0"""
        node = fragment_fromstring("<div></div>")
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


class TestUnlikelyNode(unittest.TestCase):
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


class TestScoredNode(unittest.TestCase):
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


class TestScoreCandidates(unittest.TestCase):
    """The grand daddy of tests to make sure our scoring works

    Now scoring details will change over time, so the most important thing is
    to make sure candidates come out in the right order, not necessarily how
    they scored. Make sure to keep this in mind while getting tests going.

    """

    def test_simple_candidate_set(self):
        """Tests a simple case of two candidate nodes"""
        html = """
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
        dom = document_fromstring(html)
        div_nodes = dom.findall(".//div")

        candidates = score_candidates(div_nodes)
        ordered = sorted(
            (c for c in candidates.values()), reverse=True,
            key=attrgetter("content_score"))

        self.assertEqual(ordered[0].node.tag, "div")
        self.assertEqual(ordered[0].node.attrib["class"], "content")
        self.assertEqual(ordered[1].node.tag, "body")
        self.assertEqual(ordered[2].node.tag, "html")
        self.assertEqual(ordered[3].node.tag, "div")
        self.assertEqual(ordered[3].node.attrib["class"], "footer")
