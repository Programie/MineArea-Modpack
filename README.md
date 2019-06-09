# MineArea Minecraft Modpack

This repository contains a few files for creating the zip files for the MineArea Minecraft modpack.

## How to build

* Download the [Minecraft Forge installer](https://files.minecraftforge.net) and put it into `source/forge`
* Install and update mods (see section bellow)
* Build the modpack by executing `make` in the root directory of this repository

## Install and update mods

Execute `update-mc-mods.py` to download all mods listed in the mods.yaml file and update existing mods.

**Note:** This currently only works for mods available on CurseForge.

Don't forget to update the [change log](CHANGES.md).