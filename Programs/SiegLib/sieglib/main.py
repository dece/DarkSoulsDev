import argparse
import os

from sieglib.external_archive import ExternalArchive

DESCRIPTION = """\
Dark Souls archive formats library

You can use this library to export files from the game's archive to your disk,
and generate new archives once you modified them.\
"""

SIEGLIB_DIR         = os.path.dirname(os.path.dirname(__file__))
FILELISTS_DIR       = os.path.join(SIEGLIB_DIR, "resources")
DVDBND_HASHMAP_PATH = os.path.join(FILELISTS_DIR, "dvdbnd{}.hashmap.json")

ARGS = [
    {
        "command": ("-e",),
        "params":  { "dest": "bhd",
                     "type": str,
                     "help": "export data from this archive file" }
    },
    {
        "command": ("-E",),
        "params":  { "dest": "data_dir",
                     "type": str,
                     "help": "export data from all archives in that directory" }
    },
    {
        "command": ("-l",),
        "params":  { "dest": "filelist",
                     "type": str,
                     "help": "specify BHD filelists (-E has default files)" }
    },
    {
        "command": ("-i",),
        "params":  { "dest": "archive_tree",
                     "type": str,
                     "help": "import data from that directory tree" }
    },
    {
        "command": ("-I",),
        "params":  { "dest": "archives_tree",
                     "type": str,
                     "help": "generate archives from that exported file tree" }
    },
    {
        "command": ("-o",),
        "params":  { "dest": "output",
                     "type": str,
                     "required": True,
                     "help": "output directory" }
    }
]


def main():
    argparser = argparse.ArgumentParser(description = DESCRIPTION)
    for arg in ARGS:
        argparser.add_argument(*arg["command"], **arg["params"])
    args = argparser.parse_args()

    if args.bhd:
        export_archive(args.bhd, args.filelist, args.output)
    elif args.data_dir:
        export_archives(args.data_dir, args.filelist, args.output)
    elif args.archive_tree:
        import_files(args.archive_tree, args.output)
    elif args.dir_tree:
        pass

def export_archive(bhd_path, filelist_path, output_dir):
    archive = ExternalArchive()
    archive.load(bhd_path)
    if filelist_path:
        archive.load_filelist(filelist_path)
    archive.export_all_files(output_dir)

def export_archives(data_dir, filelist_path, output_dir):
    use_default_filelist = filelist_path is None
    for index in [str(i) for i in range(4)]:
        bhd_name = "dvdbnd{}.bhd5".format(index)
        bhd_path = os.path.join(data_dir, bhd_name)
        if use_default_filelist:
            filelist_path = DVDBND_HASHMAP_PATH.format(index)
        archive_workspace = os.path.join(output_dir, index)
        export_archive(bhd_path, filelist_path, archive_workspace)

def import_files(archive_tree, output_dir, index = None):
    if index is None:
        bhd_name = "dvdbnd.bhd5"
    else:
        bhd_name = "dvdbnd{}.bhd5".format(index)
    archive_bhd_path = os.path.join(output_dir, bhd_name)
    archive = ExternalArchive()
    archive.import_files(archive_tree, archive_bhd_path)

# def reimport_archive(archives_dir, output_dir):
#     root = os.path.join(output_dir, ARCHIVES_ROOT_NAME)
#     for index in [str(i) for i in range(4)]:
#         pass


if __name__ == "__main__":
    main()
