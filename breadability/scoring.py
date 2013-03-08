# -*- coding: utf8 -*-

"""Handle dealing with scoring nodes and content for our parsing."""

from __future__ import absolute_import

import re
import logging

from hashlib import md5
from lxml.etree import tostring
from ._py3k import to_bytes

# A series of sets of attributes we check to help in determining if a node is
# a potential candidate or not.
CLS_UNLIKELY = re.compile(('combx|comment|community|disqus|extra|foot|header|'
    'menu|remark|rss|shoutbox|sidebar|sponsor|ad-break|agegate|pagination|'
    'pager|perma|popup|tweet|twitter'), re.I)
CLS_MAYBE = re.compile('and|article|body|column|main|shadow', re.I)
CLS_WEIGHT_POSITIVE = re.compile(('article|body|content|entry|hentry|main|'
    'page|pagination|post|text|blog|story'), re.I)
CLS_WEIGHT_NEGATIVE = re.compile(('combx|comment|com-|contact|foot|footer|'
    'footnote|head|masthead|media|meta|outbrain|promo|related|scroll|shoutbox|'
    'sidebar|sponsor|shopping|tags|tool|widget'), re.I)

logger = logging.getLogger("breadability")


def check_node_attr(node, attr, checkset):
    value = node.get(attr) or ""
    check = checkset.search(value)
    if check:
        return True
    else:
        return False


def generate_hash_id(node):
    """
    Generates a hash_id for the node in question.

    :param node: lxml etree node
    """
    try:
        content = tostring(node)
    except Exception as e:
        logger.exception("Generating of hash failed")
        content = to_bytes(repr(node))

    hash_id = md5(content).hexdigest()
    return hash_id[:8]


def get_link_density(node, node_text=None):
    """Generate a value for the number of links in the node.

    :param node: pared elementree node
    :param node_text: if we already have the text_content() make this easier
    on us.
    :returns float:

    """
    link_length = sum([len(a.text_content()) or 0
        for a in node.findall(".//a")])
    if node_text:
        text_length = len(node_text)
    else:
        text_length = len(node.text_content())
    return float(link_length) / max(text_length, 1)


def get_class_weight(node):
    """Get an elements class/id weight.

    We're using sets to help efficiently check for existence of matches.

    """
    weight = 0
    if check_node_attr(node, 'class', CLS_WEIGHT_NEGATIVE):
        weight = weight - 25
    if check_node_attr(node, 'class', CLS_WEIGHT_POSITIVE):
        weight = weight + 25

    if check_node_attr(node, 'id', CLS_WEIGHT_NEGATIVE):
        weight = weight - 25
    if check_node_attr(node, 'id', CLS_WEIGHT_POSITIVE):
        weight = weight + 25

    return weight


def is_unlikely_node(node):
    """Short helper for checking unlikely status.

    If the class or id are in the unlikely list, and there's not also a
    class/id in the likely list then it might need to be removed.

    """
    unlikely = check_node_attr(node, 'class', CLS_UNLIKELY) or \
        check_node_attr(node, 'id', CLS_UNLIKELY)

    maybe = check_node_attr(node, 'class', CLS_MAYBE) or \
        check_node_attr(node, 'id', CLS_MAYBE)

    if unlikely and not maybe and node.tag != 'body':
        return True
    else:
        return False


def score_candidates(nodes):
    """Given a list of potential nodes, find some initial scores to start"""
    MIN_HIT_LENTH = 25
    candidates = {}

    for node in nodes:
        logger.debug("Scoring Node")

        content_score = 0
        # if the node has no parent it knows of, then it ends up creating a
        # body and html tag to parent the html fragment.
        parent = node.getparent()
        grand = parent.getparent() if parent is not None else None
        innertext = node.text_content()

        if parent is None or grand is None:
            logger.debug("Skipping candidate because parent/grand are none")
            continue

        # If this paragraph is less than 25 characters, don't even count it.
        if innertext and len(innertext) < MIN_HIT_LENTH:
            logger.debug("Skipping candidate because not enough content.")
            continue

        # Initialize readability data for the parent.
        # if the parent node isn't in the candidate list, add it
        if parent not in candidates:
            candidates[parent] = ScoredNode(parent)

        if grand not in candidates:
            candidates[grand] = ScoredNode(grand)

        # Add a point for the paragraph itself as a base.
        content_score += 1

        if innertext:
            # Add 0.25 points for any commas within this paragraph
            content_score += innertext.count(',') * 0.25
            logger.debug("Bonus points for ,: " + str(innertext.count(',')))

            # Subtract 0.5 points for each double quote within this paragraph
            content_score += innertext.count('"') * (-0.5)
            logger.debug('Penalty points for ": ' + str(innertext.count('"')))

            # For every 100 characters in this paragraph, add another point.
            # Up to 3 points.
            length_points = len(innertext) // 100

            if length_points > 3:
                content_score += 3
            else:
                content_score += length_points
            logger.debug("Length/content points: %r : %r", length_points,
                content_score)

        # Add the score to the parent.
        logger.debug("From this current node.")
        candidates[parent].content_score += content_score
        logger.debug("Giving parent bonus points: %r", candidates[parent].content_score)
        # The grandparent gets half.
        logger.debug("Giving grand bonus points")
        candidates[grand].content_score += (content_score / 2.0)
        logger.debug("Giving grand bonus points: %r", candidates[grand].content_score)

    for candidate in candidates.values():
        adjustment = 1 - get_link_density(candidate.node)
        logger.debug("Getting link density adjustment: %r * %r",
            candidate.content_score, adjustment)
        candidate.content_score = candidate.content_score * (adjustment)

    return candidates


class ScoredNode(object):
    """We need Scored nodes we use to track possible article matches

    We might have a bunch of these so we use __slots__ to keep memory usage
    down.

    """
    __slots__ = ['node', 'content_score']

    def __repr__(self):
        """Helpful representation of our Scored Node"""
        return "{0}: {1:0.1F}\t{2}".format(
            self.hash_id,
            self.content_score,
            self.node)

    def __init__(self, node):
        """Given node, set an initial score and weigh based on css and id"""
        self.node = node
        content_score = 0
        if node.tag in ['div', 'article']:
            content_score = 5

        if node.tag in ['pre', 'td', 'blockquote']:
            content_score = 3

        if node.tag in ['address', 'ol', 'ul', 'dl', 'dd', 'dt', 'li',
            'form']:
            content_score = -3
        if node.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'th']:
            content_score = -5

        content_score += get_class_weight(node)
        self.content_score = content_score

    @property
    def hash_id(self):
        return generate_hash_id(self.node)
