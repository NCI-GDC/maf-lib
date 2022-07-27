ARG REGISTRY=quay.io
ARG BASE_CONTAINER_VERSION=2.0.1

FROM ${REGISTRY}/ncigdc/python3.8-builder:${BASE_CONTAINER_VERSION} as builder

COPY ./ /opt

WORKDIR /opt

RUN pip install tox tox -e build

FROM ${REGISTRY}/ncigdc/python3.8:${BASE_CONTAINER_VERSION}

COPY --from=builder /opt/build/dist/*.tar.gz /opt
COPY requirements.txt /opt

WORKDIR /opt

RUN pip install --no-deps -r requirements.txt \
	&& pip install --no-deps *.tar.gz \
	&& rm -f *.tar.gz requirements.txt

ENTRYPOINT ["maflib"]

CMD ["--help"]
