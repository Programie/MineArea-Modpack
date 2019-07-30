#! /usr/bin/env python3

import argparse
import glob
import hashlib
import json
import os
import re
import requests
import sys
import yaml
import zipfile

from urllib.parse import urlparse, unquote


class MCModInfo:
    def __init__(self, jar_filename, pattern):
        self.version = None

        if jar_filename is None:
            return

        try:
            zip_file = zipfile.ZipFile(jar_filename)
            mod_info = json.loads(zip_file.read("mcmod.info"))

            mod_info = mod_info[0]
        except Exception:
            mod_info = {}

        if "version" in mod_info:
            self.version = mod_info["version"]
        else:
            # Try to get version from file pattern if it contains a wildcard character (*)
            if "*" in pattern:
                match = re.match(pattern.replace("*", "(.*)"), os.path.basename(jar_filename))
                if match:
                    self.version = match.group(1)

            # Use filename without .jar extension if version is still None
            if self.version is None:
                self.version = os.path.splitext(os.path.basename(jar_filename))[0]


class Mod:
    def __init__(self, mods_dir, data):
        self.name: str = data["name"]
        self.pattern: str = data["pattern"]
        self.url: str = data["url"]
        self.download_url: str = None
        self.latest_filename: str = None
        self.md5: str = None

        if "download_url" in data and data["download_url"] is not None:
            self.download_url = data["download_url"]
            self.set_latest_file_from_download_url()

        if "md5" in data:
            self.md5 = data["md5"]

        matching_files = glob.glob(os.path.join(mods_dir, self.pattern))

        if len(matching_files) > 1:
            raise RuntimeError("More than one file matches pattern {}".format(self.pattern))

        if matching_files:
            self.filename = matching_files[0]
        else:
            self.filename = None

    def to_yaml(self):
        yaml_data = {
            "name": self.name,
            "pattern": self.pattern,
            "url": self.url,
            "download_url": self.download_url,
            "md5": self.md5
        }

        return yaml_data

    def check_url(self):
        parsed_url = urlparse(self.url)

        if parsed_url.netloc != "www.curseforge.com":
            print("Skipping unsupported URL: {}".format(self.url), file=sys.stderr)
            return False

        return True

    def get_modinfo(self):
        return MCModInfo(self.filename, self.pattern)

    def set_latest_file_from_download_url(self):
        self.latest_filename = os.path.basename(unquote(urlparse(self.download_url).path).replace("+", " "))

    def update_latest_file(self):
        response = requests.get("{}/download".format(self.url), allow_redirects=False)

        response.raise_for_status()

        match = re.search("/minecraft/mc-mods/[^/]+/download/([0-9]+)/file", response.text)

        response = requests.get("https://www.curseforge.com{}".format(match.group(0)), allow_redirects=False)

        response.raise_for_status()

        self.download_url = response.headers["Location"]
        self.set_latest_file_from_download_url()

    def download(self, filename):
        print("Downloading {} to {}".format(self.download_url, filename))

        try:
            with requests.get(self.download_url, stream=True) as response:
                response.raise_for_status()
                with open(filename, "wb") as local_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive new chunks
                            local_file.write(chunk)
            return True
        except Exception as exception:
            print("Download failed: {}".format(exception), file=sys.stderr)
            return False

    def is_file_valid(self):
        if self.filename is None:
            return False

        if self.md5 is not None and md5file(self.filename) != self.md5:
            return None

        return True


def md5file(filename):
    md5 = hashlib.md5()

    with open(filename, "rb") as file:
        while True:
            data = file.read(65536)

            if not data:
                break

            md5.update(data)

    return md5.hexdigest()


def main():
    argument_parser = argparse.ArgumentParser(description="MineArea mods downloader")

    argument_parser.add_argument("--update", help="update all mods to their latest versions", action="store_true")

    cmd_arguments = argument_parser.parse_args()

    root_dir = os.path.dirname(os.path.realpath(__file__))
    mods_dir = os.path.join(root_dir, "source", "mods")

    if not os.path.exists(mods_dir):
        os.mkdir(mods_dir)

    mod_list_file = os.path.join(root_dir, "mods.yaml")
    update_info_file = os.path.join(root_dir, "updated-mods.txt")

    update_info_data = {
        "new": [],
        "update": []
    }

    with open(mod_list_file) as mod_list_yaml:
        mods = yaml.safe_load(mod_list_yaml)

        mods = [Mod(mods_dir, mod) for mod in mods]

        mods_to_download = []

        for mod in mods:
            if not cmd_arguments.update and mod.download_url is not None and not mod.is_file_valid():
                mods_to_download.append(mod)
                continue

            if not mod.check_url():
                continue

            if not cmd_arguments.update and mod.filename is not None:
                continue

            mod.update_latest_file()

            if mod.filename is None:
                print("New mod {} found: {}".format(mod.name, mod.latest_filename))
            else:
                current_filename = os.path.basename(mod.filename)

                if mod.latest_filename == current_filename:
                    print("No update found for {}".format(mod.name), file=sys.stderr)
                    continue

                print("Update for {} found: {} -> {}".format(mod.name, current_filename, mod.latest_filename))

            mods_to_download.append(mod)

        if not mods_to_download:
            print("Nothing to download")
            return

        print("Ready to download {} mods".format(len(mods_to_download)))
        input("Press Enter to continue...")

        for mod in mods_to_download:
            download_filepath = os.path.join(mods_dir, mod.latest_filename)
            if mod.download(download_filepath):
                old_version = mod.get_modinfo().version
                new_version = MCModInfo(download_filepath, mod.pattern).version

                if mod.filename is None:
                    update_info_data["new"].append("[{}]({})".format(mod.name, mod.url))
                elif cmd_arguments.update:
                    update_info_data["update"].append("[{}]({}): {} -> {}".format(mod.name, mod.url, old_version, new_version))

                # Remove old mod file
                if mod.filename is not None and os.path.exists(mod.filename):
                    os.remove(mod.filename)

                md5 = md5file(download_filepath)

                if cmd_arguments.update:
                    mod.md5 = md5
                else:
                    if mod.md5 is not None and mod.md5 != md5:
                        print("Warning: MD5 checksum of downloaded file does not match stored MD5 checksum!")

            elif os.path.exists(download_filepath):
                os.remove(download_filepath)

    # Dump any changes to the YAML structure (e.g. new download_url) back to the mods.yaml file
    with open(mod_list_file, "w") as mod_list_yaml:
        yaml_list = []

        for mod in mods:
            yaml_list.append(mod.to_yaml())

        yaml.dump(yaml_list, mod_list_yaml, default_flow_style=False, sort_keys=False)

    with open(update_info_file, "w") as update_info:
        if update_info_data["new"]:
            update_info.write("New mods:\n")
            for line in update_info_data["new"]:
                update_info.write("- {}\n".format(line))

        if update_info_data["update"]:
            if update_info_data["new"]:
                update_info.write("\n")

            update_info.write("Updated mods:\n")
            for line in update_info_data["update"]:
                update_info.write("- {}\n".format(line))

    print("Done")


if __name__ == "__main__":
    main()
