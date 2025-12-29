FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Alexandria && \
    cd Alexandria && \
    git remote add origin https://github.com/PGG106/Alexandria.git && \
    git fetch --depth 1 origin 6b61e29604958480144ba8ab688a2a8f43a8f0b0 && \
    git checkout FETCH_HEAD && \
    wget https://github.com/PGG106/Alexandria-networks/releases/download/net03/nn.net && \
    make -j build=x86-64-avx2

FROM ubuntu:24.04

COPY --from=builder /Alexandria/Alexandria /usr/local/bin/Alexandria

CMD [ "/usr/local/bin/Alexandria" ]
