FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init Horsie && \
    cd Horsie && \
    git remote add origin https://github.com/liamt19/Horsie.git && \
    git fetch --depth 1 origin 94535e3b38eff9d14ba32c7732ae282efc1d6002 && \
    git checkout FETCH_HEAD && \
    make -j avx2-bmi2

FROM ubuntu:24.04

COPY --from=builder /Horsie/horsie /usr/local/bin/Horsie

CMD [ "/usr/local/bin/Horsie" ]
