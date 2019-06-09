#! /usr/bin/env python3

import os
import readline
import sys

from mcrcon import MCRcon
from jproperties import Properties

server_roperties_file = os.path.join(os.getenv("MINECRAFT_DIR"), "server.properties")
history_file = os.path.expanduser("~/.mcrcon_history")

if not os.path.exists(server_roperties_file):
    print("{} not found!".format(server_roperties_file))
    exit(1)

server_properties = Properties.load(server_roperties_file)

if "enable-rcon" not in server_properties or server_properties["enable-rcon"].lower() != "true":
    print("RCON is not enabled!")
    exit(1)

if "rcon.port" not in server_properties:
    print("RCON port is not configured!")
    exit(1)

if "rcon.password" not in server_properties:
    print("RCON password is not configured!")
    exit(1)

rcon_host = "localhost"
rcon_port = int(server_properties["rcon.port"])
rcon_password = server_properties["rcon.password"]

with MCRcon(host=rcon_host, port=rcon_port, password=rcon_password) as rcon:
    if len(sys.argv) < 2:
        if os.isatty(sys.stdout.fileno()):
            if os.path.isfile(history_file):
                readline.read_history_file(history_file)

            try:
                while True:
                    command = input("{}:{} > ".format(rcon_host, rcon_port)).strip()

                    if not command:
                        continue

                    command_lower = command.lower()
                    if command_lower == "quit" or command_lower == "exit":
                        break

                    response = rcon.command(command)
                    if response:
                        print(response, end="\n")
            except (EOFError, KeyboardInterrupt):
                pass
            finally:
                readline.write_history_file(history_file)

                rcon.disconnect()
        else:
            print("Usage: {} <command>".format(sys.argv[0]), file=sys.stderr)
            exit(1)
    else:
        print(rcon.command(" ".join(sys.argv[1:])))
