FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y curl git clang llvm lld build-essential libssl-dev wget && \
    rm -rf /var/lib/apt/lists/*

RUN curl https://nim-lang.org/choosenim/init.sh -sSf | sh -s -- -y && \
    ln -s ~/.nimble/bin/nim /usr/local/bin/nim && \
    ln -s ~/.nimble/bin/nimble /usr/local/bin/nimble

RUN wget https://github.com/git-lfs/git-lfs/releases/download/v3.4.0/git-lfs-linux-amd64-v3.4.0.tar.gz && \
    tar -xvf git-lfs-linux-amd64-v3.4.0.tar.gz && \
    cd git-lfs-3.4.0 && \
    ./install.sh && \
    git lfs install

RUN git init heimdall && \
    cd heimdall && \
    git remote add origin https://github.com/nocturn9x/heimdall.git && \
    git fetch --depth 1 origin 1.4.2 && \
    git checkout FETCH_HEAD && \
    make modern EXE=heimdall

FROM ubuntu:24.04

COPY --from=builder /heimdall/bin/heimdall /usr/local/bin/heimdall

CMD [ "/usr/local/bin/heimdall" ]
