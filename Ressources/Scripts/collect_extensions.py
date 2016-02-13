""" List the number of file for each extension in a directory tree. """

import argparse
import os


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("dir", type = str)
    args = argparser.parse_args()

    if os.path.isdir(args.dir):
        print_extensions(args.dir)

def print_extensions(directory):
    extensions = {}
    for _, _, files in os.walk(directory):
        for file_name in files:
            ext = os.path.splitext(file_name)[1]
            ext = ext.lstrip(".")
            if ext in extensions:
                extensions[ext] += 1
            else:
                extensions[ext] = 1

    for ext in sorted(list(extensions.keys())):
        print(ext or "<no extension>", ":", extensions[ext])


if __name__ == "__main__":
    main()
