FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Alexandria && \
    cd Alexandria && \
    git remote add origin https://github.com/PGG106/Alexandria.git && \
    git fetch --depth 1 origin e88f47068975ce9b77c960715a50a8f102c62904 && \
    git checkout FETCH_HEAD && \
    wget https://github.com/PGG106/Alexandria-networks/releases/download/net04/nn.net && \
    make -j build=x86-64-avx2

FROM ubuntu:24.04

COPY --from=builder /Alexandria/Alexandria /usr/local/bin/Alexandria

CMD [ "/usr/local/bin/Alexandria" ]
