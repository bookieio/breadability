from lxml.html import fragment_fromstring
from unittest import TestCase

from breadability.scoring import check_node_attr


class TestCheckNodeAttr(TestCase):
    """Verify a node has a class/id in the given set.

    The idea is that we have sets of known good/bad ids and classes and need
    to verify the given node does/doesn't have those classes/ids.

    """
    def test_has_class(self):
        """Verify that a node has a class in our set."""
        test_set = set(['test1', 'test2'])
        test_node = fragment_fromstring('<div/>')
        test_node.set('class', 'test2 comment')

        self.assertTrue(check_node_attr(test_node, 'class', test_set))

    def test_has_id(self):
        """Verify that a node has an id in our set."""
        test_set = set(['test1', 'test2'])
        test_node = fragment_fromstring('<div/>')
        test_node.set('id', 'test2')

        self.assertTrue(check_node_attr(test_node, 'id', test_set))

    def test_lacks_class(self):
        """Verify that a node does not have a class in our set."""
        test_set = set(['test1', 'test2'])
        test_node = fragment_fromstring('<div/>')
        test_node.set('class', 'test4 comment')
        self.assertFalse(check_node_attr(test_node, 'class', test_set))

    def test_lacks_id(self):
        """Verify that a node does not have an id in our set."""
        test_set = set(['test1', 'test2'])
        test_node = fragment_fromstring('<div/>')
        test_node.set('id', 'test4')
        self.assertFalse(check_node_attr(test_node, 'id', test_set))
