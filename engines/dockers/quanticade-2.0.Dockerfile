FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Quanticade && \
    cd Quanticade && \
    git remote add origin https://github.com/Quanticade/Quanticade.git && \
    git fetch --depth 1 origin 7e342a379f9d1537ac2e1a6d78ead530c4dbe4ef && \
    git checkout FETCH_HEAD && \
    make -j build=x86-64-avx2

FROM ubuntu:24.04

COPY --from=builder /Quanticade/Quanticade /usr/local/bin/Quanticade

CMD [ "/usr/local/bin/Quanticade" ]
