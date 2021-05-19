FROM quay.io/ncigdc/bio-python:3.6 as builder

COPY ./ /opt

WORKDIR /opt

RUN make clean && pip install tox && tox

# tox step builds sdist

FROM quay.io/ncigdc/bio-python:3.6

COPY --from=builder /opt/dist/*.tar.gz /opt

ENV BINARY=maflib

WORKDIR /opt

# Install package from sdist
RUN python -m pip install *.tar.gz && rm -rf *.tar.gz

ENTRYPOINT ["maflib"]

CMD ["--help"]
