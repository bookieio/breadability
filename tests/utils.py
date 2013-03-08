from os import path


TEST_DIR = path.dirname(__file__)


def load_snippet(filename):
    """Helper to fetch in the content of a test snippet"""
    file_path = path.join(TEST_DIR, 'test_snippets', filename)
    with open(file_path) as file:
        return file.read()


def load_article(filename):
    """Helper to fetch in the content of a test article"""
    file_path = path.join(TEST_DIR, 'test_articles', filename)
    with open(file_path) as file:
        return file.read()
