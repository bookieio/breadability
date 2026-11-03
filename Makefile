# Makefile to help automate tasks
WD := $(shell pwd)
PY := bin/python
PIP := bin/pip
PEP8 := bin/pep8
PYTEST := bin/py.test

# ###########
# Tests rule!
# ###########
.PHONY: test
test: venv develop $(PYTEST)
	$(PYTEST) -q --tb native -s tests

# Runs tests on every supported Python version like CI does (requires uv)
PYTHON_VERSIONS := 3.8 3.9 3.10 3.11 3.12 3.13 3.14 3.15

.PHONY: test-all
test-all:
	@for version in $(PYTHON_VERSIONS); do \
		echo "=== Python $$version ==="; \
		uv run --isolated --no-project --python $$version --with pytest --with . pytest || exit 1; \
	done

.PHONY: test-coverage
test-coverage: venv develop $(PYTEST)
	$(PYTEST) -q --cov breadability tests

$(PYTEST):
	$(PIP) install -r requirements.txt

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
	$(PIP) install -r requirements.txt

.PHONY: clean_venv
clean_venv:
	rm -rf bin include lib local man share

.PHONY: develop
develop: lib/python*/site-packages/breadability.egg-link
lib/python*/site-packages/breadability.egg-link:
	$(PY) setup.py develop


# ###########
# Development
# ###########
.PHONY: clean-all
clean-all: clean_venv
	if [ -d dist ]; then \
		rm -r dist; \
    fi


bin/flake8: venv
	bin/pip install flake8

lint: bin/flake8
	flake8 breadability


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
