FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Horsie && \
    cd Horsie && \
    git remote add origin https://github.com/liamt19/Horsie.git && \
    git fetch --depth 1 origin 467fd773a18ab756249f9f95d4c0b3c5e520a0ca && \
    git checkout FETCH_HEAD && \
    make -j avx2-bmi2

FROM ubuntu:24.04

COPY --from=builder /Horsie/horsie /usr/local/bin/Horsie

CMD [ "/usr/local/bin/Horsie" ]
