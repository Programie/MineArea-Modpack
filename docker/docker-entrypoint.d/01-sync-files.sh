#! /bin/bash

rsync -a --exclude server.properties /usr/src/minecraft/ ${MINECRAFT_DIR}/

rsync -a --delete \
      /usr/src/minecraft/libraries \
      /usr/src/minecraft/mods \
      ${MINECRAFT_DIR}

if [[ ! -e ${MINECRAFT_DIR}/server.properties ]]; then
    cp /usr/src/minecraft/server.properties ${MINECRAFT_DIR}/server.properties
fi