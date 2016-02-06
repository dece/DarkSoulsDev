from struct import Struct

from pyshgck.bin import read_struct


class Bhd(object):
    """ Describe a BHD5 file. """

    def __init__(self):
        self.header = None
        self.records = []

    def load(self, file_path):
        with open(file_path, "rb") as header_file:
            self._load_header(header_file)
            self._load_records(header_file)

    def _load_header(self, header_file):
        self.header = BhdHeader()
        self.header.load(header_file)

    def _load_records(self, header_file):
        header_file.seek(self.header.records_offset)
        self.records = [None] * self.header.num_records
        for index in range(self.header.num_records):
            record = BhdRecord()
            record.load(header_file)
            self.records[index] = record


class BhdHeader(object):

    MAGIC      = 0x35444842  # BHD5
    HEADER_BIN = Struct("<6I")

    def __init__(self):
        self.magic = 0
        self.unk1 = 0
        self.unk2 = 0
        self.file_size = 0
        self.num_records = 0
        self.records_offset = 0

    def load(self, header_file):
        """ Read BHD header data. """
        header_file.seek(0)
        unpacked = read_struct(header_file, self.HEADER_BIN)
        self.magic          = unpacked[0]
        self.unk1           = unpacked[1]
        self.unk2           = unpacked[2]
        self.file_size      = unpacked[3]
        self.num_records    = unpacked[4]
        self.records_offset = unpacked[5]
        assert self.magic == self.MAGIC


class BhdRecord(object):

    RECORD_BIN = Struct("<2I")

    def __init__(self):
        self.entries = []

    def load(self, header_file):
        """ Read a BHD record data and load associated data entries. """
        num_entries, offset = read_struct(header_file, self.RECORD_BIN)
        saved_position = header_file.tell()
        self._load_data_entries(header_file, num_entries, offset)
        header_file.seek(saved_position)

    def _load_data_entries(self, header_file, num_entries, offset):
        header_file.seek(offset)
        self.entries = [None] * num_entries
        for index in range(num_entries):
            data_entry = BhdDataEntry()
            data_entry.load(header_file)
            self.entries[index] = data_entry


class BhdDataEntry(object):

    DATA_ENTRY_BIN = Struct("<4I")

    def __init__(self):
        self.hash = 0
        self.size = 0
        self.offset = 0
        self.unk = 0

    def load(self, header_file):
        data = read_struct(header_file, self.DATA_ENTRY_BIN)
        self.hash   = data[0]
        self.size   = data[1]
        self.offset = data[2]
        self.unk    = data[3]

    def __str__(self):
        return "Entry [{:08} bytes @ 0x{:08X}], hash {:08X}".format(
            self.size, self.offset, self.hash
        )


def bhd_hash(characters):
    """ Get a BHD hash from this string. """
    return _truncate_hash(_get_hash_value(characters))

def _get_hash_value(characters):
    """ Get the full hash value for this string. """
    characters = characters.lower()
    hash_value = 0
    for character in characters:
        hash_value *= 37
        hash_value += ord(character)
    return hash_value

def _truncate_hash(hash_value):
    """ Truncate a hash value to an uint32. """
    return hash_value % 2**32
