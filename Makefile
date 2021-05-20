REPO = maf-lib
MODULE = maflib

GIT_SHORT_HASH:=$(shell git rev-parse --short HEAD)
GIT_COMMIT_HASH:=$(shell git rev-parse HEAD)

DOCKER_REPO := quay.io/ncigdc
DOCKER_IMAGE_COMMIT := ${DOCKER_REPO}/${REPO}:${GIT_COMMIT_HASH}
DOCKER_IMAGE_LATEST := ${DOCKER_REPO}/${REPO}:latest

TWINE_REPOSITORY_URL?=""

.PHONY: version version-* print-*
version:
	@echo --- VERSION: ${PYPI_VERSION} ---

print-pypi:
	@echo ${PYPI_VERSION}

version-docker:
	@echo

version-docker-tag:
	# Use this target to grab docker-friendly tag from built image
	@echo

.PHONY: docker-login
docker-login:
	docker login -u="${QUAY_USERNAME}" -p="${QUAY_PASSWORD}" quay.io


.PHONY: build build-* clean init init-* lint requirements run version
init: init-pip init-hooks

init-pip:
	@echo
	@echo -- Installing pip packages --
	pip3 install \
		--no-cache-dir \
		-r dev-requirements.txt \
		-r requirements.txt
	python3 setup.py develop

init-hooks:
	@echo
	@echo -- Installing Precommit Hooks --
	pre-commit install

init-venv:
	@echo
	PIP_REQUIRE_VIRTUALENV=true pip3 install --upgrade pip-tools

clean:
	rm -rf ./build/
	rm -rf ./dist/
	rm -rf ./*.egg-info/
	rm -rf ./.tox/
	rm -rf ./htmlcov

lint:
	@echo
	@echo -- Lint --
	python3 -m flake8 \
		--ignore=E501,F401,E302,E502,E126,E731,W503,W605,F841,C901 \
		${MODULE}/

run:
	bin/run

requirements: init-venv requirements-prod requirements-dev

requirements-prod:
	pip-compile -o requirements.txt

requirements-dev:
	pip-compile -o dev-requirements.txt dev-requirements.in

.PHONY: build build-*

build: build-docker

build-docker: clean
	@echo
	@echo -- Skipping docker build --
	docker build . -f Dockerfile \
		--build-arg http_proxy=${PROXY} \
		--build-arg https_proxy=${PROXY} \
		-t "${DOCKER_IMAGE_COMMIT}" \
		-t "${DOCKER_IMAGE_LATEST}"

build-pypi:
	@echo
	@echo Building wheel - ${PYPI_VERSION}
	# Requires twine and wheel to be installed
	python3 setup.py -q egg_info bdist_wheel -b ${MODULE}.egg-info
	python3 setup.py -q sdist --formats zip bdist_wheel

.PHONY: test test-* tox
test: lint test-unit

test-unit:
	@echo
	@echo -- Unit Test --
	python3 -m pytest --cov-report term-missing \
		--junitxml=build/unit-test.xml \
		--cov=${MODULE} \
		tests/

test-docker:
	@echo
	@echo -- Running Docker Test --
	docker run --rm ${DOCKER_IMAGE_LATEST} test

tox:
	@echo
	tox

.PHONY: publish-*
publish-docker:
	@echo Skipping docker publish


publish-pypi:
	@echo
	@echo Publishing wheel
	@python3 -m pip install --user --upgrade pip
	@python3 -m pip install --user --upgrade twine
	python3 -m twine upload $(shell ls -1 dist/*.whl | head -1)
