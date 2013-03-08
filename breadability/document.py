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


utf8_parser = HTMLParser(encoding='utf-8')
logger = logging.getLogger("breadability")


def get_encoding(page):
    encoding = 'utf-8'
    text = re.sub(to_bytes('</?[^>]*>\s*'), to_bytes(' '), page)

    # don't veture to guess
    if not text.strip() or len(text) < 10:
        return encoding

    try:
        diff = text.decode(encoding, 'ignore').encode(encoding)
        sizes = len(diff), len(text)

        # 99% of utf-8
        if abs(len(text) - len(diff)) < max(sizes) * 0.01:
            return encoding
    except UnicodeDecodeError:
        pass

    encoding_detector = charade.detect(text)
    encoding = encoding_detector['encoding']

    if not encoding:
        encoding = 'utf-8'
    elif encoding == 'MacCyrillic':
        encoding = 'cp1251'

    return encoding

MULTIPLE_BR_TAGS_PATTERN = re.compile(r"(?:<br[^>]*>\s*){2,}", re.IGNORECASE)
def replace_multi_br_to_paragraphs(html):
    """Converts multiple <br> tags into paragraphs."""
    logger.debug('Replacing multiple <br/> to <p>')

    return MULTIPLE_BR_TAGS_PATTERN.sub('</p><p>', html)


def build_doc(page):
    """Requires that the `page` not be None"""
    if page is None:
        logger.error("Page content is None, can't build_doc")
        return ''

    if isinstance(page, unicode):
        page_unicode = page
    else:
        encoding = get_encoding(page)
        page_unicode = page.decode(encoding, 'replace')

    try:
        doc = document_fromstring(
            page_unicode.encode('utf-8', 'replace'),
            parser=utf8_parser)
        return doc
    except XMLSyntaxError:
        msg = 'Failed to parse document contents.'
        logger.exception(msg)
        raise ValueError(msg)


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
        """Generate an lxml document from our html."""
        html = replace_multi_br_to_paragraphs(html)
        doc = build_doc(html)

        # doc = html_cleaner.clean_html(doc)
        base_href = self.url
        if base_href:
            logger.debug('Making links absolute')
            doc.make_links_absolute(base_href, resolve_base_href=True)
        else:
            doc.resolve_base_href()

        return doc

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
        titleElem = self.html.find('.//title')
        if titleElem is None or titleElem.text is None:
            return ''
        else:
            return titleElem.text
