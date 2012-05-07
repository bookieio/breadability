"""Handle dealing with scoring nodes and content for our parsing."""
import re

from breadability.logconfig import LOG

# A series of sets of attributes we check to help in determining if a node is
# a potential candidate or not.
CLS_UNLIKELY = re.compile(('combx|comment|community|disqus|extra|foot|header|'
    'menu|remark|rss|shoutbox|sidebar|sponsor|ad-break|agegate|pagination|'
    'pager|popup|tweet|twitter'), re.I)
CLS_MAYBE = re.compile('and|article|body|column|main|shadow', re.I)
CLS_WEIGHT_POSITIVE = re.compile(('article|body|content|entry|hentry|main|'
    'page|pagination|post|text|blog|story'), re.I)
CLS_WEIGHT_NEGATIVE = re.compile(('combx|comment|com-|contact|foot|footer|'
    'footnote|masthead|media|meta|outbrain|promo|related|scroll|shoutbox|'
    'sidebar|sponsor|shopping|tags|tool|widget'), re.I)


def check_node_attr(node, attr, checkset):
    value = node.get(attr) or ""
    check = checkset.search(value)
    if check:
        return True
    else:
        return False


def get_link_density(node):
    """Generate a value for the number of links in the node.

    :param node: pared elementree node
    :returns float:

    """
    link_length = sum([len(a.text_content()) or 0 for a in node.findall(".//a")])
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
        content_score = 0
        parent = node.getparent()
        grand = parent.getparent() if parent is not None else None
        innertext = node.text_content()

        if parent is None or grand is None:
            LOG.debug("Skipping candidate because parent/grand are none")
            continue

        # If this paragraph is less than 25 characters, don't even count it.
        if innertext and len(innertext) < MIN_HIT_LENTH:
            LOG.debug("Skipping candidate because not enough content.")
            continue

        # Initialize readability data for the parent.
        # if the parent node isn't in the candidate list, add it
        if parent not in candidates:
            candidates[parent] = ScoredNode(parent)

        if grand not in candidates:
            candidates[grand] = ScoredNode(grand)

        # Add a point for the paragraph itself as a base.
        content_score += 1

        # Add points for any commas within this paragraph
        content_score += innertext.count(',') if innertext else 0

        # For every 100 characters in this paragraph, add another point. Up to
        # 3 points.
        length_points = len(innertext) % 100 if innertext else 0
        content_score = length_points if length_points > 3 else 3

        # Add the score to the parent.
        candidates[parent].content_score += content_score
        # The grandparent gets half.
        candidates[grand].content_score += content_score / 2.0

        for candidate in candidates.values():
            candidate.content_score = candidate.content_score * (1 -
                    get_link_density(candidate.node))

    return candidates


class ScoredNode(object):
    """We need Scored nodes we use to track possible article matches

    We might have a bunch of these so we use __slots__ to keep memory usage
    down.

    """
    __slots__ = ['node', 'content_score']

    def __repr__(self):
        """Helpful representation of our Scored Node"""
        return "{0:0.1F}\t{1}".format(self.content_score, self.node)

    def __init__(self, node):
        """Given node, set an initial score and weigh based on css and id"""
        self.node = node
        content_score = 0
        if node.tag == 'div':
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
