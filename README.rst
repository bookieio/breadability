breadability - another readability Python (v2.6-v3.3) port
===========================================================
.. image:: https://api.travis-ci.org/bookieio/breadability.png?branch=master
   :target: https://travis-ci.org/bookieio/breadability.py

I've tried to work with the various forks of some ancient codebase that ported
`readability`_ to Python. The lack of tests, unused regex's, and commented out
sections of code in other Python ports just drove me nuts.

I put forth an effort to bring in several of the better forks into one
code base, but they've diverged so much that I just can't work with it.

So what's any sane person to do? Re-port it with my own repo, add some tests,
infrastructure, and try to make this port better. OSS FTW (and yea, NIH FML,
but oh well I did try)

This is a pretty straight port of the JS here:

- http://code.google.com/p/arc90labs-readability/source/browse/trunk/js/readability.js#82
- http://www.minvolai.com/blog/decruft-arc90s-readability-in-python/

Some other ports:

- https://github.com/aidanf/BTE
- http://www.unixuser.org/~euske/python/webstemmer/#extract
- https://github.com/al3xandru/readability.py
- https://github.com/rcarmo/soup-strainer
- https://github.com/bcampbell/decruft
- https://github.com/gfxmonk/python-readability
- https://github.com/srid/readability
- https://github.com/dcramer/decruft
- https://github.com/reorx/readability
- https://github.com/mote/python-readability
- https://github.com/predatell/python-readability-lxml
- https://github.com/Harshavardhana/boilerpipy
- https://github.com/raptium/hitomi
- https://github.com/kingwkb/readability


Installation
------------
This does depend on lxml so you'll need some C headers in order to install
things from pip so that it can compile.

.. code-block:: bash

    $ [sudo] apt-get install libxml2-dev libxslt-dev
    $ [sudo] pip install git+git://github.com/bookieio/breadability.git

Tests
-----
.. code-block:: bash

    $ nosetests --with-coverage --cover-package=breadability --cover-erase tests
    $ nosetests-3.3 --with-coverage --cover-package=breadability --cover-erase tests


Usage
-----
Command line
~~~~~~~~~~~~

.. code-block:: bash

    $ breadability http://wiki.python.org/moin/BeginnersGuide

Options
```````

- **b** will write out the parsed content to a temp file and open it in a
  browser for viewing.
- **d** will write out debug scoring statements to help track why a node was
  chosen as the document and why some nodes were removed from the final
  product.
- **f** will override the default behaviour of getting an html fragment (<div>)
  and give you back a full <html> document.
- **v** will output in verbose debug mode and help let you know why it parsed
  how it did.


Python API
~~~~~~~~~~
.. code-block:: python

    from __future__ import print_function

    from breadability.readable import Article


    if __name__ == "__main__":
        document = Article(html_as_text, url=source_url)
        print(document.readable)


Work to be done
---------------
Yep, I've got some catching up to do. I don't do pagination, I've got a lot of
custom tweaks I need to get going, there are some articles that fail to parse.
I also have more tests to write on a lot of the cleaning helpers, but
hopefully things are setup in a way that those can/will be added.

Fortunately, I need this library for my tools:

- https://bmark.us
- http://r.bmark.us

so I really need this to be an active and improving project.


Off the top of my heads TODO list:

- Support metadata from parsed article [url, confidence scores, all
  candidates we thought about?]
- More tests, more thorough tests
- More sample articles we need to test against in the test_articles
- Tests that run through and check for regressions of the test_articles
- Tidy'ing the HTML that comes out, might help with regression tests ^^
- Multiple page articles
- Performance tuning, we do a lot of looping and re-drop some nodes that
  should be skipped. We should have a set of regression tests for this so
  that if we implement a change that blows up performance we know it right
  away.
- More docs for things, but sphinx docs and in code comments to help
  understand wtf we're doing and why. That's the biggest hurdle to some of
  this stuff.


Inspiration
~~~~~~~~~~~

- `python-readability`_
- `decruft`_
- `readability`_



.. _readability: http://code.google.com/p/arc90labs-readability/
.. _TravisCI: http://travis-ci.org/
.. _decruft: https://github.com/dcramer/decruft
.. _python-readability: https://github.com/buriy/python-readability
