import json
import os

from sieglib.bhd import Bhd


GAME_DIR = r"F:\Jeux\Steam\SteamApps\common\Dark Souls Prepare to Die Edition"
DATA_DIR = os.path.join(GAME_DIR, "DATA")
BHD_PATH = os.path.join(DATA_DIR, "dvdbnd0.bhd5")

RESOURCES_DIR        = r"F:\Dev\Projets\DarkSoulsDev\Ressources"
FILELISTS_DIR        = os.path.join(RESOURCES_DIR, "Filelists")
DVDBND0_HASHMAP_PATH = os.path.join(FILELISTS_DIR, "dvdbnd0.hashmap.json")


def main():
    bhd = Bhd()
    bhd.load(BHD_PATH)

    with open(DVDBND0_HASHMAP_PATH, "r") as dvdbnd0_hashmap:
        hashmap = json.load(dvdbnd0_hashmap)
    hashmap = { int(k, 16): hashmap[k] for k in hashmap.keys() }

    for record_index, record in enumerate(bhd.records):
        print("Record #{}".format(record_index))
        for data_entry in record.entries:
            print(hashmap.get(data_entry.hash, ";("))


if __name__ == "__main__":
    main()
