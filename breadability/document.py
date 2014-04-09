# -*- coding: utf8 -*-

"""Generate a clean nice starting html document to process for an article."""

from __future__ import absolute_import

import re
import logging
import chardet

from lxml.etree import (
    tounicode,
    XMLSyntaxError,
)
from lxml.html import (
    document_fromstring,
    HTMLParser,
)

from ._compat import (
    to_bytes,
    to_unicode,
    unicode,
    unicode_compatible,
)
from .utils import (
    cached_property,
    ignored,
)


logger = logging.getLogger("breadability")


TAG_MARK_PATTERN = re.compile(to_bytes(r"</?[^>]*>\s*"))
UTF8_PARSER = HTMLParser(encoding="utf8")
CHARSET_META_TAG_PATTERN = re.compile(
    br"""<meta[^>]+charset=["']?([^'"/>\s]+)""",
    re.IGNORECASE
)


def decode_html(html):
    """
    Converts bytes stream containing an HTML page into Unicode.
    Tries to guess character encoding from meta tag of by "chardet" library.
    """
    if isinstance(html, unicode):
        return html

    match = CHARSET_META_TAG_PATTERN.search(html)
    if match:
        declared_encoding = match.group(1).decode("ASCII")
        # proceed unknown encoding as if it wasn't found at all
        with ignored(LookupError):
            return html.decode(declared_encoding, "ignore")

    # try to enforce UTF-8 firstly
    with ignored(UnicodeDecodeError):
        return html.decode("utf8")

    text = TAG_MARK_PATTERN.sub(to_bytes(" "), html)
    diff = text.decode("utf8", "ignore").encode("utf8")
    sizes = len(diff), len(text)

    # 99% of text is UTF-8
    if abs(len(text) - len(diff)) < max(sizes) * 0.01:
        return html.decode("utf8", "ignore")

    # try detect encoding
    encoding = "utf8"
    encoding_detector = chardet.detect(text)
    if encoding_detector["encoding"]:
        encoding = encoding_detector["encoding"]

    return html.decode(encoding, "ignore")


BREAK_TAGS_PATTERN = re.compile(
    to_unicode(r"(?:<\s*[bh]r[^>]*>\s*)+"),
    re.IGNORECASE
)


def convert_breaks_to_paragraphs(html):
    """
    Converts <hr> tag and multiple <br> tags into paragraph.
    """
    logger.debug("Converting multiple <br> & <hr> tags into <p>.")

    return BREAK_TAGS_PATTERN.sub(_replace_break_tags, html)


def _replace_break_tags(match):
    tags = match.group()

    if to_unicode("<hr") in tags:
        return to_unicode("</p><p>")
    elif tags.count(to_unicode("<br")) > 1:
        return to_unicode("</p><p>")
    else:
        return tags


def build_document(html_content, base_href=None):
    """Requires that the `html_content` not be None"""
    assert html_content is not None

    if isinstance(html_content, unicode):
        html_content = html_content.encode("utf8", "xmlcharrefreplace")

    try:
        document = document_fromstring(html_content, parser=UTF8_PARSER)
    except XMLSyntaxError:
        raise ValueError("Failed to parse document contents.")

    if base_href:
        document.make_links_absolute(base_href, resolve_base_href=True)
    else:
        document.resolve_base_href()

    return document


@unicode_compatible
class OriginalDocument(object):
    """The original document to process."""

    def __init__(self, html, url=None):
        self._html = html
        self._url = url

    @property
    def url(self):
        """Source URL of HTML document."""
        return self._url

    def __unicode__(self):
        """Renders the document as a string."""
        return tounicode(self.dom)

    @cached_property
    def dom(self):
        """Parsed HTML document from the input."""
        html = self._html
        if not isinstance(html, unicode):
            html = decode_html(html)

        html = convert_breaks_to_paragraphs(html)
        document = build_document(html, self._url)

        return document

    @cached_property
    def links(self):
        """Links within the document."""
        return self.dom.findall(".//a")

    @cached_property
    def title(self):
        """Title attribute of the parsed document."""
        title_element = self.dom.find(".//title")
        if title_element is None or title_element.text is None:
            return ""
        else:
            return title_element.text.strip()
