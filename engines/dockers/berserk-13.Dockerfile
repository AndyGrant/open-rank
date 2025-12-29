FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init berserk && \
    cd berserk && \
    git remote add origin https://github.com/jhonnold/berserk.git && \
    git fetch --depth 1 origin 9439b87063af42a90a05483a2c9b8cc42b41f7e9 && \
    git checkout FETCH_HEAD && \
    cd src && \
    make -j ARCH=avx2

FROM ubuntu:24.04

COPY --from=builder /berserk/src/berserk /usr/local/bin/berserk

CMD [ "/usr/local/bin/berserk" ]
