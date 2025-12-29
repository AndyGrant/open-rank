FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Stormphrax && \
    cd Stormphrax && \
    git remote add origin https://github.com/Ciekce/Stormphrax.git && \
    git fetch --depth 1 origin 100db5637ca4fdb0ed0fb1e27a50078f0b41ac08 && \
    git checkout FETCH_HEAD && \
    make -j avx2

FROM ubuntu:24.04

COPY --from=builder /Stormphrax/stormphrax-7.0.0-avx2 /usr/local/bin/Stormphrax

CMD [ "/usr/local/bin/Stormphrax" ]
