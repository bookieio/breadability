# -*- coding: utf8 -*-

from __future__ import absolute_import

import re
import logging

from operator import attrgetter
from pprint import PrettyPrinter
from lxml.html.clean import Cleaner
from lxml.etree import tounicode, tostring
from lxml.html import fragment_fromstring, fromstring

from .document import OriginalDocument
from .scoring import (score_candidates, get_link_density, get_class_weight,
    is_unlikely_node)
from .utils import cached_property


html_cleaner = Cleaner(scripts=True, javascript=True, comments=True,
    style=True, links=True, meta=False, add_nofollow=False,
    page_structure=False, processing_instructions=True,
    embedded=False, frames=False, forms=False,
    annoying_tags=False, remove_tags=None, kill_tags=("noscript", "iframe"),
    remove_unknown_tags=False, safe_attrs_only=False)


SCORABLE_TAGS = ("div", "p", "td", "pre", "article")
NULL_DOCUMENT = """
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html;charset=UTF-8">
    </head>
    <body>
    </body>
</html>
"""

logger = logging.getLogger("readability")


def ok_embedded_video(node):
    """Check if this embed/video is an ok one to count."""
    good_keywords = ('youtube', 'blip.tv', 'vimeo')

    node_str = tounicode(node)
    for key in good_keywords:
        if key in node_str:
            return True

    return False


def build_base_document(dom, return_fragment=True):
    """
    Builds a base document with the body as root.

    :param dom: Parsed lxml tree (Document Object Model).
    :param bool return_fragment: If True only <div> fragment is returned.
        Otherwise full HTML document is returned.
    """
    body_element = dom.find(".//body")

    if body_element is None:
        fragment = fragment_fromstring('<div id="readabilityBody"/>')
        fragment.append(dom)
    else:
        body_element.tag = "div"
        body_element.set("id", "readabilityBody")
        fragment = body_element

    return document_from_fragment(fragment, return_fragment)


def build_error_document(dom, return_fragment=True):
    """
    Builds an empty erorr document with the body as root.

    :param bool return_fragment: If True only <div> fragment is returned.
        Otherwise full HTML document is returned.
    """
    fragment = fragment_fromstring(
        '<div id="readabilityBody" class="parsing-error"/>')

    return document_from_fragment(fragment, return_fragment)


def document_from_fragment(fragment, return_fragment):
    if return_fragment:
        document = fragment
    else:
        document = fromstring(NULL_DOCUMENT)
        body_element = document.find(".//body")
        body_element.append(fragment)

    document.doctype = "<!DOCTYPE html>"
    return document


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
            logger.debug('Sibling is the node so append')
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
                append = True
            elif content_length < 80 and link_density == 0:
                if ". " in content:
                    append = True

        if append:
            logger.debug('Sibling being appended')
            if sibling.tag not in ('div', 'p'):
                # We have a node that isn't a common block level element, like
                # a form or td tag. Turn it into a div so it doesn't get
                # filtered out later by accident.
                sibling.tag = 'div'

            candidate_node.node.append(sibling)

    return candidate_node


def clean_document(node):
    """Clean up the final document we return as the readable article"""
    if node is None or len(node) == 0:
        return

    logger.debug("Processing doc")
    clean_list = ['object', 'h1']
    to_drop = []

    # If there is only one h2, they are probably using it as a header and
    # not a subheader, so remove it since we already have a header.
    if len(node.findall('.//h2')) == 1:
        logger.debug('Adding H2 to list of nodes to clean.')
        clean_list.append('h2')

    for n in node.iter():
        logger.debug("Cleaning iter node")
        # clean out any in-line style properties
        if 'style' in n.attrib:
            n.set('style', '')

        # remove all of the following tags
        # Clean a node of all elements of type "tag".
        # (Unless it's a youtube/vimeo video. People love movies.)
        is_embed = bool(n.tag in ('object', 'embed'))
        if n.tag in clean_list:
            allow = False

            # Allow youtube and vimeo videos through as people usually
            # want to see those.
            if is_embed:
                if ok_embedded_video(n):
                    allow = True

            if not allow:
                logger.debug("Dropping Node")
                to_drop.append(n)

        if n.tag in ('h1', 'h2', 'h3', 'h4'):
            # clean headings
            # if the heading has no css weight or a high link density,
            # remove it
            if get_class_weight(n) < 0 or get_link_density(n) > .33:
                logger.debug("Dropping <hX>, it's insignificant")
                to_drop.append(n)

        # clean out extra <p>
        if n.tag == 'p':
            # if the p has no children and has no content...well then down
            # with it.
            if not n.getchildren() and len(n.text_content()) < 5:
                logger.debug('Dropping extra <p>')
                to_drop.append(n)

        # finally try out the conditional cleaning of the target node
        if clean_conditionally(n):
            to_drop.append(n)

    drop_nodes_with_parents(to_drop)

    return node


def drop_nodes_with_parents(nodes):
    for node in nodes:
        if node.getparent() is not None:
            node.drop_tree()


def clean_conditionally(node):
    """Remove the clean_el if it looks like bad content based on rules."""
    target_tags = ('form', 'table', 'ul', 'div', 'p')

    logger.debug('Cleaning conditionally node.')

    if node.tag not in target_tags:
        # this is not the tag you're looking for
        logger.debug('Node cleared.')
        return

    weight = get_class_weight(node)
    # content_score = LOOK up the content score for this node we found
    # before else default to 0
    content_score = 0

    if weight + content_score < 0:
        logger.debug('Dropping conditional node')
        logger.debug('Weight + score < 0')
        return True

    if node.text_content().count(',') < 10:
        logger.debug("There aren't 10 ,s so we're processing more")

        # If there are not very many commas, and the number of
        # non-paragraph elements is more than paragraphs or other ominous
        # signs, remove the element.
        p = len(node.findall('.//p'))
        img = len(node.findall('.//img'))
        li = len(node.findall('.//li')) - 100
        inputs = len(node.findall('.//input'))

        embed = 0
        embeds = node.findall('.//embed')
        for e in embeds:
            if ok_embedded_video(e):
                embed += 1
        link_density = get_link_density(node)
        content_length = len(node.text_content())

        remove_node = False

        if li > p and node.tag != 'ul' and node.tag != 'ol':
            logger.debug('Conditional drop: li > p and not ul/ol')
            remove_node = True
        elif inputs > p / 3.0:
            logger.debug('Conditional drop: inputs > p/3.0')
            remove_node = True
        elif content_length < 25 and (img == 0 or img > 2):
            logger.debug('Conditional drop: len < 25 and 0/>2 images')
            remove_node = True
        elif weight < 25 and link_density > 0.2:
            logger.debug('Conditional drop: weight small and link is dense')
            remove_node = True
        elif weight >= 25 and link_density > 0.5:
            logger.debug('Conditional drop: weight big but link heavy')
            remove_node = True
        elif (embed == 1 and content_length < 75) or embed > 1:
            logger.debug('Conditional drop: embed w/o much content or many embed')
            remove_node = True

        if remove_node:
            logger.debug('Node will be removed')
        else:
            logger.debug('Node cleared')
        return remove_node

    # nope, don't remove anything
    logger.debug('Node Cleared final.')
    return False


def prep_article(doc):
    """Once we've found our target article we want to clean it up.

    Clean out:
    - inline styles
    - forms
    - strip empty <p>
    - extra tags
    """
    return clean_document(doc)


def find_candidates(document):
    """
    Finds cadidate nodes for the readable version of the article.

    Here's we're going to remove unlikely nodes, find scores on the rest,
    clean up and return the final best match.
    """
    nodes_to_score = set()
    should_remove = set()

    for node in document.iter():
        if is_unlikely_node(node):
            logger.debug("We should drop unlikely: %s", str(node))
            should_remove.add(node)
        elif is_bad_link(node):
            logger.debug("We should drop bad link: %s", str(node))
            should_remove.add(node)
        elif node.tag in SCORABLE_TAGS:
            nodes_to_score.add(node)

    return score_candidates(nodes_to_score), should_remove


def is_bad_link(node):
    """
    Helper to determine if the node is link that is useless.

    We've hit articles with many multiple links that should be cleaned out
    because they're just there to pollute the space. See tests for examples.
    """
    if node.tag != "a":
        return False

    name = node.get("name")
    href = node.get("href")
    if name and not href:
        return True

    if href:
        href_parts = href.split("#")
        if len(href_parts) == 2 and len(href_parts[1]) > 25:
            return True

    return False


class Article(object):
    """Parsed readable object"""
    _should_drop = ()

    def __init__(self, html, url=None, fragment=True):
        """Create the Article we're going to use.

        :param html: The string of html we're going to parse.
        :param url: The url so we can adjust the links to still work.
        :param fragment: Should we return a <div> fragment or
            a full <html> doc.
        """
        logger.debug('Url: ' + str(url))
        self.orig = OriginalDocument(html, url=url)
        self.fragment = fragment

    def __str__(self):
        return tostring(self._readable())

    def __unicode__(self):
        return tounicode(self._readable())

    @cached_property
    def dom(self):
        """Parsed lxml tree (Document Object Model) of the given html."""
        try:
            document = self.orig.html
            # cleaning doesn't return, just wipes in place
            html_cleaner(document)
            return leaf_div_elements_into_paragraphs(document)
        except ValueError:
            return None

    @cached_property
    def candidates(self):
        """Generates list of candidates from the DOM."""
        dom = self.dom
        if dom is None or len(dom) == 0:
            return None

        candidates, self._should_drop = find_candidates(dom)
        return candidates

    @cached_property
    def readable(self):
        return tounicode(self.readable_dom)

    @cached_property
    def readable_dom(self):
        return self._readable()

    def _readable(self):
        """The readable parsed article"""
        if not self.candidates:
            logger.warning("No candidates found in document.")
            return self._handle_no_candidates()

        # cleanup by removing the should_drop we spotted.
        drop_nodes_with_parents(self._should_drop)

        # right now we return the highest scoring candidate content
        best_candidates = sorted((c for c in self.candidates.values()),
            key=attrgetter("content_score"), reverse=True)

        printer = PrettyPrinter(indent=2)
        logger.debug(printer.pformat(best_candidates))

        # since we have several candidates, check the winner's siblings
        # for extra content
        winner = best_candidates[0]
        updated_winner = check_siblings(winner, self.candidates)
        logger.debug('Begin final prep of article')
        updated_winner.node = prep_article(updated_winner.node)
        if updated_winner.node is not None:
            doc = build_base_document(updated_winner.node, self.fragment)
        else:
            logger.warning('Had candidates but failed to find a cleaned winning doc.')
            doc = self._handle_no_candidates()

        return doc

    def _handle_no_candidates(self):
        """
        If we fail to find a good candidate we need to find something else.
        """
        # since we've not found a good candidate we're should help this
        if self.dom is not None and len(self.dom):
            # cleanup by removing the should_drop we spotted.
            drop_nodes_with_parents(self._should_drop)

            dom = prep_article(self.dom)
            return build_base_document(dom, self.fragment)
        else:
            logger.warning("No document to use.")
            return build_error_document(self.fragment)


def leaf_div_elements_into_paragraphs(document):
    """
    Turn all <div> elements that don't have children block level
    elements into <p> elements.

    Since we can't change the tree as we iterate over it, we must do this
    before we process our document.
    """
    for element in document.iter(tag="div"):
        child_tags = tuple(n.tag for n in element.getchildren())
        if "div" not in child_tags:
            logger.debug("Changing leaf <div> into <p>")
            element.tag = "p"

    return document