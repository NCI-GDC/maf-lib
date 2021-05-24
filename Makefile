REPO = maf-lib
MODULE = maflib

GIT_SHORT_HASH:=$(shell git rev-parse --short HEAD)
GIT_COMMIT_HASH:=$(shell git rev-parse HEAD)
GIT_DESCRIBE:=$(shell git describe --tags)

DOCKER_REPO := quay.io/ncigdc
DOCKER_IMAGE_COMMIT := ${DOCKER_REPO}/${REPO}:${GIT_COMMIT_HASH}
DOCKER_IMAGE_LATEST := ${DOCKER_REPO}/${REPO}:latest
DOCKER_IMAGE_DESCRIBE := ${DOCKER_REPO}/${REPO}:${GIT_DESCRIBE}

TWINE_REPOSITORY_URL?=""

.PHONY: version version-*
version:
	@python setup.py --version

version-docker:
	@echo ${DOCKER_IMAGE_COMMIT}

version-docker-tag:
	@echo

.PHONY: docker-login
docker-login:
	docker login -u="${QUAY_USERNAME}" -p="${QUAY_PASSWORD}" quay.io


.PHONY: init init-*
init: init-pip init-hooks

init-pip:
	@echo
	@echo -- Installing pip packages --
	pip-sync requirements.txt dev-requirements.txt
	python setup.py develop

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
	rm -rf ./.tox/
	rm -rf ./htmlcov

clean-docker:
	@docker rmi -f ${DOCKER_IMAGE_COMMIT}

.PHONY: requirements requirements-*
requirements: init-venv requirements-prod requirements-dev

requirements-prod:
	pip-compile -o requirements.txt

requirements-dev:
	pip-compile -o dev-requirements.txt dev-requirements.in

.PHONY: build build-*

build: build-docker

build-docker: clean
	@echo -- Building docker --
	docker build . -f Dockerfile \
		--build-arg http_proxy=${PROXY} \
		--build-arg https_proxy=${PROXY} \
		-t "${DOCKER_IMAGE_COMMIT}" \
		-t "${DOCKER_IMAGE_LATEST}"

build-pypi: clean
	@tox -e check_dist

.PHONY: lint test test-* tox
test: tox

test-unit:
	@echo
	@echo -- Unit Test --
	tox -e py36

test-docker:
	@echo

tox:
	@echo Running tox
	tox -p all

lint:
	@echo
	@echo -- Lint --
	tox -p -e flake8

.PHONY: publish-*
publish-docker:
	docker tag ${DOCKER_IMAGE_LATEST} ${DOCKER_IMAGE_DESCRIBE}
	docker push ${DOCKER_IMAGE_COMMIT}
	docker push ${DOCKER_IMAGE_DESCRIBE}

publish-pypi:
	@echo
	@echo Publishing dists
	python -m twine upload dist/*
