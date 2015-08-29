from struct import Struct


BHD5_MAGIC = 0x35444842

HEADER_BIN = Struct("<6I")
ENTRY_RECORD_BIN = Struct("<2I")
DATA_ENTRY_BIN = Struct("<4I")


class CombinedExternalArchiveHeader(object):
    """ BHD5 parser. Some useless elements commented for performance.

    To keep all offsets valid, do not modify the entry_records end data_entries
    lists directly but use the given methods to work with them. Currently, only
    adding stuff is supported.
    """

    def __init__(self):
        self.magic = 0
        self.unk1 = 0
        self.unk2 = 0
        self.file_size = 0
        self.num_records = 0
        self.records_offset = 0

        self.entry_records = []
        self.data_entries = []

    def load_file(self, header_file_path):
        with open(header_file_path, "rb") as header_file:
            self._load_header(header_file)
            self._load_entry_records(header_file)
            self._load_data_entries(header_file)

    def _load_header(self, header_file):
        header_file.seek(0)
        data = header_file.read(HEADER_BIN.size)
        unpacked = HEADER_BIN.unpack(data)
        self.magic = unpacked[0]
        self.unk1 = unpacked[1]
        self.unk2 = unpacked[2]
        self.file_size = unpacked[3]
        self.num_records = unpacked[4]
        self.records_offset = unpacked[5]
        assert self.magic == BHD5_MAGIC

    def _load_entry_records(self, header_file):
        header_file.seek(self.records_offset)
        offset = self.records_offset
        for _ in range(self.num_records):
            record = EntryRecord()
            record.load_record(header_file, offset)
            self.entry_records.append(record)
            offset += ENTRY_RECORD_BIN.size

    def _load_data_entries(self, header_file):
        for entry_record in self.entry_records:
            offset = entry_record.entries_offset
            for _ in range(entry_record.num_entries):
                data_entry = DataEntry()
                data_entry.load_entry(header_file, offset)
                self.data_entries.append(data_entry)
                offset += DATA_ENTRY_BIN.size

    def add_record(self, new_record):
        """ Add a record to the BHD and updates all other records offsets. """
        self.entry_records.append(new_record)
        self.file_size += ENTRY_RECORD_BIN.size
        self.num_records += 1
        for record in self.entry_records:
            record.entries_offset += ENTRY_RECORD_BIN.size

    def add_entry(self, new_entry):
        entry_offset = ( HEADER_BIN.size
                       + self.num_records * ENTRY_RECORD_BIN.size
                       + len(self.data_entries) * DATA_ENTRY_BIN.size )
        self.data_entries.append(new_entry)
        self.file_size += DATA_ENTRY_BIN.size
        return entry_offset


class EntryRecord(object):
    """ Entry record, pointing to a bunch of data entries. """

    def __init__(self):
        self.num_entries = 0
        self.entries_offset = 0

    def load_record(self, header_file, offset):
        header_file.seek(offset)
        data = header_file.read(ENTRY_RECORD_BIN.size)
        unpacked = ENTRY_RECORD_BIN.unpack(data)
        self.num_entries = unpacked[0]
        self.entries_offset = unpacked[1]


class DataEntry(object):
    """ Data entry, describing of to parse the content archive file. """

    def __init__(self):
        self.hash = 0
        self.size = 0
        self.offset = 0
        self.unk = 0

    def __str__(self):
        return "Entry of {} bytes at offset {} of hash {}".format(
            self.size, self.offset, self.hash
        )

    def load_entry(self, header_file, offset):
        header_file.seek(offset)
        data = header_file.read(DATA_ENTRY_BIN.size)
        unpacked = DATA_ENTRY_BIN.unpack(data)
        self.hash = unpacked[0]
        self.size = unpacked[1]
        self.offset = unpacked[2]
        self.unk = unpacked[3]
