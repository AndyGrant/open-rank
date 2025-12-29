FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Obsidian && \
    cd Obsidian && \
    git remote add origin https://github.com/gab8192/Obsidian.git && \
    git fetch --depth 1 origin ba52814c6a202792fd70059982918f9ad1122144 && \
    git checkout FETCH_HEAD && \
    make -j build=avx2

FROM ubuntu:24.04

COPY --from=builder /Obsidian/Obsidian.elf /usr/local/bin/Obsidian

CMD [ "/usr/local/bin/Obsidian" ]
