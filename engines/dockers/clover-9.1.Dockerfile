FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Clover && \
    cd Clover && \
    git remote add origin https://github.com/lucametehau/CloverEngine.git && \
    git fetch --depth 1 origin e647926a8f23b6b93f7f27c01cb6f686909ec482 && \
    git checkout FETCH_HEAD && \
    cd src && \
    make -j release

FROM ubuntu:24.04

COPY --from=builder /Clover/src/Clover.9.1-avx2 /usr/local/bin/Clover

CMD [ "/usr/local/bin/Clover" ]
