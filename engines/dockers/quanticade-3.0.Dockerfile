FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Quanticade && \
    cd Quanticade && \
    git remote add origin https://github.com/Quanticade/Quanticade.git && \
    git fetch --depth 1 origin 5b46162956d40aceee2d9c9f4bf4b9d701db67a6 && \
    git checkout FETCH_HEAD && \
    make -j build=x86-64-avx2

FROM ubuntu:24.04

COPY --from=builder /Quanticade/Quanticade /usr/local/bin/Quanticade

CMD [ "/usr/local/bin/Quanticade" ]
