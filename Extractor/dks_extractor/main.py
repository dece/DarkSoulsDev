#!/usr/bin/env python3

import argparse
import os

# from dks_extractor.extractor import Extractor

DESCRIPTION = "Dark Souls archive parser"

ARCHIVE_COUPLES = [
    ("0", "dvdbnd0.bhd5", "dvdbnd0.bdt"),
    ("1", "dvdbnd1.bhd5", "dvdbnd1.bdt"),
    ("2", "dvdbnd2.bhd5", "dvdbnd2.bdt"),
    ("3", "dvdbnd3.bhd5", "dvdbnd3.bdt")
]


def main():
    argparser = argparse.ArgumentParser(description = DESCRIPTION)
    argparser.add_argument("data_dir", type = str, help = "DATA directory")
    argparser.add_argument("output_dir", type = str, help = "output directory")
    args = argparser.parse_args()

    if not os.path.isdir(args.data_dir):
        print("No directory at " + args.data_dir)
        return

    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir, exist_ok = True)

    # extract(args.data_dir, args.output_dir)

# def extract(data_dir, output_dir):
#     extractor = Extractor()
#     for archive in ARCHIVE_COUPLES:
#         header_file_path = os.path.join(data_dir, archive[1])
#         data_file_path = os.path.join(data_dir, archive[2])

#         output_subdir = os.path.join(output_dir, archive[0])
#         os.makedirs(output_subdir, exist_ok = True)

#         print("Archive #{}...".format(archive[0]))
#         extractor.output_dir = output_subdir
#         extractor.extract_archive(header_file_path, data_file_path)


if __name__ == "__main__":
    main()
