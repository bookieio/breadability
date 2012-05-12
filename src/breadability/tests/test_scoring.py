import re

from lxml.html import fragment_fromstring
from unittest import TestCase

from breadability.readable import Article
from breadability.scoring import check_node_attr
from breadability.scoring import get_class_weight
from breadability.readable import get_link_density
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


