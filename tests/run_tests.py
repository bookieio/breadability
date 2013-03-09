# -*- coding: utf8 -*-

from __future__ import print_function

import sys
import atexit
import nose

from os.path import dirname, abspath


DEFAULT_PARAMS = [
    "nosetests",
    "--with-coverage",
    "--cover-package=breadability",
    "--cover-erase",
]


@atexit.register
def exit_function(msg="Shutting down"):
    print(msg, file=sys.stderr)


def run(argv=[]):
    sys.exitfunc = exit_function

    nose.run(
        argv=DEFAULT_PARAMS + argv,
        defaultTest=abspath(dirname(__file__)),
    )


if __name__ == "__main__":
    run(sys.argv[1:])
