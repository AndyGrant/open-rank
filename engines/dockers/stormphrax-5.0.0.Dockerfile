FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Stormphrax && \
    cd Stormphrax && \
    git remote add origin https://github.com/Ciekce/Stormphrax.git && \
    git fetch --depth 1 origin 7146b18d51d21d450e6183ff42fe7995c7b0f985 && \
    git checkout FETCH_HEAD && \
    make -j avx2

FROM ubuntu:24.04

COPY --from=builder /Stormphrax/stormphrax-5.0.0-avx2 /usr/local/bin/Stormphrax

CMD [ "/usr/local/bin/Stormphrax" ]
