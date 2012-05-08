"""Generate a clean nice starting html document to process for an article."""

import chardet
import re
from lxml.etree import tostring
from lxml.etree import tounicode
from lxml.html import document_fromstring
from lxml.html import HTMLParser

from breadability.logconfig import LOG
from breadability.utils import cached_property


utf8_parser = HTMLParser(encoding='utf-8')


def get_encoding(page):
    text = re.sub('</?[^>]*>\s*', ' ', page)
    enc = 'utf-8'
    if not text.strip() or len(text) < 10:
        return enc  # can't guess
    try:
        diff = text.decode(enc, 'ignore').encode(enc)
        sizes = len(diff), len(text)
        # 99% of utf-8
        if abs(len(text) - len(diff)) < max(sizes) * 0.01:
            return enc
    except UnicodeDecodeError:
        pass
    res = chardet.detect(text)
    enc = res['encoding']
    # print '->', enc, "%.2f" % res['confidence']
    if enc == 'MacCyrillic':
        enc = 'cp1251'
    return enc


def replace_multi_br_to_paragraphs(html):
    """Convert multiple <br>s into paragraphs"""
    LOG.debug('Replacing multiple <br/> to <p>')
    rep = re.compile("(<br[^>]*>[ \n\r\t]*){2,}", re.I)
    return rep.sub('</p><p>', html)


def build_doc(page):
    """Requires that the `page` not be None"""
    if page is None:
        LOG.error("Page content is None, can't build_doc")
        return ''
    if isinstance(page, unicode):
        page_unicode = page
    else:
        enc = get_encoding(page)
        page_unicode = page.decode(enc, 'replace')
    doc = document_fromstring(
        page_unicode.encode('utf-8', 'replace'),
        parser=utf8_parser)
    return doc


class OriginalDocument(object):
    """The original document to process"""
    _base_href = None

    def __init__(self, html, url=None):
        self.orig_html = html
        self.url = url

    def __str__(self):
        """Render out our document as a string"""
        return tostring(self.html)

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
            LOG.debug('Making links absolute')
            doc.make_links_absolute(base_href, resolve_base_href=True)
        else:
            doc.resolve_base_href()
        return doc

    @cached_property(ttl=600)
    def html(self):
        """The parsed html document from the input"""
        return self._parse(self.orig_html)

    @cached_property(ttl=600)
    def links(self):
        """Links within the document"""
        return self.html.findall(".//a")

    @cached_property(ttl=600)
    def title(self):
        """Pull the title attribute out of the parsed document"""
        titleElem = self.html.find('.//title')
        if titleElem is None or titleElem.text is None:
            return ''
        else:
            return titleElem.text
