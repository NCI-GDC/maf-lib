VERSION = 1.0.0
REPO = maf-lib
MODULE = maflib
BRANCH_NAME?=unknown

GIT_SHORT_HASH:=$(shell git rev-parse --short HEAD)

LONG_VERSION:=$(shell python3 setup.py -q capture_version --semver ${VERSION} --branch ${BRANCH_NAME})
PYPI_VERSION:=$(shell python3 setup.py -q print_version --pypi)
COMMIT_HASH:=$(shell python3 setup.py -q print_version --hash)

DOCKER_REPO := quay.io/ncigdc
DOCKER_IMAGE := ${DOCKER_REPO}/${REPO}:${LONG_VERSION}
DOCKER_IMAGE_COMMIT := ${DOCKER_REPO}/${REPO}:${COMMIT_HASH}
DOCKER_IMAGE_LATEST := ${DOCKER_REPO}/${REPO}:latest
DOCKER_IMAGE_STAGING := ${DOCKER_REPO}/${REPO}:staging
DOCKER_IMAGE_RELEASE := ${DOCKER_REPO}/${REPO}:${VERSION}

TWINE_REPOSITORY_URL?=""

.PHONY: version version-* print-*
version:
	@echo --- VERSION: ${LONG_VERSION} ---

print-version:
	@echo ${LONG_VERSION}

print-short:
	@echo ${VERSION}

print-pypi:
	@echo ${PYPI_VERSION}

version-docker:
	@echo ${DOCKER_IMAGE}
	@echo ${DOCKER_IMAGE_COMMIT}
	@echo ${DOCKER_IMAGE_LATEST}

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

lint:
	@echo
	@echo -- Lint --
	python3 -m flake8 \
		--ignore=E501,F401,E302,E502,E126,E731,W503,W605,F841,C901 \
		${MODULE}/

run:
	bin/run

requirements: init-venv
	python3 setup.py -q capture_requirements --dev
	pip-compile -o requirements.txt requirements.in

.PHONY: build build-*

build: build-docker

build-docker:
	@echo
	@echo -- Building docker --
	python3 setup.py build
	mkdir -p dist
	cp -r build/lib/* dist/
	cp -r bin/ dist/
	cp -f Makefile requirements.txt README.md setup.py dist/
	docker build . \
		--file ./Dockerfile \
		--build-arg http_proxy=${PROXY} \
		--build-arg https_proxy=${PROXY} \
		-t "${DOCKER_IMAGE_COMMIT}" \
		-t "${DOCKER_IMAGE}" \
		-t "${DOCKER_IMAGE_LATEST}"

build-pypi:
	@echo
	@echo Building wheel - ${PYPI_VERSION}
	python3 setup.py bdist_wheel -b ${MODULE}.egg-info

.PHONY: test test-*
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

.PHONY: publish-*

publish-staging: docker-login
	docker tag ${DOCKER_IMAGE_LATEST} ${DOCKER_IMAGE_STAGING}
	docker push ${DOCKER_IMAGE_COMMIT}
	docker push ${DOCKER_IMAGE_STAGING}
	docker push ${DOCKER_IMAGE}

publish-release: docker-login
	docker tag ${DOCKER_IMAGE_LATEST} ${DOCKER_IMAGE_RELEASE}
	docker push ${DOCKER_IMAGE_RELEASE}

publish-pypi: dist/*.whl
	@echo
	@echo Publishing wheel
	python3 -m twine upload $(shell ls -1 dist/*.whl | head -1)
