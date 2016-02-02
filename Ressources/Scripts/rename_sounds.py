""" Rename some game sounds according to the sheet from Illusorywall.

This script should be used with the directory tree of my extract_sounds.py
script. This is highly incomplete as its based on an incomplete list of only NPC
names. Could be done better with more data later.

Google Drive Sheet :
https://docs.google.com/spreadsheets/d/1AdlhpYFITAGnKVAIBMVverQ_E5m5xA19m0rG0Diyixs/edit#gid=0
"""

import argparse
import csv
import os
import re


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("csv_sheet", type = str, help = "CSV sheet")
    argparser.add_argument("sounds_dir", type = str, help = "sounds dir")
    args = argparser.parse_args()

    csv_sheet = os.path.abspath(args.csv_sheet)
    sounds_dir = os.path.abspath(args.sounds_dir)

    process_csv(csv_sheet, sounds_dir)

def process_csv(csv_sheet_file_path, sounds_dir):
    csv_reader = load_csv(csv_sheet_file_path)
    enemies = []
    for raw_row in csv_reader:
        enemies.append(parse_row(raw_row))

    old_dir = os.getcwd()
    os.chdir(sounds_dir)
    for directory in os.listdir(sounds_dir):
        package, model = tuple(directory.split("_"))
        new_name = get_new_name(package, model, enemies)
        if new_name:
            os.rename(directory, new_name)
    os.chdir(old_dir)

def load_csv(csv_sheet_file_path):
    with open(csv_sheet_file_path, "r") as csv_sheet_file:
        lines = csv_sheet_file.readlines()
    reader = csv.reader(lines)
    next(reader)  # Skip first line
    return reader

def parse_row(raw_row):
    return {
        "model": raw_row[0],
        "ai": raw_row[1],
        "common_name": raw_row[2],
        "real_name": raw_row[3]
    }

def get_new_name(package, model, enemies):
    for enemy in enemies:
        if enemy["model"] == model:
            new_name = package + " " + model + " " + enemy["real_name"]
            if enemy["common_name"]:
                new_name += " (" + enemy["common_name"] + ")"
            new_name = clean_string(new_name)
            return new_name
    return ""

def clean_string(dubious_string):
    return re.sub(r'[<>:"/\|?*]', "_", dubious_string)


if __name__ == "__main__":
    main()
