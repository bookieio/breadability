# Makefile to help automate tasks
WD := $(shell pwd)
PY := bin/python
PIP := bin/pip
PEP8 := bin/pep8
NOSE := bin/nosetests

# ###########
# Tests rule!
# ###########
.PHONY: test
test: venv develop $(NOSE)
	$(NOSE) -s tests

$(NOSE):
	$(PIP) install nose nose-selecttests pep8 pylint coverage

# #######
# INSTALL
# #######
.PHONY: all
all: venv deps develop

venv: bin/python
bin/python:
	virtualenv .

.PHONY: deps
deps: venv
	pip install -r requirements.txt

.PHONY: clean_venv
clean_venv:
	rm -rf bin include lib local man share

.PHONY: develop
develop: lib/python*/site-packages/readability.egg-link
lib/python*/site-packages/readability.egg-link:
	$(PY) setup.py develop


# ###########
# Development
# ###########
.PHONY: clean_all
clean_all: clean_venv
	if [ -d dist ]; then \
		rm -r dist; \
    fi


# ###########
# Deploy
# ###########
.PHONY: dist
dist:
	$(PY) setup.py sdist

.PHONY: upload
upload:
	$(PY) setup.py sdist upload

.PHONY: version_update
version_update:
	$(EDITOR) setup.py CHANGELOG.rst
