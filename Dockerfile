FROM quay.io/ncigdc/python38-builder as builder

COPY ./ /opt

WORKDIR /opt

RUN pip install tox && tox -e build

FROM quay.io/ncigdc/python38

COPY --from=builder /opt/dist/*.tar.gz /opt
COPY requirements.txt /opt

WORKDIR /opt

RUN pip install --no-deps -r requirements.txt \
	&& pip install --no-deps *.tar.gz \
	&& rm -f *.tar.gz requirements.txt

ENTRYPOINT ["maflib"]

CMD ["--help"]
