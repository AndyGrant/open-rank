FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Caissa && \
    cd Caissa && \
    git remote add origin https://github.com/Witek902/Caissa.git && \
    git fetch --depth 1 origin bae00a2df132fc8877f0ebcd9d4010ed73dc3f90 && \
    git checkout FETCH_HEAD && \
    cd src && \
    make -j avx2

FROM ubuntu:24.04

COPY --from=builder /Caissa/src/caissa-1.24-x64-avx2 /usr/local/bin/Caissa

CMD [ "/usr/local/bin/Caissa" ]
