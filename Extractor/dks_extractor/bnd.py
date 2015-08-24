import os
from struct import Struct


BND_MAGIC = 0x424E4433303744375236000074000000

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

    def load_file(self, bnd_file_path):
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

    def _load_entries(self, bnd_file):
        bnd_file.seek(HEADER_BIN.size)
        offset = bnd_file.tell()
        for _ in range(self.num_entries):
            entry = StandaloneArchiveEntry()
            entry.load_entry(bnd_file, offset)
            self.entries.append(entry)
            offset += ENTRY_BIN.size

    def extract_all_files(self, output_dir):
        for file_entry in self.entries:
            joinable_subpath = file_entry.sane_name.lstrip(os.path.sep)
            full_path = os.path.join(output_dir, joinable_subpath)
            os.makedirs(os.path.dirname(full_path), exist_ok = True)

            file_entry.extract_entry(full_path)


class StandaloneArchiveEntry(object):

    def __init__(self):
        # self.unk1 = 0
        self.data_size = 0
        self.data_offset = 0
        self.ident = 0
        self.name_offset = 0
        # self.unk2 = 0
        self.file_name = ""
        self.sane_name = ""
        self.file_data = b""

    def __str__(self):
        return "Entry {} of size {} at offset {}, named: {}".format(
            self.ident, self.data_size, self.data_offset, self.sane_name
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
        print("Starting at", offset)
        while True:
            bnd_file.seek(offset)
            next_byte = bnd_file.read(1)
            print(next_byte)
            if next_byte == b"\x00":
                break
            if next_byte == b"":
                print("tendé...")
                break
            name_bytes += next_byte
            offset += 1

        self.file_name = name_bytes.decode(errors = "ignore")
        self._compute_sane_name()

    def _compute_sane_name(self):
        normalized_path = os.path.normpath(self.file_name)
        if normalized_path.startswith("N:"):
            normalized_path = normalized_path[2:]
        self.sane_name = normalized_path.replace("\\", "/")

    def _load_data(self, bnd_file):
        bnd_file.seek(self.data_offset)
        self.file_data = bnd_file.read(self.data_size)

    def extract_entry(self, output_file_path):
        with open(output_file_path, "wb") as output_file:
            output_file.write(self.file_data)
