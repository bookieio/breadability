from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()


version = '0.1.0'
install_requires = [
    # List your project dependencies here.
    # For more details, see:
    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
    'chardet',
    'lxml',
]
tests_require = [
    'coverage',
    'nose',
    'pep8',
    'pylint',
]


setup(name='breadability',
    version=version,
    description="Redone port of Readability API in Python",
    long_description=README + '\n\n' + NEWS,
    classifiers=[
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    keywords='readable parsing html content bookie',
    author='Rick Harding',
    author_email='rharding@mitechie.com',
    url='http://docs.bmark.us',
    license='BSD',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'test': tests_require
    },
    entry_points={
        'console_scripts':
            ['breadability=breadability:client.main']
    }
)

