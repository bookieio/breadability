# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

from lxml.sax import saxify, ContentHandler
from .utils import is_blank, normalize_whitespace


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
            self._dom_path.append(name)

    def endElementNS(self, name, qname):
        namespace, name = name

        if name == "p" and self._paragraph:
            self._append_paragraph(self._paragraph)
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

        current_text = ""
        last_annotation = None
        for text, annotation in paragraph:
            if last_annotation != annotation and not is_blank(current_text):
                current_text = normalize_whitespace(current_text.strip())
                pair = (current_text, last_annotation)
                current_paragraph.append(pair)
                current_text = ""

            current_text += text
            last_annotation = annotation

        if not is_blank(current_text):
            current_text = normalize_whitespace(current_text.strip())
            pair = (current_text, last_annotation)
            current_paragraph.append(pair)

        return tuple(current_paragraph)

    def characters(self, content):
        if is_blank(content):
            return

        if self._dom_path:
            pair = (content, tuple(frozenset(self._dom_path)))
        else:
            pair = (content, None)

        self._paragraph.append(pair)
