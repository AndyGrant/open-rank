FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get -y install wget

RUN wget https://github.com/kevlu8/PZChessBot/releases/download/v6.0/pzchessbot-linux-avx2 && mv pzchessbot-linux-avx2 pzchessbot && chmod +x pzchessbot

FROM ubuntu:24.04

COPY --from=builder /pzchessbot /usr/local/bin/pzchessbot

CMD [ "/usr/local/bin/pzchessbot" ]
