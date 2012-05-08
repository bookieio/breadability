import argparse
import codecs
import os
import sys
import urllib
import webbrowser

from tempfile import mkstemp

from breadability import VERSION
from breadability.logconfig import LOG
from breadability.logconfig import set_logging_level
from breadability.readable import Article


LOGLEVEL = 'WARNING'

def parse_args():
    desc = "A fast python port of arc90's readability tool"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--version',
        action='version', version=VERSION)

    parser.add_argument('-v', '--verbose',
        action='store_true',
        default=False,
        help='Increase logging verbosity to DEBUG.')

    parser.add_argument('-f', '--fragment',
        action='store_false',
        default=True,
        help='Output html fragment by default.')

#     parser.add_argument('-m', '--metadata',
#         action='store_true',
#         default=False,
#         help='print all metadata as well as content for the content')

    parser.add_argument('-b', '--browser',
        action='store_true',
        default=False,
        help='open the parsed content in your web browser')

    parser.add_argument('path', metavar='P', type=str, nargs=1,
        help="The url or file path to process in readable form.")

    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    if args.verbose:
        set_logging_level('DEBUG')

    target = args.path[0]
    LOG.debug("Target: " + target)

    if target.startswith('http') or target.startswith('www'):
        is_url = True
        url = target
    else:
        is_url = False
        url = None

    if is_url:
        req = urllib.urlopen(target)
        ucontent = req.read().encode('utf-8')
    else:
        ucontent = codecs.open(target, "r", "utf-8").read()

    enc = sys.__stdout__.encoding or 'utf-8'

    doc = Article(ucontent, url=url, fragment=args.fragment)
    if args.browser:
        fg, pathname = mkstemp(suffix='.html')
        out = codecs.open(pathname, 'w', 'utf-8')
        out.write(doc.readable)
        out.close()
        webbrowser.open(pathname)
    else:
        sys.stdout(doc.readable.encode(enc, 'replace'))


if __name__ == '__main__':
    main()
