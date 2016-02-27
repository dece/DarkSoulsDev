import os
import sys
import tkinter as tk
import tkinter.filedialog as tkfd

from sieglib.bnd import Bnd


def main():
    root = tk.Tk()
    root.withdraw()

    if len(sys.argv) == 1:
        select_and_process(root)
    elif len(sys.argv) == 2:
        process(sys.argv[1])

    root.destroy()

def select_and_process(root):
    file_path = tkfd.askopenfilename(parent = root)
    process(file_path)

def process(file_path):
    file_path = os.path.normpath(file_path)
    if not os.path.isfile(file_path):
        return
    if file_path.endswith("bnd"):
        extract_bnd(file_path)

def extract_bnd(bnd_path):
    print("Extract", bnd_path)
    bnd = Bnd()
    load_success = bnd.load(bnd_path)
    if not load_success:
        return
    output_dir = os.path.join(
        os.path.dirname(bnd_path),
        os.path.splitext(os.path.basename(bnd_path))[0]
    )
    bnd.extract_all_files(output_dir)


if __name__ == "__main__":
    main()
