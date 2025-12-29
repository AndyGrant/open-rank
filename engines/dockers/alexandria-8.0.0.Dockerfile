FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Alexandria && \
    cd Alexandria && \
    git remote add origin https://github.com/PGG106/Alexandria.git && \
    git fetch --depth 1 origin cc1f1f0f5b4e681ee65202d7fc2876823e7c6c00 && \
    git checkout FETCH_HEAD && \
    wget https://github.com/PGG106/Alexandria-networks/releases/download/net02/nn.net && \
    make -j build=x86-64-avx2

FROM ubuntu:24.04

COPY --from=builder /Alexandria/Alexandria /usr/local/bin/Alexandria

CMD [ "/usr/local/bin/Alexandria" ]
