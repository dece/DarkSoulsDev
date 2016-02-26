import os
import sys
import tkinter as tk
import tkinter.filedialog as tkfd

from solairelib.tpf import Tpf


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

    if file_path.endswith(".tpf"):
        extract_textures(file_path)

def extract_textures(tpf_path):
    print("Extracting", tpf_path)
    tpf = Tpf()
    load_success = tpf.load(tpf_path)
    if not load_success:
        return

    output_dir = os.path.splitext(tpf_path)[0]
    os.makedirs(output_dir, exist_ok = True)
    tpf.extract_textures(output_dir)


if __name__ == "__main__":
    main()
