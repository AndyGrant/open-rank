FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Clover && \
    cd Clover && \
    git remote add origin https://github.com/lucametehau/CloverEngine.git && \
    git fetch --depth 1 origin 68272b3f931a23164dfc39a74675239a613e5cab && \
    git checkout FETCH_HEAD && \
    cd src && \
    make -j release

FROM ubuntu:24.04

COPY --from=builder /Clover/src/Clover.8.2.1-avx2 /usr/local/bin/Clover

CMD [ "/usr/local/bin/Clover" ]
