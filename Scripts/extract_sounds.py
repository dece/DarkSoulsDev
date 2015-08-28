""" Use FsbExtractor to extract sounds from all FSB files.

I know this is ineffective to call the program for each file but there aren't so
many of them and I need a seperate folder for each one, so that's easier that
way.
"""

import os
import subprocess


FSB_EXTRACTOR_EXE = r"F:\Dev\Projets\DarkSoulsDev\Tools\FsbExtractor.exe"
DATA_DIR = r"F:\Dev\Projets\DarkSoulsDev\ExtractedData"
OUTPUT_DIR = r"F:\Dev\Projets\DarkSoulsDev\ExtractedSounds"


def main():
    for root, _, files in os.walk(DATA_DIR):
        for file_name in files:
            extension = os.path.splitext(file_name)[1]
            if extension == ".fsb":
                relative_root = os.path.relpath(root, DATA_DIR)
                extract_file(relative_root, file_name)

def extract_file(relative_root, file_name):
    full_fsb_file_path = os.path.join(DATA_DIR, relative_root, file_name)

    file_name_no_ext = os.path.splitext(file_name)[0]
    output_dir = os.path.join(OUTPUT_DIR, relative_root, file_name_no_ext)
    os.makedirs(output_dir, exist_ok = True)

    call_fsb_extractor(full_fsb_file_path, output_dir)

def call_fsb_extractor(fsb_file, output_dir):
    log_file = os.path.join(output_dir, "log.txt")
    command = [ FSB_EXTRACTOR_EXE, "/C"
              , "/S1"
              , "/O:{}".format(output_dir)
              , "/L:{}".format(log_file)
              , "/V1"
              , fsb_file ]
    print("Executing command:", " ".join(command))
    subprocess.call(command)


if __name__ == "__main__":
    main()
