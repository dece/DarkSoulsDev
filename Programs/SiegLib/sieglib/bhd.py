from struct import Struct

from pyshgck.bin import read_struct
from sieglib.log import LOG


class Bhd(object):
    """ Describe a BHD5 file. """

    def __init__(self):
        self.header = None
        self.records = []

    def load(self, file_path):
        """ Load the archive at file_path, return True on success. """
        try:
            with open(file_path, "rb") as header_file:
                self._load_header(header_file)
                self._load_records(header_file)
        except OSError as exc:
            LOG.error("Error reading {}: {}".format(file_path, exc))
            return False
        return True

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

    def save(self, file_path):
        """ Save the BHD to disk, return True on success. """
        try:
            with open(file_path, "wb") as header_file:
                self.header.save(header_file)
                self._save_records(header_file)
                self._save_data_entries(header_file)
        except OSError as exc:
            LOG.error("Error writing {}: {}".format(file_path, exc))
            return False
        return True

    def _save_records(self, file_object):
        """ Save each record with an appropriate data offset. """
        offset = ( self.header.records_offset +
                   len(self.records) * BhdRecord.RECORD_BIN.size )
        for record in self.records:
            record.save(offset, file_object)
            offset += len(record.entries) * BhdDataEntry.DATA_ENTRY_BIN.size

    def _save_data_entries(self, file_object):
        """ Save each data entry of each record. """
        for record in self.records:
            for entry in record.entries:
                entry.save(file_object)


class BhdHeader(object):

    MAGIC      = 0x35444842  # BHD5
    HEADER_BIN = Struct("<6I")

    def __init__(self):
        self.magic = self.MAGIC
        self.unk1 = 0xFF
        self.unk2 = 0x01
        self.file_size = 0
        self.num_records = 0
        self.records_offset = self.HEADER_BIN.size

    def load(self, header_file):
        header_file.seek(0)
        unpacked = read_struct(header_file, self.HEADER_BIN)
        self.magic          = unpacked[0]
        self.unk1           = unpacked[1]
        self.unk2           = unpacked[2]
        self.file_size      = unpacked[3]
        self.num_records    = unpacked[4]
        self.records_offset = unpacked[5]
        assert self.magic == self.MAGIC

    def save(self, file_object):
        data = self.HEADER_BIN.pack(
            self.magic, self.unk1, self.unk2,
            self.file_size, self.num_records, self.records_offset
        )
        file_object.write(data)


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
        """ Load all data entries associated with that record. """
        header_file.seek(offset)
        self.entries = [None] * num_entries
        for index in range(num_entries):
            data_entry = BhdDataEntry()
            data_entry.load(header_file)
            self.entries[index] = data_entry

    def save(self, offset, file_object):
        data = self.RECORD_BIN.pack(len(self.entries), offset)
        file_object.write(data)


class BhdDataEntry(object):

    DATA_ENTRY_BIN = Struct("<4I")

    def __init__(self):
        self.hash = 0
        self.size = 0
        self.offset = 0
        self.unk = 0

    def __str__(self):
        return "Entry [{:08} bytes @ 0x{:08X}], hash {:08X}".format(
            self.size, self.offset, self.hash
        )

    def load(self, header_file):
        """ Load a BHD data entry. """
        data = read_struct(header_file, self.DATA_ENTRY_BIN)
        self.hash   = data[0]
        self.size   = data[1]
        self.offset = data[2]
        self.unk    = data[3]

    def save(self, file_object):
        data = self.DATA_ENTRY_BIN.pack(
            self.hash, self.size, self.offset, self.unk
        )
        file_object.write(data)

    @staticmethod
    def hash_name(characters):
        """ Hash that string. """
        full_hash = BhdDataEntry._get_hash_value(characters)
        bhd_hash = BhdDataEntry._truncate_hash(full_hash)
        return bhd_hash

    @staticmethod
    def _get_hash_value(characters):
        """ Get the full hash value for this string. """
        characters = characters.lower()
        hash_value = 0
        for character in characters:
            hash_value *= 37
            hash_value += ord(character)
        return hash_value

    @staticmethod
    def _truncate_hash(hash_value):
        """ Truncate a hash value to an uint32. """
        return hash_value % 2**32
