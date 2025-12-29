FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init integral && \
    cd integral && \
    git remote add origin https://github.com/aronpetko/integral.git && \
    git fetch --depth 1 origin 9b7c23d664cb493896e476966bab19069f6c0974 && \
    git checkout FETCH_HEAD && \
    make -j avx2 CC=clang

FROM ubuntu:24.04

COPY --from=builder /integral/integral /usr/local/bin/integral

CMD [ "/usr/local/bin/integral" ]
