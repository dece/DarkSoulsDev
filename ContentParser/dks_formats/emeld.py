from struct import Struct

from shgck_tools.bin import read_cstring, read_struct


EMELD_MAGIC = b"ELD\x00"

HEADER_BIN = Struct("<4sI2H11I")
ENTRY_BIN = Struct("<3I")


class Emeld(object):

    def __init__(self):
        self.magic = b""
        self.unk1 = 0
        self.unk2 = 0
        self.unk3 = 0
        self.file_size = 0
        self.num_entries = 0
        self.entries_offset = 0
        self.unk4 = 0
        self.data_offset = 0
        self.unk5 = 0
        self.unk6 = 0
        self.unk7 = 0
        self.unk8 = 0
        self.unk9 = 0
        self.unk10 = 0

        self.entries = []

    def load_file(self, emeld_file_path):
        with open(emeld_file_path, "rb") as emeld_file:
            self._load_header(emeld_file)
            self._load_entries(emeld_file)
            self._load_data(emeld_file)

    def _load_header(self, emeld_file):
        emeld_file.seek(0)
        unpacked = read_struct(emeld_file, HEADER_BIN)
        self.magic = unpacked[0]
        self.unk1 = unpacked[1]
        self.unk2 = unpacked[2]
        self.unk3 = unpacked[3]
        self.file_size = unpacked[4]
        self.num_entries = unpacked[5]
        self.entries_offset = unpacked[6]
        self.unk4 = unpacked[7]
        self.data_offset = unpacked[8]
        self.unk5 = unpacked[9]
        self.unk6 = unpacked[10]
        self.unk7 = unpacked[11]
        self.unk8 = unpacked[12]
        self.unk9 = unpacked[13]
        self.unk10 = unpacked[14]
        assert self.magic == EMELD_MAGIC

    def _load_entries(self, emeld_file):
        offset = self.entries_offset
        emeld_file.seek(offset)
        for _ in range(self.num_entries):
            entry = EmeldEntry()
            entry.load_entry(emeld_file, offset)
            self.entries.append(entry)
            offset += ENTRY_BIN.size

    def _load_data(self, emeld_file):
        for entry in self.entries:
            string_offset = self.data_offset + entry.data_offset
            entry.data = read_cstring( emeld_file, string_offset
                                     , utf16_mode = True )
            entry.decode_data()

    def print_entries(self):
        for entry in self.entries:
            print(entry.ident, ":", entry.string)


class EmeldEntry(object):

    def __init__(self):
        self.ident = 0
        self.data_offset = 0
        self.unk = 0

        self.data = b""
        self.string = ""

    def load_entry(self, emeld_file, offset):
        emeld_file.seek(offset)
        unpacked = read_struct(emeld_file, ENTRY_BIN)
        self.ident = unpacked[0]
        self.data_offset = unpacked[1]
        self.unk = unpacked[2]

    def decode_data(self):
        try:
            self.string = self.data.decode("utf_16")
        except UnicodeDecodeError:
            self.string = "<decoding failed>"
