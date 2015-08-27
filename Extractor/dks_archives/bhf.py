from struct import Struct

import dks_archives.bin_utils as bin_utils


BHD5_MAGIC = 0x33464842

HEADER_BIN = Struct("<12s5I")
ENTRY_BIN = Struct("<6I")


class CombinedInternalArchiveHeader(object):
    """ BHD5 parser. Some useless elements commented for performance. """

    def __init__(self):
        self.magic = 0
        # self.unk1 = 0
        self.num_entries = 0
        # self.unk2 = 0
        # self.unk3 = 0
        # self.unk4 = 0
        self.entries = []

    def load_file(self, bhf_file_path):
        with open(bhf_file_path, "rb") as bhf_file:
            self._load_header(bhf_file)
            self._load_entries(bhf_file)

    def _load_header(self, bhf_file):
        bhf_file.seek(0)
        data = bnd_file.read(HEADER_BIN.size)
        unpacked = HEADER_BIN.unpack(data)
        self.magic = unpacked[0]
        # self.unk1 = unpacked[1]
        self.num_entries = unpacked[2]
        # self.unk2 = unpacked[3]
        # self.unk3 = unpacked[4]
        # self.unk4 = unpacked[5]
    
    def _load_entries(self, bhf_file):
        bhf_file.seek(HEADER_BIN.size)
        offset = bhf_file.tell()
        for _ in range(self.num_entries):
            entry = CombinedInternalArchiveHeaderEntry()
            entry.load_entry(bhf_file, offset)
            self.entries.append(entry)
            offset += ENTRY_BIN.size


class CombinedInternalArchiveHeaderEntry(object):

    def __init__(self):
        # self.unk1 = 0
        self.data_size = 0
        self.data_offset = 0
        self.ident = 0
        self.name_offset = 0
        # self.unk2 = 0
        self.name = ""

    def load_entry(self, bhf_file, offset):
        data = bhf_file.read(ENTRY_BIN.size)
        unpacked = ENTRY_BIN.unpack(data)
        # self.unk1 = unpacked[0]
        self.data_size = unpacked[1]
        self.data_offset = unpacked[2]
        self.ident = unpacked[3]
        self.name_offset = unpacked[4]
        # self.unk2 = unpacked[5]
        self._load_name(bhf_file)

    def _load_name(self, bhf_file):
        name_bytes = bin_utils.read_string(bhf_file, self.name_offset)
        self.name = name_bytes.decode("shift_jis")
