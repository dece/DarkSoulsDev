import argparse
import os

from sieglib.config import RESOURCES_DIR
from sieglib.external_archive import ExternalArchive

DESCRIPTION = """
Dark Souls archive formats library. You can use this library to export files
from the game's archive to your disk, and generate new archives once you
modified them.
"""

DVDBND_HASHMAP_PATH = os.path.join(RESOURCES_DIR, "dvdbnd{}.hashmap.json")

ARGS = [
    {
        "command": ("-e", "--export-archive"),
        "params":  { "dest": "bhd",
                     "type": str,
                     "help": "export data from this archive file" }
    },
    {
        "command": ("-E", "--export-archives"),
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
        "command": ("-i", "--import-files"),
        "params":  { "dest": "archive_tree",
                     "type": str,
                     "help": "import data from that directory tree" }
    },
    {
        "command": ("-I", "--reimport-archives"),
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
        export_archive(args.bhd, args.output, args.filelist)
    elif args.data_dir:
        export_archives(args.data_dir, args.output, args.filelist)
    elif args.archive_tree:
        import_files(args.archive_tree, args.output)
    elif args.archives_tree:
        reimport_archives(args.archives_tree, args.output)

def export_archive(bhd_path, output_dir, filelist_path):
    """ Export the archive located at bhd_path in the directory output_dir.
    A filelist can be provided as filelist_path. """
    archive = ExternalArchive()
    archive.load(bhd_path)
    if filelist_path:
        archive.load_filelist(filelist_path)
    archive.export_all_files(output_dir)

def export_archives(data_dir, output_dir, filelist_path = None):
    """ Export the Dark Souls archives located in the data_dir directory, to
    the output_dir. A subdirectory for each archive will be created. A filelist
    can be provided as filelist_path, but default filelists are available. """
    use_default_filelist = filelist_path is None
    for index in [str(i) for i in range(4)]:
        bhd_name = "dvdbnd{}.bhd5".format(index)
        bhd_path = os.path.join(data_dir, bhd_name)
        if use_default_filelist:
            filelist_path = DVDBND_HASHMAP_PATH.format(index)
        archive_workspace = os.path.join(output_dir, index)
        export_archive(bhd_path, filelist_path, archive_workspace)

def import_files(archive_tree, output_dir, index = None):
    """ Import the data located in archive_tree in an external archive that will
    be written in output_dir. An archive index can be provided. """
    if index is None:
        bhd_name = "dvdbnd.bhd5"
    else:
        bhd_name = "dvdbnd{}.bhd5".format(index)
    archive_bhd_path = os.path.join(output_dir, bhd_name)
    archive = ExternalArchive()
    archive.import_files(archive_tree, archive_bhd_path)

def reimport_archives(archives_tree, output_dir):
    """ Generate Dark Souls archives from the archives tree formerly created by
    using the export_archives function; files are written in output_dir. """
    for index in [str(i) for i in range(4)]:
        archive_tree = os.path.join(archives_tree, index)
        import_files(archive_tree, output_dir, index)


if __name__ == "__main__":
    main()
