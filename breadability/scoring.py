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
CLS_UNLIKELY = re.compile(
    "combx|comment|community|disqus|extra|foot|header|menu|remark|rss|shoutbox|"
    "sidebar|sponsor|ad-break|agegate|pagination|pager|perma|popup|tweet|"
    "twitter",
    re.IGNORECASE
)
CLS_MAYBE = re.compile(
    "and|article|body|column|main|shadow",
    re.IGNORECASE
)
CLS_WEIGHT_POSITIVE = re.compile(
    "article|body|content|entry|hentry|main|page|pagination|post|text|blog|"
    "story",
    re.IGNORECASE
)
CLS_WEIGHT_NEGATIVE = re.compile(
    "combx|comment|com-|contact|foot|footer|footnote|head|masthead|media|meta|"
    "outbrain|promo|related|scroll|shoutbox|sidebar|sponsor|shopping|tags|tool|"
    "widget",
    re.IGNORECASE
)

logger = logging.getLogger("breadability")


def check_node_attributes(pattern, node, *attributes):
    """
    Searches match in attributes against given pattern and if
    finds the match against any of them returns True.
    """
    for attribute_name in attributes:
        attribute = node.get(attribute_name)
        if attribute is not None and pattern.search(attribute):
            return True

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
    """
    Generates a value for the number of links in the node.

    :param node: pared elementree node
    :param node_text: if we already have the text_content() make
        this easier on us.
    :returns float:
    """
    link_length = sum(len(a.text_content()) or 0 for a in node.findall(".//a"))
    text_length = len(node_text if node_text else node.text_content())

    return float(link_length) / max(text_length, 1)


def get_class_weight(node):
    """
    Computes weight of element according to its class/id.

    We're using sets to help efficiently check for existence of matches.
    """
    weight = 0

    if check_node_attributes(CLS_WEIGHT_NEGATIVE, node, "class"):
        weight -= 25
    if check_node_attributes(CLS_WEIGHT_POSITIVE, node, "class"):
        weight += 25

    if check_node_attributes(CLS_WEIGHT_NEGATIVE, node, "id"):
        weight -= 25
    if check_node_attributes(CLS_WEIGHT_POSITIVE, node, "id"):
        weight += 25

    return weight


def is_unlikely_node(node):
    """
    Short helper for checking unlikely status.

    If the class or id are in the unlikely list, and there's not also a
    class/id in the likely list then it might need to be removed.
    """
    unlikely = check_node_attributes(CLS_UNLIKELY, node, "class", "id")
    maybe = check_node_attributes(CLS_MAYBE, node, "class", "id")

    return bool(unlikely and not maybe and node.tag != "body")


def score_candidates(nodes):
    """Given a list of potential nodes, find some initial scores to start"""
    MIN_HIT_LENTH = 25
    candidates = {}

    for node in nodes:
        logger.debug("Scoring Node")

        # if the node has no parent it knows of
        # then it ends up creating a body & html tag to parent the html fragment
        parent = node.getparent()
        if parent is None:
            logger.debug("Skipping node - parent node is none.")
            continue

        grand = parent.getparent()
        if grand is None:
            logger.debug("Skipping node - grand parent node is none.")
            continue

        # if paragraph is < `MIN_HIT_LENTH` characters don't even count it
        inner_text = node.text_content().strip()
        if len(inner_text) < MIN_HIT_LENTH:
            logger.debug("Skipping candidate because inner text is shorter than %d characters.", MIN_HIT_LENTH)
            continue

        # initialize readability data for the parent
        # add parent node if it isn't in the candidate list
        if parent not in candidates:
            candidates[parent] = ScoredNode(parent)

        if grand not in candidates:
            candidates[grand] = ScoredNode(grand)

        # add a point for the paragraph itself as a base
        content_score = 1

        if inner_text:
            # add 0.25 points for any commas within this paragraph
            commas_count = inner_text.count(",")
            content_score += commas_count * 0.25
            logger.debug("Bonus points for commas: %d", commas_count)

            # subtract 0.5 points for each double quote within this paragraph
            double_quotes_count = inner_text.count('"')
            content_score += double_quotes_count * -0.5
            logger.debug("Penalty points for double-quotes: %d", double_quotes_count)

            # for every 100 characters in this paragraph, add another point
            # up to 3 points
            length_points = len(inner_text) // 100
            content_score += min(length_points, 3)
            logger.debug("Length/content points: %d : %f", length_points, content_score)

        # add the score to the parent
        candidates[parent].content_score += content_score
        logger.debug("Giving parent bonus points: %f", candidates[parent].content_score)
        # the grand node gets half
        candidates[grand].content_score += content_score / 2.0
        logger.debug("Giving grand bonus points: %f", candidates[grand].content_score)

    for candidate in candidates.values():
        adjustment = 1 - get_link_density(candidate.node)
        logger.debug("Getting link density adjustment: %f * %f", candidate.content_score, adjustment)
        candidate.content_score = candidate.content_score * adjustment

    return candidates


class ScoredNode(object):
    """
    We need Scored nodes we use to track possible article matches

    We might have a bunch of these so we use __slots__ to keep memory usage
    down.
    """
    __slots__ = ('node', 'content_score')

    def __init__(self, node):
        """Given node, set an initial score and weigh based on css and id"""
        self.node = node
        self.content_score = 0

        if node.tag in ('div', 'article'):
            self.content_score = 5
        if node.tag in ('pre', 'td', 'blockquote'):
            self.content_score = 3

        if node.tag in ('address', 'ol', 'ul', 'dl', 'dd', 'dt', 'li', 'form'):
            self.content_score = -3
        if node.tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'th'):
            self.content_score = -5

        self.content_score += get_class_weight(node)

    @property
    def hash_id(self):
        return generate_hash_id(self.node)

    def __repr__(self):
        return "<ScoredNode: {0}, {1:0.1F} {2}>".format(
            self.hash_id,
            self.content_score,
            self.node
        )
