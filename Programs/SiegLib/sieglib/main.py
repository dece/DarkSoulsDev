import os

from sieglib.external_archive import ExternalArchive


GAME_DIR = r"F:\Jeux\Steam\SteamApps\common\Dark Souls Prepare to Die Edition"
DATA_DIR = os.path.join(GAME_DIR, "DATA")
BHD_PATH = os.path.join(DATA_DIR, "dvdbnd{}.bhd5")

SIEGLIB_DIR         = os.path.dirname(os.path.dirname(__file__))
FILELISTS_DIR       = os.path.join(SIEGLIB_DIR, "resources")
DVDBND_HASHMAP_PATH = os.path.join(FILELISTS_DIR, "dvdbnd{}.hashmap.json")

WORKSPACE_DIR = r"F:\Dev\Projets\DarkSoulsDev\Workspace"


def main():
    for index in (0,):
        archive = ExternalArchive()
        archive.load(BHD_PATH.format(index))
        archive.load_filelist(DVDBND_HASHMAP_PATH.format(index))
        archive.extract_all_files(WORKSPACE_DIR + "/RootFiles/" + str(index))


if __name__ == "__main__":
    main()
