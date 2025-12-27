FROM ubuntu:26.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs > rustup.sh && \
    chmod +x rustup.sh && ./rustup.sh -y --profile minimal && \
    $HOME/.cargo/bin/rustup update

ENV PATH="/root/.cargo/bin:$PATH"

ENV RUSTFLAGS="-C target-cpu=x86-64-v3"

RUN git clone --revision=62c307295ade75fefb42add1072a49fa0024bf4e --depth=1 https://github.com/tcheran-chess/tcheran.git tcheran && \
    cd tcheran && \
    cargo build --release --package engine --no-default-features --features release && \
    mv target/$(rustc --print host-tuple)/release/tcheran tcheran


FROM ubuntu:26.04

COPY --from=builder /tcheran/tcheran /usr/local/bin/tcheran

CMD [ "/usr/local/bin/tcheran" ]
