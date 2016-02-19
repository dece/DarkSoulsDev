import os
from struct import Struct

from pyshgck.bin import read_cstring, read_struct
from solairelib.log import LOG


class Tpf(object):

    MAGIC = b"TPF\x00"

    HEADER_BIN = Struct("<4sIII")

    def __init__(self):
        self.data_entries = []

    def load(self, file_path):
        try:
            with open(file_path, "rb") as tpf_file:
                self._load_entries(tpf_file)
        except OSError as exc:
            LOG.error("Error reading '{}': {}".format(file_path, exc))
            return False
        return True

    def _load_entries(self, tpf_file):
        tpf_file.seek(0)
        unpacked = read_struct(tpf_file, self.HEADER_BIN)
        num_entries = unpacked[2]
        self.data_entries = [None] * num_entries
        for index in range(num_entries):
            entry = TpfDataEntry()
            entry.load(tpf_file)
            self.data_entries[index] = entry

    def extract_textures(self, output_dir, add_extension = True):
        for entry in self.data_entries:
            name = entry.name
            entry_path = os.path.join(output_dir, name)
            if add_extension:
                entry_path += ".dds"

            try:
                with open(entry_path, "wb") as dds_file:
                    dds_file.write(entry.data)
            except OSError as exc:
                LOG.error("Error writing texture {}: {}".format(name, exc))


class TpfDataEntry(object):
    """ Data entry, also contains the name and the DDS data. Currently assume
    that the name is encoded in UTF8. """

    BIN = Struct("<IIIII")

    def __init__(self):
        self.position = 0
        self.size = 0
        self.unk1 = 0
        self.name_position = 0
        self.unk3 = 0

        self.name = ""
        self.data = b""

    def load(self, tpf_file):
        unpacked = read_struct(tpf_file, self.BIN)
        self.position      = unpacked[0]
        self.size          = unpacked[1]
        self.unk1          = unpacked[2]
        self.name_position = unpacked[3]
        self.unk3          = unpacked[4]
        self._load_name_and_data(tpf_file)

    def _load_name_and_data(self, tpf_file):
        current_position = tpf_file.tell()

        tpf_file.seek(self.name_position)
        self.name = read_cstring(tpf_file).decode("utf8")

        tpf_file.seek(self.position)
        self.data = tpf_file.read(self.size)

        tpf_file.seek(current_position)
