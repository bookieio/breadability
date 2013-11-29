# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

from itertools import groupby
from lxml.sax import saxify, ContentHandler
from .utils import is_blank, shrink_text
from ._compat import to_unicode


_SEMANTIC_TAGS = frozenset((
    "a", "abbr", "acronym", "b", "big", "blink", "blockquote", "cite", "code",
    "dd", "del", "dfn", "dir", "dl", "dt", "em", "h", "h1", "h2", "h3", "h4",
    "h5", "h6", "i", "ins", "kbd", "li", "marquee", "menu", "ol", "pre", "q",
    "s", "samp", "strike", "strong", "sub", "sup", "tt", "u", "ul", "var",
))


class AnnotatedTextHandler(ContentHandler):
    """A class for converting a HTML DOM into annotated text."""

    @classmethod
    def parse(cls, dom):
        """Converts DOM into paragraphs."""
        handler = cls()
        saxify(dom, handler)
        return handler.content

    def __init__(self):
        self._content = []
        self._paragraph = []
        self._dom_path = []

    @property
    def content(self):
        return self._content

    def startElementNS(self, name, qname, attrs):
        namespace, name = name

        if name in _SEMANTIC_TAGS:
            self._dom_path.append(to_unicode(name))

    def endElementNS(self, name, qname):
        namespace, name = name

        if name == "p" and self._paragraph:
            self._append_paragraph(self._paragraph)
        elif name in ("ol", "ul", "pre") and self._paragraph:
            self._append_paragraph(self._paragraph)
            self._dom_path.pop()
        elif name in _SEMANTIC_TAGS:
            self._dom_path.pop()

    def endDocument(self):
        if self._paragraph:
            self._append_paragraph(self._paragraph)

    def _append_paragraph(self, paragraph):
        paragraph = self._process_paragraph(paragraph)
        self._content.append(paragraph)
        self._paragraph = []

    def _process_paragraph(self, paragraph):
        current_paragraph = []

        for annotation, items in groupby(paragraph, key=lambda i: i[1]):
            if annotation and "li" in annotation:
                for text, _ in items:
                    text = shrink_text(text)
                    current_paragraph.append((text, annotation))
            else:
                text = "".join(i[0] for i in items)
                text = shrink_text(text)
                current_paragraph.append((text, annotation))

        return tuple(current_paragraph)

    def characters(self, content):
        if is_blank(content):
            return

        if self._dom_path:
            pair = (content, tuple(sorted(frozenset(self._dom_path))))
        else:
            pair = (content, None)

        self._paragraph.append(pair)
