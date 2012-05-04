from breadability.document import OriginalDocument
from breadability.utils import cached_property

def drop_tag(doc, *tags):
    [[n.drop_tree() for n in doc.iterfind(".//" + tag)]
            for tag in tags]
    return doc


class Article(object):
    """Parsed readable object"""

    def __init__(self, html, url=None):
        self.orig = OriginalDocument(html, url=url)


    @cached_property(ttl=600)
    def readable(self):
        """The readable parsed article"""
        doc = self.orig.html
        doc = drop_tag(doc, 'script', 'link', 'style', 'noscript')
        return doc

