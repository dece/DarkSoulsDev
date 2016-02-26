from enum import IntEnum
import json
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

    DEFAULT_MAGIC = KNOWN_MAGICS[0]
    DEFAULT_FLAGS = BndFlags.TYPE3

    # This is the root of all entries absolute paths found in the game.
    VIRTUAL_ROOT = "N:\\FRPG\\data"

    INFOS_FILE_NAME = "bnd.json"

    HEADER_BIN = Struct("<12sIII II")

    def __init__(self):
        self.magic = self.DEFAULT_MAGIC
        self.flags = self.DEFAULT_FLAGS
        self.num_entries = 0
        self.data_position = 0

        self.entry_bin = None
        self.entries = []

    def reset(self):
        self.__init__()

    def load(self, file_path):
        """ Load the whole BND archive in memory, return True on success. """
        self.reset()
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
            magic_str = self.magic.decode("ascii")
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

    def extract_all_files(self, output_dir, write_infos = True):
        """ Extract all files contained in this archive in output_dir.

        If write_infos is True (default), a JSON file is written to the disk for
        each file, plus an additional general file for the whole BND. This
        allows you to call import_files later and use the same BND and entries
        properties, to try not to break anything when editing a file.
        """
        for entry in self.entries:
            relative_path = entry.get_joinable_path()
            LOG.info("Extracting {}".format(relative_path))
            entry_path = os.path.join(output_dir, relative_path)
            entry.extract_file(entry_path, write_infos)
        self._write_infos(output_dir)

    def _write_infos(self, output_dir):
        infos = {
            "magic": self.magic.decode("ascii"),
            "flags": self.flags
        }
        json_path = os.path.join(output_dir, self.INFOS_FILE_NAME)
        try:
            with open(json_path, "w") as infos_file:
                json.dump(infos, infos_file)
        except OSError as exc:
            LOG.error("Error writing {}: {}".format(json_path, exc))

    def import_files(self, data_dir):
        """ Import files contained in data_dir into this BND archive.

        If the BND infos file or individual files info files are found, they are
        used to load the necessary information and rebuild a similar BND file.

        Note that these info files aren't *really* required in case you are
        creating a BND from scratch (i.e. not from a previously extracted BND);
        you will need to manually provide a decoded_path to each entry after
        this function, and call set_has_absolute_path. I do not actively support
        that functionality though, you should let it write and load infos files.
        """
        self.reset()

        bnd_info_path = os.path.join(data_dir, self.INFOS_FILE_NAME)
        if os.path.isfile(bnd_info_path):
            self._load_infos(bnd_info_path)

        for root, _, files in os.walk(data_dir):
            for file_name in files:
                if file_name.endswith(".json"):
                    continue

                file_path = os.path.join(root, file_name)
                entry = BndEntry()
                entry.import_file(file_path)

    def _load_infos(self, bnd_info_path):
        try:
            with open(bnd_info_path, "r") as infos_file:
                infos = json.load(infos_file)
        except OSError as exc:
            LOG.error("Error reading {}: {}".format(bnd_info_path, exc))
            return
        self.magic = infos["magic"]
        self.flags = infos["flags"]


class BndEntry(object):

    CONST_UNK1 = 0x40

    ENTRY_20B_BIN = Struct("<5I")
    ENTRY_24B_BIN = Struct("<6I")

    def __init__(self, entry_bin = None):
        self.unk1 = self.CONST_UNK1
        self.data_size = 0
        self.data_position = 0
        self.ident = 0
        self.path_position = 0
        self.unk2 = 0

        self.bin = entry_bin or BndEntry.ENTRY_24B_BIN
        self.has_absolute_path = False
        self.decoded_path = ""
        self.data = b""

    def reset(self):
        self.__init__(BndEntry.ENTRY_24B_BIN)

    def set_has_absolute_path(self):
        """ Set the has_absolute_path variable. Should be called after
        decoded_path has been changed. """
        self.has_absolute_path = self.decoded_path.startswith(Bnd.VIRTUAL_ROOT)

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
            self.unk2 = self.data_size
        assert self.unk1 == self.CONST_UNK1
        assert self.unk2 == self.data_size

        self._load_name_and_data(bnd_file)

    def _load_name_and_data(self, bnd_file):
        current_position = bnd_file.tell()

        bnd_file.seek(self.path_position)
        encoded_path = read_cstring(bnd_file)
        self.decoded_path = encoded_path.decode("shift_jis")
        self.set_has_absolute_path()

        bnd_file.seek(self.data_position)
        self.data = bnd_file.read(self.data_size)

        bnd_file.seek(current_position)

    def get_joinable_path(self):
        """ Get a relative, joinable path for this entry. If the path is
        absolute, it removes the virtual root from the path. """
        if self.has_absolute_path:
            relative_path = self.decoded_path[ len(Bnd.VIRTUAL_ROOT) : ]
        else:
            relative_path = self.decoded_path
        relative_path = os.path.normpath(relative_path)
        relative_path = relative_path.lstrip(os.path.sep)
        return relative_path

    def extract_file(self, output_path, write_infos = True):
        """ Write entry data at output_path, return True on success. """
        try:
            if not os.path.isdir(os.path.dirname(output_path)):
                os.makedirs(os.path.dirname(output_path))
            with open(output_path, "wb") as output_file:
                output_file.write(self.data)
        except OSError as exc:
            LOG.error("Error writing {}: {}".format(output_path, exc))
            return False

        if write_infos:
            self._write_infos(output_path)

        return True

    def _write_infos(self, output_path):
        infos = {
            "ident": self.ident,
            "path": self.decoded_path
        }
        json_path = output_path + ".json"
        try:
            with open(json_path, "w") as infos_file:
                json.dump(infos, infos_file)
        except OSError as exc:
            LOG.error("Error writing {}: {}".format(json_path, exc))

    def import_file(self, file_path):
        """ Load the file at file_path and the associated informations,
        return True on success. """
        self.reset()

        file_infos_path = file_path + ".json"
        if os.path.isfile(file_infos_path):
            self._load_infos(file_infos_path)

        try:
            with open(file_path, "rb") as input_file:
                self.data = input_file.read()
        except OSError as exc:
            LOG.error("Error writing {}: {}".format(file_path, exc))
            return False

        self.data_size = os.stat(file_path).st_size
        self.unk2 = self.data_size

        return True

    def _load_infos(self, infos_path):
        try:
            with open(infos_path, "r") as infos_file:
                infos = json.load(infos_file)
        except OSError as exc:
            LOG.error("Error reading {}: {}".format(infos_path, exc))
            return
        self.ident = infos["ident"]
        self.decoded_path = infos["path"]
        self.set_has_absolute_path()
