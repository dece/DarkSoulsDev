import os

from sieglib.external_archive import ExternalArchive


GAME_DIR = r"F:\Jeux\Steam\SteamApps\common\Dark Souls Prepare to Die Edition"
DATA_DIR = os.path.join(GAME_DIR, "DATA")
BHD_PATH = os.path.join(DATA_DIR, "dvdbnd0.bhd5")

RESOURCES_DIR        = r"F:\Dev\Projets\DarkSoulsDev\Ressources"
FILELISTS_DIR        = os.path.join(RESOURCES_DIR, "Filelists")
DVDBND0_HASHMAP_PATH = os.path.join(FILELISTS_DIR, "dvdbnd0.hashmap.json")

WORKSPACE_DIR = r"F:\Dev\Projets\DarkSoulsDev\Workspace"


def main():
    archive = ExternalArchive()
    archive.load(BHD_PATH)
    archive.load_filelist(DVDBND0_HASHMAP_PATH)

    first_entry = archive.bhd.records[14].entries[0]
    archive.extract_all_files(WORKSPACE_DIR + "/RootFiles/0/")


if __name__ == "__main__":
    main()
