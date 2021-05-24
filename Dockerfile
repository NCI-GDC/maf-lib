FROM quay.io/ncigdc/bio-python:3.6 as builder

COPY ./ /opt

WORKDIR /opt

RUN python -m pip install tox && tox

# tox step builds sdist

FROM quay.io/ncigdc/bio-alpine:py36

COPY --from=builder /opt/dist/*.tar.gz /opt
COPY ./requirements.txt /opt/requirements.txt

ENV BINARY=maflib

WORKDIR /opt

# Install package from sdist
RUN pip install -r requirements.txt \
	&& pip install *.tar.gz \
	&& rm -rf *.tar.gz requirements.txt

ENTRYPOINT ["maflib"]

CMD ["--help"]
