FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init stockfish && \
    cd stockfish && \
    git remote add origin https://github.com/official-stockfish/stockfish.git && \
    git fetch --depth 1 origin 03e27488f3d21d8ff4dbf3065603afa21dbd0ef3 && \
    git checkout FETCH_HEAD && \
    cd src && \
    make -j profile-build ARCH=x86-64-avx2

FROM ubuntu:24.04

COPY --from=builder /stockfish/src/stockfish /usr/local/bin/stockfish

CMD [ "/usr/local/bin/stockfish" ]
