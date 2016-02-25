from enum import IntEnum
import os
from struct import Struct

from pyshgck.bin import read_cstring, read_struct, pad_data
from sieglib.log import LOG


class BndFlags(IntEnum):
    """ Flags present in BND headers. """

    UNK1            = 0x01
    UNK2            = 0x02
    HAS_24B_ENTRIES = 0x04
    UNK4            = 0x08
    UNK5            = 0x10
    UNK6            = 0x20
    UNK7            = 0x40
    UNK8            = 0x80

    TYPE1 = 0x04 | 0x10        | 0x40
    TYPE2 =        0x10 | 0x20 | 0x40
    TYPE3 = 0x04 | 0x10 | 0x20 | 0x40


class Bnd(object):
    """ Manage BND standalone archives. """

    MAGIC        = 0x33444E42  # BND3

    # Known magics and flags. No assertions should be made about these, I just
    # collected them to try to find some meaning.
    KNOWN_MAGICS = [ pad_data(magic, 12) for magic in [
        b"BND307C15R17",
        b"BND307D7R6",
        b"BND307F31W13",
        b"BND307J12L31",
        b"BND307K31N36",
        b"BND307M13L29",
        b"BND308C1N50",
        b"BND308J17V46",
        b"BND309G17X51",
        b"BND310B20L16",
        b"BND310I2N48"
    ] ]
    KNOWN_FLAGS = [
        BndFlags.TYPE1,
        BndFlags.TYPE2,
        BndFlags.TYPE3
    ]

    # This is the root of all entries absolute paths found in the game.
    VIRTUAL_ROOT = "N:\\FRPG\\data"

    HEADER_BIN = Struct("<12sIII II")

    def __init__(self):
        self.magic = b""
        self.flags = 0
        self.num_entries = 0
        self.data_position = 0

        self.entry_bin = None
        self.entries = []

    def load(self, file_path):
        """ Load the whole BND archive in memory, return True on success. """
        try:
            with open(file_path, "rb") as bnd_file:
                self._load_header(bnd_file)
                self._load_entries(bnd_file)
        except OSError as exc:
            LOG.error("Error reading {}: {}".format(file_path, exc))
            return False
        return True

    def _load_header(self, bnd_file):
        unpacked = read_struct(bnd_file, self.HEADER_BIN)
        self.magic         = unpacked[0]
        self.flags         = unpacked[1]
        self.num_entries   = unpacked[2]
        self.data_position = unpacked[3]
        if self.magic not in self.KNOWN_MAGICS:
            magic_str = self.magic.decode("ascii", errors = "ignore")
            magic_str = magic_str.rstrip("\x00")
            LOG.debug("Unknown magic {}".format(magic_str))
        if self.flags not in self.KNOWN_FLAGS:
            LOG.debug("Unknown flags {}".format(hex(self.flags)))

        if self.flags & BndFlags.HAS_24B_ENTRIES:
            self.entry_bin = BndEntry.ENTRY_24B_BIN
        else:
            self.entry_bin = BndEntry.ENTRY_20B_BIN

    def _load_entries(self, bnd_file):
        self.entries = [None] * self.num_entries
        for index in range(self.num_entries):
            entry = BndEntry(self.entry_bin)
            entry.load(bnd_file)
            self.entries[index] = entry

    def extract_all_files(self, output_dir):
        for entry in self.entries:
            relative_path = entry.get_joinable_path()
            LOG.info("Extracting {}".format(relative_path))
            entry_path = os.path.join(output_dir, relative_path)
            entry.extract_file(entry_path)


class BndEntry(object):

    DEFAULT_UNK2 = 0

    ENTRY_20B_BIN = Struct("<5I")
    ENTRY_24B_BIN = Struct("<6I")

    def __init__(self, entry_bin = None):
        self.bin = entry_bin or BndEntry.ENTRY_20B_BIN

        self.unk1 = 0
        self.data_size = 0
        self.data_position = 0
        self.ident = 0
        self.path_position = 0
        self.unk2 = self.DEFAULT_UNK2

        self.decoded_path = ""
        self.data = b""

    def load(self, bnd_file):
        """ Load the BND entry, decode its path and load its data. """
        unpacked = read_struct(bnd_file, self.bin)
        self.unk1          = unpacked[0]
        self.data_size     = unpacked[1]
        self.data_position = unpacked[2]
        self.ident         = unpacked[3]
        self.path_position = unpacked[4]
        if len(unpacked) > 5:
            self.unk2 = unpacked[5]
        else:
            self.unk2 = self.DEFAULT_UNK2
        self._load_name_and_data(bnd_file)

    def _load_name_and_data(self, bnd_file):
        current_position = bnd_file.tell()

        bnd_file.seek(self.path_position)
        encoded_path = read_cstring(bnd_file)
        self.decoded_path = encoded_path.decode("shift_jis")

        bnd_file.seek(self.data_position)
        self.data = bnd_file.read(self.data_size)

        bnd_file.seek(current_position)

    def get_joinable_path(self):
        """ Get a relative, joinable path for this entry. If the path is
        absolute, it removes the virtual root from the path. """
        if self._has_absolute_path():
            relative_path = self.decoded_path[ len(Bnd.VIRTUAL_ROOT) : ]
        else:
            relative_path = self.decoded_path
        relative_path = os.path.normpath(relative_path)
        relative_path = relative_path.lstrip(os.path.sep)
        return relative_path

    def _has_absolute_path(self):
        return self.decoded_path.startswith(Bnd.VIRTUAL_ROOT)

    def extract_file(self, output_path):
        """ Write entry data at output_path, return True on success. """
        try:
            if not os.path.isdir(os.path.dirname(output_path)):
                os.makedirs(os.path.dirname(output_path))
            with open(output_path, "wb") as output_file:
                output_file.write(self.data)
        except OSError as exc:
            LOG.error("Error writing {}: {}".format(output_path, exc))
            return False
        return True
