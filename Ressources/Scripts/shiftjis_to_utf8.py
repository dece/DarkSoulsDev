import argparse
import os

DESCRIPTION = "Convert files encoded with shift_jis to UTF-8 encoded files."


def convert_file(input_file_path, output_file_path):
    with open(input_file_path, "r", encoding = "shift_jis") as input_file:
        content = input_file.read()
    with open(output_file_path, "w", encoding = "utf8") as output_file:
        output_file.write(content)


def main():
    argparser = argparse.ArgumentParser(description = DESCRIPTION)
    argparser.add_argument("input_file", type = str, help = "file to convert")
    args = argparser.parse_args()

    input_file_path = args.input_file
    if not os.path.isfile(input_file_path):
        print("File not found:", input_file_path)
        return

    output_file_path = input_file_path + ".utf8.txt"
    convert_file(input_file_path, output_file_path)


if __name__ == "__main__":
    main()
