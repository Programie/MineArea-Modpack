FROM openjdk:8-jre-stretch

ENV MINECRAFT_DIR=/opt/minecraft \
    MINECRAFT_USER=minecraft \
    MINECRAFT_GROUP=minecraft \
    JMXREMOTE_PORT=3000 \
    JMXREMOTE_HOSTNAME=localhost \
    GOSU_VERSION=1.11

RUN apt-get update && \
    apt-get install -y python3 python3-pip rsync && \
    pip3 install jproperties3 mcrcon wget; \
    rm -rf /var/lib/apt/lists/*

RUN wget -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-amd64" && \
    chmod +x /usr/local/bin/gosu

RUN groupadd -g 999 ${MINECRAFT_USER} && \
    useradd -d ${MINECRAFT_DIR} -m -u 999 -g 999 ${MINECRAFT_GROUP}

COPY ./mcrcon.py /usr/local/bin/mcrcon
COPY ./entrypoint.sh /entrypoint.sh

COPY ./server /usr/src/minecraft
COPY ./additional-files /usr/src/minecraft

RUN mv /usr/src/minecraft/forge-1.12.2-*-universal.jar /usr/src/minecraft/minecraftforge.jar

EXPOSE 25565 ${JMXREMOTE_PORT}

VOLUME ${MINECRAFT_DIR}

WORKDIR ${MINECRAFT_DIR}

ENTRYPOINT ["/entrypoint.sh"]

CMD ["server"]