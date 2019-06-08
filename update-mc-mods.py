#! /usr/bin/env python3

import glob
import json
import os
import re
import requests
import sys
import yaml
import zipfile

from urllib.parse import urlparse


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

        matching_files = glob.glob(os.path.join(mods_dir, self.pattern))

        if len(matching_files) > 1:
            raise RuntimeError("More than one file matches pattern {}".format(self.pattern))

        if matching_files:
            self.filename = matching_files[0]
        else:
            self.filename = None

    def check_url(self):
        parsed_url = urlparse(self.url)

        if parsed_url.netloc != "minecraft.curseforge.com":
            print("Skipping unsupported URL: {}".format(self.url), file=sys.stderr)
            return False

        return True

    def get_modinfo(self):
        return MCModInfo(self.filename, self.pattern)

    def get_latest_file(self):
        response = requests.get("{}/files/latest".format(self.url), allow_redirects=False)

        response.raise_for_status()

        self.download_url = response.headers["Location"]

        return os.path.basename(self.download_url)

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


def main():
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
        mods = [mod for mod in mods if mod.check_url()]

        for mod in mods:
            old_version = mod.get_modinfo().version

            latest_filename = mod.get_latest_file()

            if mod.filename is not None:
                current_filename = os.path.basename(mod.filename)

                if latest_filename == current_filename:
                    print("No update found for {}".format(mod.name), file=sys.stderr)
                    continue

                print("Update for {} found: {} -> {}".format(mod.name, current_filename, latest_filename))

            download_filepath = os.path.join(mods_dir, latest_filename)
            if mod.download(download_filepath):
                new_version = MCModInfo(download_filepath, mod.pattern).version

                if mod.filename is None:
                    update_info_data["new"].append("{} ({})".format(mod.name, mod.url))
                else:
                    update_info_data["update"].append("{} ({}): {} -> {}".format(mod.name, mod.url, old_version, new_version))

                # Remove old mod file
                if mod.filename is not None and os.path.exists(mod.filename):
                    os.remove(mod.filename)
            elif os.path.exists(download_filepath):
                os.remove(download_filepath)

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


if __name__ == "__main__":
    main()
