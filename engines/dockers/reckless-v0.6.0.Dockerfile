FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

# Install Cargo, but we won't have cargo on the path
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs > rustup.sh && \
    chmod +x rustup.sh && ./rustup.sh -y && \
    $HOME/.cargo/bin/rustup update

# Add Cargo to the path
ENV PATH="/root/.cargo/bin:$PATH"

# Setup for PGO
RUN rustup component add llvm-tools && \
    cargo install cargo-pgo

ENV RUSTFLAGS="-C target-cpu=x86-64-v3"

RUN git init Reckless && \
    cd Reckless && \
    git remote add origin https://github.com/codedeliveryservice/Reckless.git && \
    git fetch --depth 1 origin f3467aea83a996eb3cf57be1f25ff507766fea4e && \
    git checkout FETCH_HEAD && \
    cargo rustc --release && \
    mv target/release/reckless reckless

FROM ubuntu:24.04

COPY --from=builder /Reckless/reckless /usr/local/bin/reckless

CMD [ "/usr/local/bin/reckless" ]
