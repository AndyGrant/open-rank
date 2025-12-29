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

RUN git init Viridithas && \
    cd Viridithas && \
    git remote add origin https://github.com/cosmobobak/Viridithas.git && \
    git fetch --depth 1 origin 121a6786f755055e857e34f57b37299e340cb63c && \
    git checkout FETCH_HEAD && \
    wget https://github.com/cosmobobak/viridithas-networks/releases/download/v96/perseverance-b200.nnue.zst -O viridithas.nnue.zst && \
    cargo b -r --features syzygy,bindgen

FROM ubuntu:24.04

COPY --from=builder /Viridithas/target/release/viridithas /usr/local/bin/Viridithas

CMD [ "/usr/local/bin/Viridithas" ]
