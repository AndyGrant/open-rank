FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init berserk && \
    cd berserk && \
    git remote add origin https://github.com/jhonnold/berserk.git && \
    git fetch --depth 1 origin c67650dbf6dde7f41ca7f2c8aa9e4b718eb304f8 && \
    git checkout FETCH_HEAD && \
    cd src && \
    make -j release VERSION=11

FROM ubuntu:24.04

COPY --from=builder /berserk/src/berserk-11-x64-avx2 /usr/local/bin/berserk

CMD [ "/usr/local/bin/berserk" ]
