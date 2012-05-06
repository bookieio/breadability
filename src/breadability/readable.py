import re
from operator import attrgetter
from lxml.etree import tounicode
from lxml.etree import tostring
from lxml.html.clean import Cleaner
from lxml.html import fragment_fromstring
from lxml.html import fromstring
from pprint import PrettyPrinter

from breadability.document import OriginalDocument
from breadability.logconfig import LOG
from breadability.scoring import score_candidates
from breadability.scoring import get_link_density
from breadability.scoring import get_class_weight
from breadability.scoring import is_unlikely_node
from breadability.utils import cached_property


html_cleaner = Cleaner(scripts=True, javascript=True, comments=True,
                  style=True, links=True, meta=False, add_nofollow=False,
                  page_structure=False, processing_instructions=True,
                  embedded=False, frames=False, forms=False,
                  annoying_tags=False, remove_tags=None,
                  remove_unknown_tags=False, safe_attrs_only=False)


def drop_tag(doc, *tags):
    """Helper to just remove any nodes that match this html tag passed in

    :param *tags: one or more html tag strings to remove e.g. style, script

    """
    for tag in tags:
        found = doc.iterfind(".//" + tag)
        for n in found:
            LOG.debug("Dropping tag: " + str(n))
            n.drop_tree()
    return doc


def build_base_document(html):
    """Return a base document with the body as root.

    :param html: Parsed Element object

    """
    if html.tag == 'body':
        html.tag = 'div'
        found_body = html
    else:
        found_body = html.find('.//body')

    if found_body is None:
        fragment = fragment_fromstring('<div/>')
        fragment.set('id', 'readabilityBody')
        fragment.append(html)
        return fragment
    else:
        found_body.tag = 'div'
        found_body.set('id', 'readabilityBody')

    return found_body


def transform_misused_divs_into_paragraphs(doc):
    """Turn all divs that don't have children block level elements into p's

    Since we can't change the tree as we iterate over it, we must do this
    before we process our document.

    The idea is that we process all divs and if the div does not contain
    another list of divs, then we replace it with a p tag instead appending
    it's contents/children to it.

    """
    for elem in doc.iter(tag='div'):
        child_tags = [n.tag for n in elem.getchildren()]
        if 'div' not in child_tags:
            # if there is no div inside of this div...then it's a leaf
            # node in a sense.
            # We need to create a <p> and put all it's contents in there
            # We'll just stringify it, then regex replace the first/last
            # div bits to turn them into <p> vs <div>.
            LOG.debug('Turning leaf <div> into <p>')
            orig = tounicode(elem).strip()
            started = re.sub(r'^<\s*div', '<p', orig)
            ended = re.sub(r'div>$', 'p>', started)
            elem.getparent().replace(elem, fromstring(ended))
    return doc


def check_siblings(candidate_node, candidate_list):
    """Look through siblings for content that might also be related.

    Things like preambles, content split by ads that we removed, etc.

    """
    candidate_css = candidate_node.node.get('class')
    potential_target = candidate_node.content_score * 0.2
    sibling_target_score = potential_target if potential_target > 10 else 10
    parent = candidate_node.node.getparent()
    siblings = parent.getchildren() if parent is not None else []

    for sibling in siblings:
        append = False
        content_bonus = 0

        if sibling is candidate_node.node:
            append = True

        # Give a bonus if sibling nodes and top candidates have the example
        # same class name
        if candidate_css and sibling.get('class') == candidate_css:
            content_bonus += candidate_node.content_score * 0.2

        if sibling in candidate_list:
            adjusted_score = candidate_list[sibling].content_score + \
                content_bonus

            if adjusted_score >= sibling_target_score:
                append = True

        if sibling.tag == 'p':
            link_density = get_link_density(sibling)
            content = sibling.text_content()
            content_length = len(content)

            if content_length > 80 and link_density < 0.25:
                append = true
            elif content_length < 80 and link_density == 0:
                if ". " in content:
                    append = True

        if append:
            LOG.debug('Sibling being appended' + str(sibling))
            if sibling.tag not in ['div', 'p']:
                # We have a node that isn't a common block level element, like
                # a form or td tag. Turn it into a div so it doesn't get
                # filtered out later by accident.
                sibling.tag = 'div'

            candidate_node.node.append(sibling)

    return candidate_node


def prep_article(doc):
    """Once we've found our target article we want to clean it up.

    Clean out:
    - inline styles
    - forms
    - strip empty <p>
    - extra tags

    """
    def clean_document(node):
        """Clean up the final document we return as the readable article"""
        LOG.debug('Cleaning document')
        clean_list = ['object', 'h1']
        keep_keywords = ['youtube', 'blip.tv', 'vimeo']

        # If there is only one h2, they are probably using it as a header and
        # not a subheader, so remove it since we already have a header.
        if len(node.findall('.//h2')) == 1:
            LOG.debug('Adding H2 to list of nodes to clean.')
            clean_list.append('h2')

        for n in node.iter():
            # clean out any incline style properties
            if 'style' in n.attrib:
                n.set('style', '')

            # remove all of the following tags
            # Clean a node of all elements of type "tag".
            # (Unless it's a youtube/vimeo video. People love movies.)
            is_embed = True if n.tag in ['object', 'embed'] else False
            if n.tag in clean_list:
                allow = False

                # Allow youtube and vimeo videos through as people usually
                # want to see those.
                if is_embed:
                    # if this object or embed has any of the keywords in the
                    # html from here on out, then let it live.
                    node_str = tounicode(n)

                    for key in keep_keywords:
                        if not allow and key in node_str:
                            allow = True
                if not allow:
                    LOG.debug('Dropping node: ' + str(n))
                    n.drop_tree()
                    # go on with next loop, this guy is gone
                    continue

            if n.tag in ['h1', 'h2', 'h3', 'h4']:
                # clean headings
                # if the heading has no css weight or a high link density,
                # remove it
                if get_class_weight(n) < 0 or get_link_density(n) > .33:
                    # for some reason we get nodes here without a parent
                    if n.getparent() is not None:
                        LOG.debug(
                            "Dropping <hX>, it's insignificant: " + str(n))
                        n.drop_tree()
                        # go on with next loop, this guy is gone
                        continue


            # clean out extra <p>
            if n.tag == 'p':
                # if the p has no children and has no content...well then down
                # with it.
                if not n.getchildren() and len(n.text_content()) < 5:
                    LOG.debug('Dropping extra <p>: ' + str(n))
                    n.drop_tree()
                    # go on with next loop, this guy is gone
                    continue
        return node

    def clean_conditionally(doc, clean_el):
        """Remove the clean_el if it looks like bad content based on rules."""

    doc = clean_document(doc)
    return doc


def find_candidates(doc):
    """Find cadidate nodes for the readable version of the article.

    Here's we're going to remove unlikely nodes, find scores on the rest, and
    clean up and return the final best match.

    """
    scorable_node_tags = ['p', 'td', 'pre']
    nodes_to_score = []

    for node in doc.iter():
        if is_unlikely_node(node):
            LOG.debug('Dropping unlikely: ' + str(node))
            node.drop_tree()
        elif node.tag in scorable_node_tags:
            nodes_to_score.append(node)
    return score_candidates(nodes_to_score)


class Article(object):
    """Parsed readable object"""

    def __init__(self, html, url=None):
        LOG.debug('Url: ' + str(url))
        self.orig = OriginalDocument(html, url=url)

    def __str__(self):
        return tostring(self.readable)

    def __unicode__(self):
        return tounicode(self.readable)

    @cached_property(ttl=600)
    def readable(self):
        """The readable parsed article"""
        doc = self.orig.html
        # cleaning doesn't return, just wipes in place
        html_cleaner(doc)
        doc = drop_tag(doc, 'noscript')
        doc = transform_misused_divs_into_paragraphs(doc)
        candidates = find_candidates(doc)

        if candidates:
            LOG.debug('Candidates found:')
            pp = PrettyPrinter(indent=2)
            LOG.debug(pp.pformat(candidates))

            # right now we return the highest scoring candidate content
            by_score = sorted([c for c in candidates.values()],
                key=attrgetter('content_score'), reverse=True)

            # since we have several candidates, check the winner's siblings
            # for extra content
            winner = by_score[0]
            LOG.debug('Selected winning node: ' + str(winner))
            updated_winner = check_siblings(winner, candidates)
            LOG.debug('Begin final prep of article')
            updated_winner.node = prep_article(updated_winner.node)
            doc = build_base_document(updated_winner.node)
        else:
            LOG.warning('No candidates found: using document.')
            LOG.debug('Begin final prep of article')
            doc = prep_article(doc)
            doc = build_base_document(doc)

        return doc
