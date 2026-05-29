FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y curl git clang llvm lld build-essential libssl-dev zlib1g-dev wget && \
    rm -rf /var/lib/apt/lists/*

RUN curl https://nim-lang.org/choosenim/init.sh -sSf | CHOOSENIM_CHOOSE_VERSION=2.2.6 sh -s -- -y && \
    ln -s ~/.nimble/bin/nim /usr/local/bin/nim && \
    ln -s ~/.nimble/bin/nimble /usr/local/bin/nimble

RUN wget https://github.com/git-lfs/git-lfs/releases/download/v3.4.0/git-lfs-linux-amd64-v3.4.0.tar.gz && \
    tar -xvf git-lfs-linux-amd64-v3.4.0.tar.gz && \
    cd git-lfs-3.4.0 && \
    ./install.sh && \
    git lfs install

# Backport the LFS network storage: wasn't a thing for 1.2.2 yet
RUN git init heimdall && \
    cd heimdall && \
    git remote add origin https://github.com/nocturn9x/heimdall.git && \
    git submodule init && \
    git submodule add https://git.nocturn9x.space/heimdall-engine/networks && \
    GIT_LFS_SKIP_SMUDGE=1 git submodule update --recursive && \
    git -C networks lfs fetch --include="files/hofud-v2.bin" && \
    git -C networks lfs checkout "files/hofud-v2.bin" && \
    git fetch --depth 1 origin 1.2.2 && \
    git checkout FETCH_HEAD && \
    make modern EXE=bin/heimdall EVALFILE=../networks/files/hofud-v2.bin

FROM ubuntu:24.04

COPY --from=builder /heimdall/bin/heimdall /usr/local/bin/heimdall

CMD [ "/usr/local/bin/heimdall"]
