FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Clover && \
    cd Clover && \
    git remote add origin https://github.com/lucametehau/CloverEngine.git && \
    git fetch --depth 1 origin c22e05d29baa515b1067ebe07bf6815d8d7a0ace && \
    git checkout FETCH_HEAD && \
    cd src && \
    make -j release

FROM ubuntu:24.04

COPY --from=builder /Clover/src/Clover.9.0-avx2 /usr/local/bin/Clover

CMD [ "/usr/local/bin/Clover" ]
