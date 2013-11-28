.. :changelog:

Changelog for readability
==========================
- Added User-Agent string into HTTP requests.
- Added property ``Article.main_text`` for getting text annotated with
  semantic HTML tags (<em>, <strong>, ...).
- Join node with 1 child of the same type. From
  ``<div><div>...</div></div>`` we get ``<div>...</div>``.
- Don't change <div> to <p> if it contains <p> elements.
- Renamed test generation helper 'readability_newtest' -> 'readability_test'.
- Renamed package to readability.
- Added support for Python >= 3.2.
- Py3k compatible package 'charade' is used instead of 'chardet'.

0.1.11 (Dec 12th 2012)
-----------------------
- Add argparse to the install requires for python < 2.7

0.1.10 (Sept 13th 2012)
-----------------------
- Updated scoring bonus and penalty with , and " characters.

0.1.9 (Aug 27nd 2012)
----------------------
- In case of an issue dealing with candidates we need to act like we didn't
  find any candidates for the article content. #10

0.1.8 (Aug 27nd 2012)
----------------------
- Add code/tests for an empty document.
- Fixes #9 to handle xml parsing issues.

0.1.7 (July 21nd 2012)
----------------------
- Change the encode 'replace' kwarg into a normal arg for older python
  version.

0.1.6 (June 17th 2012)
----------------------
- Fix the link removal, add tests and a place to process other bad links.

0.1.5 (June 16th 2012)
----------------------
- Start to look at removing bad links from content in the conditional cleaning
  state. This was really used for the scripting.com site's garbage.

0.1.4 (June 16th 2012)
----------------------
- Add a test generation helper readability_newtest script.
- Add tests and fixes for the scripting news parse failure.

0.1.3 (June 15th 2012)
----------------------
- Add actual testing of full articles for regression tests.
- Update parser to properly clean after winner doc node is chosen.

0.1.2 (May 28th 2012)
----------------------
- Bugfix: #4 issue with logic of the 100char bonus points in scoring
- Garden with PyLint/PEP8
- Add a bunch of tests to readable/scoring code.

0.1.1 (May 11th 2012)
---------------------
- Fix bugs in scoring to help in getting right content
- Add concept of -d which shows scoring/decisions on nodes
- Update command line client to be able to pipe output to other tools

0.1.0 (May 6th 2012)
--------------------
- Initial release and upload to PyPi
