FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt-get -y install git cmake ninja-build clang++-20 llvm-20 lld-20 && \
    update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-20 100

RUN git init sirius && \
    cd sirius && \
    git remote add origin https://github.com/mcthouacbb/Sirius.git && \
    git fetch --depth 1 origin 060b37292d8ee13b9f39726240aa6dc194f028ea && \
    git checkout FETCH_HEAD && \
    clang++ --version && \
    cmake --preset ninja-clang-x86-64-v3 && \
    cmake --build build/x86-64-v3

FROM ubuntu:24.04

COPY --from=builder /sirius/build/x86-64-v3/Sirius/sirius-x86-64-v3 /usr/local/bin/sirius

CMD [ "/usr/local/bin/sirius" ]