FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive
ARG HALOGEN_VERSION=14.0.0

RUN apt update && apt-get -y install wget

RUN wget https://github.com/KierenP/Halogen/releases/download/v${HALOGEN_VERSION}/Halogen-${HALOGEN_VERSION}-windows-latest-avx2-pext.exe && chmod +x Halogen-${HALOGEN_VERSION}-windows-latest-avx2-pext.exe

FROM ubuntu:24.04

COPY --from=builder /Halogen-${HALOGEN_VERSION}-windows-latest-avx2-pext.exe /usr/local/bin/Halogen-${HALOGEN_VERSION}-windows-latest-avx2-pext.exe
CMD [ "/usr/local/bin/Halogen-${HALOGEN_VERSION}-windows-latest-avx2-pext.exe" ]