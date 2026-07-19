FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Prune && \
    cd Prune && \
    git remote add origin https://github.com/tgirolami09/Prune.git && \
    git fetch --depth 1 --tags origin f2f552e32740f7a327daef20a248938460d8d363 && \
    git checkout FETCH_HEAD && \
    cd core && \
    make -B prune -j CPUSET=avx2 EXE=prune-3.2.1-avx2 ARCH=haswell

FROM ubuntu:24.04

COPY --from=builder /Prune/core/prune-3.2.1-avx2 /usr/local/bin/Prune

CMD [ "/usr/local/bin/Prune" ]