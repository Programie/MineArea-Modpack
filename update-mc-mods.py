#! /usr/bin/env python3

import csv
import glob
import json
import os
import requests
import sys
import zipfile

from urllib.parse import urlparse


def get_modinfo(filename):
    name = None
    version = None

    try:
        zip = zipfile.ZipFile(filename)
        mod_info = json.loads(zip.read("mcmod.info"))

        mod_info = mod_info[0]

        if "name" in mod_info:
            mod_name = mod_info["name"]
        
        if "version" in mod_info:
            version = mod_info["version"]
    except Exception as exception:
        print("Unable to read mcmod.info: {}".format(exception), file=sys.stderr)
    
    return name, version


def download_file(url, local_filename):
    print("Downloading {} to {}".format(url, local_filename))

    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(local_filename, "wb") as local_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        local_file.write(chunk)
        return True
    except Exception as exception:
        print("Download failed: {}".format(exception), file=sys.stderr)
        return False


root_dir = os.path.dirname(os.path.realpath(__file__))
mods_dir = os.path.join(root_dir, "source", "mods")
latest_url_suffix = "/files/latest"

mod_list_file = os.path.join(root_dir, "mods.csv")
update_info_file = os.path.join(root_dir, "updated-mods.txt")

with open(mod_list_file) as csv_file:
    mods = csv.reader(csv_file)

    with open(update_info_file, "w") as update_info:
        for line_index, mod in enumerate(mods):
            # First line contains the column headers
            if line_index == 0:
                continue

            prefix, url = mod

            if not url:
                print("No URL defined for {}".format(prefix), file=sys.stderr)
                continue

            parsed_url = urlparse(url)

            if parsed_url.netloc != "minecraft.curseforge.com":
                print("Skipping non-curseforge URL: {}".format(url), file=sys.stderr)
                continue

            file_pattern = "{}*".format(prefix)

            matching_files = glob.glob(os.path.join(mods_dir, file_pattern))

            if not matching_files:
                print("No files found matching pattern {}".format(
                    file_pattern), file=sys.stderr)
                continue
            elif len(matching_files) > 1:
                print("Multiple files matching pattern: {}".format(
                    file_pattern), file=sys.stderr)
                continue
            
            local_filepath = matching_files[0]
            local_filename = os.path.basename(local_filepath)

            mod_name, old_version = get_modinfo(local_filepath)

            if not old_version:
                old_version = local_filename

            response = requests.get(url + latest_url_suffix, allow_redirects=False)

            download_url = response.headers["Location"]

            latest_filename = os.path.basename(download_url)

            if latest_filename == local_filename:
                print("No update found for {}".format(prefix), file=sys.stderr)
                continue
            
            download_filepath = os.path.join(mods_dir, latest_filename)

            print("Update for {} found: {} -> {}".format(prefix, local_filename, latest_filename))

            if download_file(download_url, download_filepath):
                mod_name, new_version = get_modinfo(download_filepath)

                if not mod_name:
                    mod_name = prefix
                
                if not new_version:
                    new_version = latest_filename

                update_info.write("{} ({}): {} -> {}\n".format(mod_name, url, old_version, new_version))

                os.remove(local_filepath)
            elif os.path.exists(download_filepath):
                os.remove(download_filepath)
