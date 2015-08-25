import os
from struct import Struct


BND_MAGIC_307C15R17 = \
        b"\x42\x4E\x44\x33\x30\x37\x43\x31\x35\x52\x31\x37\x70\x00\x00\x00"
BND_MAGIC_307D7R6   = \
        b"\x42\x4E\x44\x33\x30\x37\x44\x37\x52\x36\x00\x00\x74\x00\x00\x00"
BND_MAGIC_307M13L29 = \
        b"\x42\x4E\x44\x33\x30\x37\x4D\x31\x33\x4C\x32\x39\x74\x00\x00\x00"

BND_MAGICS = [
    BND_MAGIC_307D7R6,
    BND_MAGIC_307M13L29,
    BND_MAGIC_307C15R17
]

HEADER_BIN = Struct("<16s4I")
ENTRY_BIN = Struct("<6I")


class StandaloneArchive(object):
    """ BND parser. """

    def __init__(self):
        self.magic = 0
        self.num_entries = 0
        self.data_offset = 0
        # self.unk1 = 0
        # self.unk2 = 0
        self.entries = []
        self.dirname = ""

    def load_file(self, bnd_file_path):
        self.dirname = os.path.dirname(bnd_file_path)
        print("Loading", bnd_file_path)
        with open(bnd_file_path, "rb") as bnd_file:
            self._load_header(bnd_file)
            self._load_entries(bnd_file)

    def _load_header(self, bnd_file):
        bnd_file.seek(0)
        data = bnd_file.read(HEADER_BIN.size)
        unpacked = HEADER_BIN.unpack(data)
        self.magic = unpacked[0]
        self.num_entries = unpacked[1]
        self.data_offset = unpacked[2]
        # self.unk1 = unpacked[3]
        # self.unk2 = unpacked[4]
        assert self.magic in BND_MAGICS

    def _load_entries(self, bnd_file):
        bnd_file.seek(HEADER_BIN.size)
        offset = bnd_file.tell()
        for _ in range(self.num_entries):
            entry = StandaloneArchiveEntry()
            entry.load_entry(bnd_file, offset)
            self.entries.append(entry)
            offset += ENTRY_BIN.size

    def extract_all_files(self, output_dir, force_output_dir = False):
        """ Extract all files contained in this archive.

        The output_dir parameter is used only as root for absolute file names.
        Relative file names are placed relatively to the BND file, except if
        force_output_dir is set to True.
        """
        if self.magic != BND_MAGIC_307D7R6:
            print("Not implemented BND format")
            return
        for file_entry in self.entries:
            if file_entry.has_absolute_file_name() or force_output_dir:
                target_dir = output_dir
            else:
                target_dir = self.dirname
            full_path = os.path.join(target_dir, file_entry.joinable_name)
            os.makedirs(os.path.dirname(full_path), exist_ok = True)
            file_entry.extract_entry(full_path)


class StandaloneArchiveEntry(object):
    """

    Attributes:
        data_size: see BND documentation
        data_offset: see BND documentation
        ident: see BND documentation
        name_offset: see BND documentation
        file_name: raw file name linked to this entry
        joinable_name: relative file name that can be safely used with join
        file_data: file bytes
    """

    def __init__(self):
        # self.unk1 = 0
        self.data_size = 0
        self.data_offset = 0
        self.ident = 0
        self.name_offset = 0
        # self.unk2 = 0
        self.file_name = ""
        self.joinable_name = ""
        self.file_data = b""

    def __str__(self):
        return "Entry {} of size {} at offset {}, named: {}".format(
            self.ident, self.data_size, self.data_offset, self.file_name
        )

    def load_entry(self, bnd_file, offset):
        bnd_file.seek(offset)
        data = bnd_file.read(ENTRY_BIN.size)
        unpacked = ENTRY_BIN.unpack(data)
        # self.unk1 = unpacked[0]
        self.data_size = unpacked[1]
        self.data_offset = unpacked[2]
        self.ident = unpacked[3]
        self.name_offset = unpacked[4]
        # self.unk2 = unpacked[5]
        self._load_names(bnd_file)
        self._load_data(bnd_file)

    def _load_names(self, bnd_file):
        name_bytes = b""
        offset = self.name_offset
        while True:
            bnd_file.seek(offset)
            next_byte = bnd_file.read(1)
            if not next_byte or next_byte == b"\x00":
                break
            name_bytes += next_byte
            offset += 1
        self.file_name = name_bytes.decode(errors = "ignore")
        self._compute_joinable_name()

    def _compute_joinable_name(self):
        normpath = os.path.normpath(self.file_name)
        if self.has_absolute_file_name():
            path_without_drive_letter = normpath[2:].lstrip(os.path.sep)
            normpath = os.path.join("N", path_without_drive_letter)
        else:
            normpath = normpath.lstrip(os.path.sep)
        self.joinable_name = normpath

    def _load_data(self, bnd_file):
        bnd_file.seek(self.data_offset)
        print(self.data_size)
        self.file_data = bnd_file.read(self.data_size)

    def has_absolute_file_name(self):
        return self.file_name.startswith("N:")

    def extract_entry(self, output_file_path):
        print("Extracting BND file at", output_file_path)
        with open(output_file_path, "wb") as output_file:
            output_file.write(self.file_data)
