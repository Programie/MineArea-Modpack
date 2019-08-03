#! /bin/bash

set -e

server_properties_file="${MINECRAFT_DIR}/server.properties"

if [[ ! -e ${server_properties_file} ]]; then
    echo "${server_properties_file} not found!"
    exit 1
fi

rcon_port=$(fgrep "rcon.port" ${server_properties_file} | cut -d "=" -f 2 | tr -d " ")
rcon_password=$(fgrep "rcon.password" ${server_properties_file} | cut -d "=" -f 2 | tr -d " ")

/opt/mcrcon -H localhost -P ${rcon_port} -p "${rcon_password}" "$@"