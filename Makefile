source_dir = source
forge_dir = $(source_dir)/forge
target_dir = target
client_dir = $(target_dir)/client
server_dir = $(target_dir)/server
docker_dir = docker

all: install-forge download-mods client server

.PHONY: clean install-forge download-mods client server server-docker

clean:
	rm -rf $(target_dir)

install-forge:
	mkdir -p $(forge_dir)
	cd $(forge_dir) && java -jar forge-*-installer.jar --installServer

download-mods:
	./download-mods.py

client:
	mkdir -p $(client_dir)/bin $(client_dir)/config $(client_dir)/mods
	cp $(forge_dir)/forge-1.12.2-*-universal.jar $(client_dir)/bin/modpack.jar
	rsync -av --delete $(source_dir)/config/ $(client_dir)/config/
	rsync -av --delete --exclude-from client-mods.rsync-exclude $(source_dir)/mods/ $(client_dir)/mods/
	cd $(client_dir) && zip -r -FS ../minearea-1.12.2.zip .

server:
	mkdir -p $(server_dir)/config $(server_dir)/libraries $(server_dir)/mods
	cp $(source_dir)/eula.txt $(server_dir)/eula.txt
	cp $(forge_dir)/forge-1.12.2-*-universal.jar $(server_dir)
	cp $(forge_dir)/minecraft_server.1.12.2.jar $(server_dir)
	rsync -av --delete $(source_dir)/config/ $(server_dir)/config/
	rsync -av --delete $(forge_dir)/libraries/ $(server_dir)/libraries/
	rsync -av --delete --exclude-from server-mods.rsync-exclude $(source_dir)/mods/ $(server_dir)/mods/
	cd $(server_dir) && zip -r -FS ../minearea-1.12.2-server.zip .

server-docker: server
	rsync -av --delete $(server_dir)/ $(docker_dir)/server/
	docker build -t programie/minearea-mc-server $(docker_dir)