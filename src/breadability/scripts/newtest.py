import argparse
import codecs
import urllib2
from os import mkdir
from os import path

from breadability import VERSION


TESTPATH = path.join(
            path.dirname(path.dirname(__file__)),
            'tests', 'test_articles')

TESTTPL = """
import os
from unittest import TestCase

from breadability.readable import Article


class TestArticle(TestCase):
    \"\"\"Test the scoring and parsing of the Article\"\"\"

    def setUp(self):
        \"\"\"Load up the article for us\"\"\"
        article_path = os.path.join(os.path.dirname(__file__), 'article.html')
        self.article = open(article_path).read()

    def tearDown(self):
        \"\"\"Drop the article\"\"\"
        self.article = None

    def test_parses(self):
        \"\"\"Verify we can parse the document.\"\"\"
        doc = Article(self.article)
        self.assertTrue('id="readabilityBody"' in doc.readable)

    def test_content_exists(self):
        \"\"\"Verify that some content exists.\"\"\"
        pass

    def test_content_does_not_exist(self):
        \"\"\"Verify we cleaned out some content that shouldn't exist.\"\"\"
        pass
"""


def parse_args():
    desc = "breadability helper to generate a new set of article test files."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--version',
        action='version', version=VERSION)

    parser.add_argument('-n', '--name',
        action='store',
        required=True,
        help='Name of the test directory')

    parser.add_argument('url', metavar='URL', type=str, nargs=1,
        help='The url of content to fetch for the article.html')

    args = parser.parse_args()
    return args


def make_dir(name):
    """Generate a new directory for tests.

    """
    dir_name = 'test_' + name.replace(' ', '_')
    updated_name = path.join(TESTPATH, dir_name)
    mkdir(updated_name)
    return updated_name


def make_files(dirname):
    init_file = path.join(dirname, '__init__.py')
    test_file = path.join(dirname, 'test.py')
    open(init_file, "a").close()
    with open(test_file, 'w') as f:
        f.write(TESTTPL)


def fetch_article(dirname, url):
    """Get the content of the url and make it the article.html"""
    opener = urllib2.build_opener()
    opener.addheaders = [('Accept-Charset', 'utf-8')]
    url_response = opener.open(url)
    dl_html = url_response.read().decode('utf-8')

    fh = codecs.open(path.join(dirname, 'article.html'), "w", "utf-8")
    fh.write(dl_html)
    fh.close()


def main():
    """Run the script."""
    args = parse_args()
    new_dir = make_dir(args.name)
    make_files(new_dir)
    fetch_article(new_dir, args.url[0])


if __name__ == '__main__':
    main()
