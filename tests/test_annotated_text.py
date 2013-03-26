# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

from lxml.html import fragment_fromstring, document_fromstring
from readability.annotated_text import AnnotatedTextHandler
from .compat import unittest
from .utils import load_snippet


class TestAnnotatedText(unittest.TestCase):
    def test_simple_document(self):
        dom = fragment_fromstring("<p>This is\n\tsimple\ttext.</p>")
        annotated_text = AnnotatedTextHandler.parse(dom)

        expected = [
            (
                ("This is\nsimple text.", None),
            ),
        ]
        self.assertEqual(annotated_text, expected)

    def test_empty_paragraph(self):
        dom = fragment_fromstring("<div><p>Paragraph <p>\t  \n</div>")
        annotated_text = AnnotatedTextHandler.parse(dom)

        expected = [
            (
                ("Paragraph", None),
            ),
        ]
        self.assertEqual(annotated_text, expected)

    def test_multiple_paragraphs(self):
        dom = fragment_fromstring("<div><p> 1 first<p> 2\tsecond <p>3\rthird   </div>")
        annotated_text = AnnotatedTextHandler.parse(dom)

        expected = [
            (
                ("1 first", None),
            ),
            (
                ("2 second", None),
            ),
            (
                ("3\nthird", None),
            ),
        ]
        self.assertEqual(annotated_text, expected)

    def test_single_annotation(self):
        dom = fragment_fromstring("<div><p> text <em>emphasis</em> <p> last</div>")
        annotated_text = AnnotatedTextHandler.parse(dom)

        expected = [
            (
                ("text", None),
                ("emphasis", ("em",)),
            ),
            (
                ("last", None),
            ),
        ]
        self.assertEqual(annotated_text, expected)

    def test_recursive_annotation(self):
        dom = fragment_fromstring("<div><p> text <em><i><em>emphasis</em></i></em> <p> last</div>")
        annotated_text = AnnotatedTextHandler.parse(dom)

        expected = [
            (
                ("text", None),
                ("emphasis", ("em", "i")),
            ),
            (
                ("last", None),
            ),
        ]

        self.assertEqual(annotated_text[0][0][0], expected[0][0][0])
        self.assertEqual(annotated_text[0][0][1], expected[0][0][1])

        self.assertEqual(annotated_text[0][1][0], expected[0][1][0])
        self.assertEqual(sorted(annotated_text[0][1][1]), sorted(expected[0][1][1]))

        self.assertEqual(annotated_text[1], expected[1])

    def test_annotations_without_explicit_paragraph(self):
        dom = fragment_fromstring("<div>text <strong>emphasis</strong>\t<b>hmm</b> </div>")
        annotated_text = AnnotatedTextHandler.parse(dom)

        expected = [
            (
                ("text", None),
                ("emphasis", ("strong",)),
                ("hmm", ("b",)),
            ),
        ]
        self.assertEqual(annotated_text, expected)

    def test_process_paragraph_with_chunked_text(self):
        handler = AnnotatedTextHandler()
        paragraph = handler._process_paragraph([
            (" 1", ("b", "del")),
            (" 2", ("b", "del")),
            (" 3", None),
            (" 4", None),
            (" 5", None),
            (" 6", ("em",)),
        ])

        expected = (
            ("1 2", ("b", "del")),
            ("3 4 5", None),
            ("6", ("em",)),
        )
        self.assertEqual(paragraph, expected)

    def test_include_heading(self):
        dom = document_fromstring(load_snippet("h1_and_2_paragraphs.html"))
        annotated_text = AnnotatedTextHandler.parse(dom.find("body"))

        expected = [
            (
                ('Nadpis H1, ktorý chce byť prvý s textom ale predbehol ho "title"', ("h1",)),
                ("Toto je prvý odstavec a to je fajn.", None),
            ),
            (
                ("Tento text je tu aby vyplnil prázdne miesto v srdci súboru.\nAj súbory majú predsa city.", None),
            ),
        ]
        self.assertSequenceEqual(annotated_text, expected)
