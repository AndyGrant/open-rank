FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install curl

RUN curl --proto '=https' --tlsv1.2 -sSf \
    https://github.com/tcheran-chess/tcheran/releases/download/v10.0/tcheran-v10.0-linux-x86_64-v3 \
    -o /tcheran \
    && chmod +x /tcheran

FROM ubuntu:24.04

COPY --from=builder /tcheran /usr/local/bin/tcheran

CMD [ "/usr/local/bin/tcheran" ]
