FROM python:3.6-alpine

ENV BINARY=maflib

RUN apk add make

COPY ./dist/ /opt

WORKDIR /opt

RUN make init-pip \
  && ln -s /opt/bin/${BINARY} /bin/${BINARY} \
  && chmod +x /bin/${BINARY}

ENTRYPOINT ["/bin/maflib"]

CMD ["--help"]
