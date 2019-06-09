#! /bin/bash

find ${MINECRAFT_DIR} \! -user ${MINECRAFT_USER} -exec chown ${MINECRAFT_USER}:${MINECRAFT_GROUP} '{}' +

case "$1" in
    server)
        java_opts=("java")

        if [[ -z ${JAVA_HEAP_MAX} ]]; then
            java_opts+=("-XX:+UnlockExperimentalVMOptions" "-XX:+UseCGroupMemoryLimitForHeap")
        else
            java_opts+=("-Xmx${JAVA_HEAP_MAX}")

            if [[ ! -z ${JAVA_HEAP_MIN} ]]; then
                java_opts+=$("-Xms${JAVA_HEAP_MIN}")
            fi
        fi

        if [[ ${JMXREMOTE_ENABLE} ]]; then
            java_opts+=("-Dcom.sun.management.jmxremote" "-Dcom.sun.management.jmxremote.port=${JMXREMOTE_PORT}" "-Dcom.sun.management.jmxremote.rmi.port=${JMXREMOTE_PORT}" "-Dcom.sun.management.jmxremote.local.only=false" "-Dcom.sun.management.jmxremote.authenticate=false" "-Dcom.sun.management.jmxremote.ssl=false" "-Djava.rmi.server.hostname=${JVMREMOTE_HOSTNAME}")
        fi

        if [[ ! -z ${JAVA_OPTS} ]]; then
            java_opts+=(${JAVA_OPTS})
        fi

        java_opts+=("-jar" "${MINECRAFT_DIR}/minecraftforge.jar" "--noconsole")

        if [[ -e ${MINECRAFT_DIR}/server.properties ]] && ! grep -q "rcon.password" ${MINECRAFT_DIR}/server.properties; then
            echo "rcon.password=$(date +%s | sha256sum | base64 | head -c 32)" >> ${MINECRAFT_DIR}/server.properties
        fi

        echo "Starting Minecraft server: ${java_opts[@]}"

        exec gosu ${MINECRAFT_USER} "${java_opts[@]}"
    ;;

    *)
        exec "$@"
    ;;
esac