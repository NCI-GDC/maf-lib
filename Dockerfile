ARG REGISTRY=docker.osdc.io
ARG BASE_CONTAINER_VERSION=2.3.3

FROM ${REGISTRY}/ncigdc/python3.8-builder:${BASE_CONTAINER_VERSION} as builder

COPY ./ /opt

WORKDIR /opt

RUN pip install tox && tox -e build

FROM ${REGISTRY}/ncigdc/python3.8:${BASE_CONTAINER_VERSION}

LABEL org.opencontainers.image.title="maflib" \
      org.opencontainers.image.description="Python package for processing and creating MAF files for the GDC" \
      org.opencontainers.image.source="https://github.com/NCI-GDC/maf-lib" \
      org.opencontainers.image.vendor="NCI GDC"


COPY --from=builder /opt/dist/*.whl /opt/
COPY requirements.txt /opt/

WORKDIR /opt

RUN pip install --no-deps -r requirements.txt \
	&& pip install --no-deps *.whl \
	&& rm -f *.whl requirements.txt

ENTRYPOINT ["maflib"]

CMD ["--help"]
