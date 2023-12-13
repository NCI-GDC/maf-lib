#!/bin/bash
set -eox pipefail

BRANCH="${CI_COMMIT_BRANCH}"

SHORT_SHA="$(git rev-parse --short HEAD)"
SHA="$(git rev-parse HEAD)"
DESCRIBE="$(git describe --tags --always --dirty)"

BASE_CONTAINER_REGISTRY="${BASE_CONTAINER_REGISTRY:-docker.osdc.io}"
BASE_CONTAINER_VERSION="${BASE_CONTAINER_VERSION:-2.3.3}"
PROXY="${PROXY:-}"

export DOCKER_BUILDKIT=1
export BUILDKIT_STEP_LOG_MAX_SIZE=10485760
export BUILDKIT_STEP_LOG_MAX_SPEED=1048576

# Initialize Registry array
REGISTRIES=()
if [ "$BRANCH" = "$CI_DEFAULT_BRANCH" ] || [ -n "$SCM_TAG" ]; then
	# Which internal registry to push the images to.
	# Production registries/quay on release
	REGISTRIES+=("containers.osdc.io" "quay.io")
else
	# Dev registry otherwise
	REGISTRIES+=("dev-containers.osdc.io")
fi

TAG_VERSIONS=("${DESCRIBE} ${SHA}")

function populate_image_tags() {
  IMAGE_TAGS=()
  for REGISTRY in "${REGISTRIES[@]}"; do
    for TAG_VERSION in "${TAG_VERSIONS[@]}"; do
      IMAGE_TAGS+=("${REGISTRY}/ncigdc/${CI_PROJECT_NAME}:${TAG_VERSION}")
    done
  done
}

BUILD_TAG="build-${CI_PROJECT_NAME}"

docker buildx build \
    --compress \
    -f Dockerfile . \
    --build-arg VERSION="${DESCRIBE}" \
    --build-arg REGISTRY="${BASE_CONTAINER_REGISTRY}" \
    --build-arg BASE_CONTAINER_VERSION="${BASE_CONTAINER_VERSION}" \
    --label org.opencontainers.image.version="${DESCRIBE}" \
    --label org.opencontainers.image.created="$(date -Iseconds)" \
    --label org.opencontainers.image.revision="${SHORT_SHA}" \
    --label org.opencontainers.ref.name="${CI_PROJECT_NAME}:${GIT_BRANCH}" \
    -t "${BUILD_TAG}"

populate_image_tags
for TAG in "${IMAGE_TAGS[@]}"; do
	docker tag "${BUILD_TAG}" "$TAG"
done

docker rmi "${BUILD_TAG}"
if [[ -n "$GITLAB_CI" ]]; then
	# Only publish on CI
    for TAG in "${IMAGE_TAGS[@]}"; do
        docker push "${TAG}"
        docker rmi "${TAG}"
        echo "${TAG} is all set"
    done
fi
