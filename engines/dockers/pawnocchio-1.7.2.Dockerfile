FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive
ARG PAWN_VERSION=1.7.2

RUN apt update && apt-get -y install wget

RUN wget -O pawnocchio https://github.com/JonathanHallstrom/pawnocchio/releases/download/v${PAWN_VERSION}/pawnocchio-${PAWN_VERSION}-linux-x86_64_v3 \
    && chmod +x pawnocchio

FROM ubuntu:24.04

COPY --from=builder /pawnocchio /usr/local/bin/pawnocchio

CMD [ "/usr/local/bin/pawnocchio" ]
