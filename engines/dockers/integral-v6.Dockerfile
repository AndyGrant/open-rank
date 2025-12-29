FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init integral && \
    cd integral && \
    git remote add origin https://github.com/aronpetko/integral.git && \
    git fetch --depth 1 origin 26d38b8654e1d7f7101474f258384afa8c753539 && \
    git checkout FETCH_HEAD && \
    wget https://github.com/aronpetko/integral-networks/raw/238c8e4a30f6aa58f4d3c4e0f2db88daaf3750cf/integral.nnue && \
    make -j avx2 CC=clang

FROM ubuntu:24.04

COPY --from=builder /integral/integral /usr/local/bin/integral

CMD [ "/usr/local/bin/integral" ]
