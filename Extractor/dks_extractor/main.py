#!/usr/bin/env python3

import argparse
import os
import sys

from dks_extractor.archive_manager import ArchiveManager

DESCRIPTION = "Dark Souls archive parser"


def main():
    argparser = argparse.ArgumentParser(description = DESCRIPTION)
    argparser.add_argument("data_dir", type = str, help = "DATA directory")
    argparser.add_argument("output_dir", type = str, help = "output directory")
    argparser.add_argument("res_dir", type = str, help = "resources directory")
    args = argparser.parse_args()

    check_dir(args.data_dir)
    check_dir(args.res_dir)

    full_extraction(args.data_dir, args.output_dir, args.res_dir)

def check_dir(directory):
    if not os.path.isdir(directory):
        print("No directory at " + directory)
        sys.exit()

def full_extraction(data_dir, output_dir, resources_dir):
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok = True)

    archive_manager = ArchiveManager(resources_dir)
    archive_manager.full_extraction(data_dir, output_dir)


if __name__ == "__main__":
    main()
