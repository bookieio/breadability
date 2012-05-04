from breadability.document import OriginalDocument
from breadability.utils import cached_property


def drop_tag(doc, *tags):
    [[n.drop_tree() for n in doc.iterfind(".//" + tag)]
            for tag in tags]
    return doc


def build_base_document(html):
    """Return a base document with the body as root.

    html should be a parsed Element object.

    """
    found_body = html.find('.//body')
    if found_body is not None:
        # remove any CSS and set our own
        found_body.set('class', 'readabilityBody')
        return found_body


class Article(object):
    """Parsed readable object"""

    def __init__(self, html, url=None):
        self.orig = OriginalDocument(html, url=url)

    @cached_property(ttl=600)
    def readable(self):
        """The readable parsed article"""
        doc = self.orig.html
        doc = build_base_document(doc)
        doc = drop_tag(doc, 'script', 'link', 'style', 'noscript')
        return doc

