FROM programie/minecraft-server

ENV MINECRAFT_SERVER_JAR=minecraftforge.jar \
    MINECRAFT_CMD_OPTS=--noconsole

COPY ./mcrcon.sh /usr/local/bin/mcrcon
COPY ./docker-entrypoint.d/ /docker-entrypoint.d/

COPY ./server /usr/src/minecraft
COPY ./additional-files /usr/src/minecraft

RUN mv /usr/src/minecraft/forge-1.12.2-*-universal.jar /usr/src/minecraft/minecraftforge.jar