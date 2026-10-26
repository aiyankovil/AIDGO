# AIDGO pipeline.  `make` = build + validate + query + analyses + site;  `make test` runs the checks.
PY ?= python3

.PHONY: all install build validate query distance agreement site check test clean

all:
	$(PY) -m aidgo_tools all

install:
	$(PY) -m pip install -r requirements.txt

build:
	$(PY) -m aidgo_tools build

validate: build
	$(PY) -m aidgo_tools validate

query: build
	$(PY) -m aidgo_tools query

distance: build
	$(PY) -m aidgo_tools distance

agreement:
	$(PY) -m aidgo_tools agreement

site:
	$(PY) -m aidgo_tools site

check:
	$(PY) -m aidgo_tools site --check

test:
	$(PY) -m pytest -q

clean:
	rm -rf output/cq_results output/distance output/coding_agreement .pytest_cache
