import os
import sys
import tkinter as tk
import tkinter.filedialog as tkfd

from sieglib.dcx import Dcx


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

    if file_path.endswith(".dcx"):
        decompress(file_path)
    else:
        compress(file_path)

def decompress(dcx_path):
    print("Decompress", dcx_path)
    dcx = Dcx()
    load_success = dcx.load(dcx_path)
    if not load_success:
        return
    basefile_path = os.path.splitext(dcx_path)[0]
    dcx.save_decompressed(basefile_path)

def compress(file_path):
    print("Compress", file_path)
    dcx = Dcx()
    load_success = dcx.load_decompressed(file_path)
    if not load_success:
        return
    dcx_path = file_path + ".dcx"
    dcx.save(dcx_path)


if __name__ == "__main__":
    main()
