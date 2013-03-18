# -*- coding: utf8 -*-

"""Generate a clean nice starting html document to process for an article."""

from __future__ import absolute_import

import re
import logging
import charade

from lxml.etree import tostring, tounicode, XMLSyntaxError
from lxml.html import document_fromstring, HTMLParser

from ._py3k import unicode, to_string, to_bytes
from .utils import cached_property


logger = logging.getLogger("readability")


def determine_encoding(page):
    encoding = "utf8"
    text = re.sub(to_bytes(r"</?[^>]*>\s*"), to_bytes(" "), page)

    # don't venture to guess
    if not text.strip() or len(text) < 10:
        return encoding

    # try enforce UTF-8
    diff = text.decode(encoding, "ignore").encode(encoding)
    sizes = len(diff), len(text)

    # 99% of UTF-8
    if abs(len(text) - len(diff)) < max(sizes) * 0.01:
        return encoding

    # try detect encoding
    encoding_detector = charade.detect(text)
    if encoding_detector["encoding"]:
        encoding = encoding_detector["encoding"]

    return encoding


MULTIPLE_BR_TAGS_PATTERN = re.compile(r"(?:<br[^>]*>\s*){2,}", re.IGNORECASE)
def replace_multi_br_to_paragraphs(html):
    """Converts multiple <br> tags into paragraphs."""
    logger.debug("Replacing multiple <br/> to <p>")

    return MULTIPLE_BR_TAGS_PATTERN.sub("</p><p>", html)


UTF8_PARSER = HTMLParser(encoding="utf8")
def build_document(html_content, base_href=None):
    """Requires that the `html_content` not be None"""
    assert html_content is not None

    if isinstance(html_content, unicode):
        html_content = html_content.encode("utf8", "replace")

    try:
        document = document_fromstring(html_content, parser=UTF8_PARSER)
    except XMLSyntaxError:
        raise ValueError("Failed to parse document contents.")

    if base_href:
        document.make_links_absolute(base_href, resolve_base_href=True)
    else:
        document.resolve_base_href()

    return document


class OriginalDocument(object):
    """The original document to process"""

    def __init__(self, html, url=None):
        self.orig_html = html
        self.url = url

    def __str__(self):
        """Render out our document as a string"""
        return to_string(tostring(self.html))

    def __unicode__(self):
        """Render out our document as a string"""
        return tounicode(self.html)

    def _parse(self, html):
        """Generate an lxml document from html."""
        html = replace_multi_br_to_paragraphs(html)
        document = build_document(html, self.url)

        return document

    @cached_property
    def html(self):
        """The parsed html document from the input"""
        return self._parse(self.orig_html)

    @cached_property
    def links(self):
        """Links within the document"""
        return self.html.findall(".//a")

    @cached_property
    def title(self):
        """Pull the title attribute out of the parsed document"""
        title_element = self.html.find(".//title")
        if title_element is None or title_element.text is None:
            return ""
        else:
            return title_element.text.strip()
