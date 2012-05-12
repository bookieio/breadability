breadability - another readability Python port
===============================================
I've tried to work with the various forks of some ancient codebase that ported
`readability`_ to Python. The lack of tests, unused regex's, and commented out
sections of code in other Python ports just drove me nuts.

I put forth an effort to bring in several of the better forks into one
codebase, but they've diverged so much that I just can't work with it.

So what's any sane person to do? Re-port it with my own repo, add some tests,
infrastructure, and try to make this port better. OSS FTW (and yea, NIH FML,
but oh well I did try)

This is a pretty straight port of the JS here:

- http://code.google.com/p/arc90labs-readability/source/browse/trunk/js/readability.js#82


Installation
-------------
This does depend on lxml so you'll need some C headers in order to install
things from pip so that it can compile.

::

    sudo apt-get install libxml2-dev libxslt-dev
    pip install breadability


Usage
------

cmd line
~~~~~~~~~

::

    $ breadability http://wiki.python.org/moin/BeginnersGuide

Options
``````````

  - b will write out the parsed content to a temp file and open it in a
    browser for viewing.
  - f will override the default behaviour of getting an html fragment (<div>)
    and give you back a full <html> document.
  - v will output in verbose debug mode and help let you know why it parsed
    how it did.


Using from Python
~~~~~~~~~~~~~~~~~~

::

    from breadability.readable import Article
    readable_article = Article(html_text, url=url_came_from)
    print readable_article


Work to be done
---------------
Yep, I've got some catching up to do. I don't do pagination, I've got a lot of
custom tweaks I need to get going, there are some articles that fail to parse.
I also have more tests to write on a lot of the cleaning helpers, but
hopefully things are setup in a way that those can/will be added.

Fortunately, I need this library for my tools:

- https://bmark.us
- http://readable.bmark.us

so I really need this to be an active and improving project.


Off the top of my heads todo list:

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
  - Get up on pypi along with the rest of the ports
  - More docs for things, but sphinx docs and in code comments to help
    understand wtf we're doing and why. That's the biggest hurdle to some of
    this stuff.

Helping out
------------
If you want to help, shoot me a pull request, an issue report with broken
urls, etc.

You can ping me on irc, I'm always in the `#bookie` channel in freenode.


Important Links
----------------

- `Builds`_ are done on `TravisCI`_


Inspiration
~~~~~~~~~~~~

- `python-readability`_
- `decruft`_
- `readability`_



.. _readability: http://code.google.com/p/arc90labs-readability/
.. _Builds: http://travis-ci.org/#!/mitechie/breadability
.. _TravisCI: http://travis-ci.org/
.. _decruft: https://github.com/dcramer/decruft
.. _python-readability: https://github.com/buriy/python-readability
