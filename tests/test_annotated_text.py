# -*- coding: utf8 -*-

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

from lxml.html import fragment_fromstring, document_fromstring
from breadability.readable import Article
from breadability.annotated_text import AnnotatedTextHandler
from .utils import load_snippet, load_article


def test_simple_document():
    dom = fragment_fromstring("<p>This is\n\tsimple\ttext.</p>")
    annotated_text = AnnotatedTextHandler.parse(dom)

    assert annotated_text == [
        (
            ("This is\nsimple text.", None),
        ),
    ]


def test_empty_paragraph():
    dom = fragment_fromstring("<div><p>Paragraph <p>\t  \n</div>")
    annotated_text = AnnotatedTextHandler.parse(dom)

    assert annotated_text == [
        (
            ("Paragraph", None),
        ),
    ]


def test_multiple_paragraphs():
    dom = fragment_fromstring("<div><p> 1 first<p> 2\tsecond <p>3\rthird   </div>")
    annotated_text = AnnotatedTextHandler.parse(dom)

    assert annotated_text == [
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


def test_single_annotation():
    dom = fragment_fromstring("<div><p> text <em>emphasis</em> <p> last</div>")
    annotated_text = AnnotatedTextHandler.parse(dom)

    assert annotated_text == [
        (
            ("text", None),
            ("emphasis", ("em",)),
        ),
        (
            ("last", None),
        ),
    ]


def test_recursive_annotation():
    dom = fragment_fromstring("<div><p> text <em><i><em>emphasis</em></i></em> <p> last</div>")
    annotated_text = AnnotatedTextHandler.parse(dom)

    assert annotated_text == [
        (
            ("text", None),
            ("emphasis", ("em", "i")),
        ),
        (
            ("last", None),
        ),
    ]


def test_annotations_without_explicit_paragraph():
    dom = fragment_fromstring("<div>text <strong>emphasis</strong>\t<b>hmm</b> </div>")
    annotated_text = AnnotatedTextHandler.parse(dom)

    assert annotated_text == [
        (
            ("text", None),
            ("emphasis", ("strong",)),
            ("hmm", ("b",)),
        ),
    ]


def test_process_paragraph_with_chunked_text():
    handler = AnnotatedTextHandler()
    paragraph = handler._process_paragraph([
        (" 1", ("b", "del")),
        (" 2", ("b", "del")),
        (" 3", None),
        (" 4", None),
        (" 5", None),
        (" 6", ("em",)),
    ])

    assert paragraph == (
        ("1 2", ("b", "del")),
        ("3 4 5", None),
        ("6", ("em",)),
    )


def test_include_heading():
    dom = document_fromstring(load_snippet("h1_and_2_paragraphs.html"))
    annotated_text = AnnotatedTextHandler.parse(dom.find("body"))

    assert annotated_text == [
        (
            ('Nadpis H1, ktorý chce byť prvý s textom ale predbehol ho "title"', ("h1",)),
            ("Toto je prvý odstavec a to je fajn.", None),
        ),
        (
            ("Tento text je tu aby vyplnil prázdne miesto v srdci súboru.\nAj súbory majú predsa city.", None),
        ),
    ]


def test_real_article():
    article = Article(load_article("zdrojak_automaticke_zabezpeceni.html"))
    annotated_text = article.main_text

    assert annotated_text == [
        (
            ("Automatické zabezpečení", ("h1",)),
            ("Úroveň zabezpečení aplikace bych rozdělil do tří úrovní:", None),
        ),
        (
            ("Aplikace zabezpečená není, neošetřuje uživatelské vstupy ani své výstupy.", ("li", "ol")),
            ("Aplikace se o zabezpečení snaží, ale takovým způsobem, že na ně lze zapomenout.", ("li", "ol")),
            ("Aplikace se o zabezpečení stará sama, prakticky se nedá udělat chyba.", ("li", "ol")),
        ),
        (
            ("Jak se tyto úrovně projevují v jednotlivých oblastech?", None),
        ),
        (
            ("XSS", ("a", "h2")),
            ("Druhou úroveň představuje ruční ošetřování pomocí", None),
            ("htmlspecialchars", ("a", "kbd")),
            (". Třetí úroveň zdánlivě reprezentuje automatické ošetřování v šablonách, např. v", None),
            ("Nette Latte", ("a", "strong")),
            (". Proč píšu zdánlivě? Problém je v tom, že ošetření se dá obvykle snadno zakázat, např. v Latte pomocí", None),
            ("{!$var}", ("code",)),
            (". Viděl jsem šablony plné vykřičníků i na místech, kde být neměly. Autor to vysvětlil tak, že psaní", None),
            ("{$var}", ("code",)),
            ("někde způsobovalo problémy, které po přidání vykřičníku zmizely, tak je začal psát všude.", None),
        ),
        (
            ("<?php\n$safeHtml = $texy->process($content_texy);\n$content = Html::el()->setHtml($safeHtml);\n// v šabloně pak můžeme použít {$content}\n?>", ("pre", )),
        ),
        (
            ("Ideální by bylo, když by už samotná metoda", None),
            ("process()", ("code",)),
            ("vracela instanci", None),
            ("Html", ("code",)),
            (".", None),
        ),
    ]
