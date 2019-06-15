# MineArea Minecraft Modpack

This repository contains a few files for creating the zip files for the MineArea Minecraft modpack.

## How to build

* Download the [Minecraft Forge installer](https://files.minecraftforge.net) and put it into `source/forge`
* Install and update mods (see section bellow)
* Build the modpack by executing `make` in the root directory of this repository
* Optional: Build the Docker image for the Minecraft server using `make server-docker`

## Install and update mods

Execute `download-mods.py` to download all mods listed in the mods.yaml file.

In case you want to update the mods, specify the `--update` option: `download-mods.py --update`

**Note:** This currently only works for mods available on CurseForge.

Don't forget to update the [change log](CHANGES.md) after updating the mods (use the information from the updated-mods.txt file).