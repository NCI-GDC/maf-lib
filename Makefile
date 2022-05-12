REPO = maf-lib

MODULE = maflib

# Redirect error when run in container
COMMIT_HASH:=$(shell git rev-parse HEAD 2>/dev/null)
GIT_DESCRIBE:=$(shell git describe --tags 2>/dev/null)

DOCKER_REPO := quay.io/ncigdc
DOCKER_IMAGE_COMMIT := ${DOCKER_REPO}/${REPO}:${COMMIT_HASH}
DOCKER_IMAGE_DESCRIBE := ${DOCKER_REPO}/${REPO}:${GIT_DESCRIBE}
DOCKER_IMAGE_LATEST := ${DOCKER_REPO}/${REPO}:latest

.PHONY: version version-*
version:
	@python setup.py --version

version-docker:
	@echo ${DOCKER_IMAGE_DESCRIBE}

version-docker-tag:
	@echo

.PHONY: docker-login
docker-login:
	docker login -u="${QUAY_USERNAME}" -p="${QUAY_PASSWORD}" quay.io

.PHONY: venv
venv:
	@echo
	rm -rf .venv/
	tox -r -e dev --devenv .venv

.PHONY: init init-*
init: init-pip init-hooks
init-pip:
	@echo
	@echo -- Installing pip packages --
	pip-sync requirements.txt dev-requirements.txt
	python -m pip install -e .

init-hooks:
	@echo
	@echo -- Installing Precommit Hooks --
	pre-commit install

init-venv:
	@echo
	PIP_REQUIRE_VIRTUALENV=true python -m pip install --upgrade pip pip-tools

.PHONY: clean clean-*
clean: clean-dirs
clean-dirs:
	rm -rf ./build/
	rm -rf ./dist/
	rm -rf ./*.egg-info/
	rm -rf ./test-reports/
	rm -rf ./htmlcov/

clean-docker:
	@echo


.PHONY: requirements requirements-*
requirements: init-venv requirements-prod requirements-dev
requirements-dev:
	pip-compile -o dev-requirements.txt dev-requirements.in

requirements-prod:
	pip-compile -o requirements.txt

.PHONY: build build-*

build: build-docker

build-docker: clean
	@echo
	@echo -- Building docker --
	docker build . \
		--file ./Dockerfile \
		--build-arg http_proxy=${PROXY} \
		--build-arg https_proxy=${PROXY} \
		-t "${DOCKER_IMAGE_COMMIT}" \
		-t "${DOCKER_IMAGE_LATEST}"

build-pypi: clean
	@echo
	tox -e check_dist

.PHONY: run run-*
run:
	@echo

run-docker:
	@echo
	docker run --rm "${DOCKER_IMAGE_COMMIT}"

.PHONY: lint test test-* tox
test: tox
lint:
	@echo
	@echo -- Lint --
	tox -p -e flake8

test-unit:
	pytest tests/

test-docker:
	@echo

tox:
	@echo
	TOX_PARALLEL_NO_SPINNER=1 tox -p --recreate

.PHONY: publish-*
publish-docker:
	docker tag ${DOCKER_IMAGE_COMMIT} ${DOCKER_IMAGE_DESCRIBE}
	docker push ${DOCKER_IMAGE_COMMIT}
	docker push ${DOCKER_IMAGE_DESCRIBE}

publish-pypi:
	@echo
	@echo Publishing wheel
	python3 -m twine upload dist/*
