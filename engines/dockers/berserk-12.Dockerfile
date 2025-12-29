FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install git make cmake wget curl gcc g++ clang llvm lld

RUN git init berserk && \
    cd berserk && \
    git remote add origin https://github.com/jhonnold/berserk.git && \
    git fetch --depth 1 origin 94d48b044bbad8144f7fce7a2848ac888812a1fd && \
    git checkout FETCH_HEAD && \
    cd src && \
    make -j release VERSION=12

FROM ubuntu:24.04

COPY --from=builder /berserk/src/berserk-12-x64-avx2 /usr/local/bin/berserk

CMD [ "/usr/local/bin/berserk" ]
