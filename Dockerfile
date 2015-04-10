FROM ubuntu:14.04
MAINTAINER Ryan Parrish <ryan@stickystyle.net>

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends wget

RUN adduser --gecos 'PocketMine-MP' --disabled-password --home /pocketmine pocketmine
USER pocketmine

WORKDIR /pocketmine
RUN mkdir configs

ENV GNUPGHOME /pocketmine
ENV PM_RELEASE beta

RUN gpg --keyserver pgp.mit.edu --recv-key 2280B75B
RUN wget -q -O - http://get.pocketmine.net/ | bash -s - -v $PM_RELEASE

VOLUME ["/pocketmine/worlds", "/pocketmine/plugins", "/pocketmine/configs", "/pocketmine/players"]

EXPOSE 19132/tcp
EXPOSE 19132/udp

RUN ln -s configs/pocketmine.yml && \
    ln -s configs/server.properties && \
    ln -s configs/banned-ips.txt && \
    ln -s configs/banned-players.txt && \
    ln -s configs/white-list.txt
CMD ["./start.sh", "--no-wizard"]
