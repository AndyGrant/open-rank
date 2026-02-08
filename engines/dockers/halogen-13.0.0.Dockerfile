FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

ARG BINARY_NAME=Halogen-13-ubuntu-avx2-pext
ARG DOWNLOAD_URL=https://github.com/KierenP/Halogen/releases/download/v13/${BINARY_NAME}

RUN apt update && apt-get -y install wget

RUN wget ${DOWNLOAD_URL} && \
    chmod +x ${BINARY_NAME} && \
    mv ${BINARY_NAME} halogen

FROM ubuntu:24.04

COPY --from=builder /halogen /usr/local/bin/halogen

CMD [ "/usr/local/bin/halogen" ]
