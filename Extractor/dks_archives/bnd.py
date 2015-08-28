import os
from struct import Struct

import dks_archives.bin_utils as bin_utils
import dks_archives.file_names as file_names


HEADER_BIN = Struct("<12s5I")
ENTRY_BIN_24 = Struct("<6I")
ENTRY_BIN_20 = Struct("<5I")


class StandaloneArchive(object):
    """ BND parser. """

    FLAGS = {
        "UNK1": 0x1,
        "UNK2": 0x2,
        "USE_24_BYTES_STRUCT": 0x4,
        "UNK4": 0x8,
        "UNK5": 0x10,
        "UNK6": 0x20,
        "UNK7": 0x40,
        "UNK8": 0x80
    }

    def __init__(self):
        self.magic = 0
        self.flags = 0
        self.num_entries = 0
        self.data_offset = 0
        # self.unk2 = 0
        # self.unk3 = 0
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
        self.flags = unpacked[1]
        self.num_entries = unpacked[2]
        self.data_offset = unpacked[3]
        # self.unk1 = unpacked[4]
        # self.unk2 = unpacked[5]

    def _load_entries(self, bnd_file):
        bnd_file.seek(HEADER_BIN.size)
        entry_type = self._determine_entry_type()
        offset = bnd_file.tell()
        for _ in range(self.num_entries):
            entry = StandaloneArchiveEntry()
            entry.load_entry(bnd_file, offset, entry_type)
            self.entries.append(entry)
            offset += entry_type.size

    def _determine_entry_type(self):
        if self.flags not in [0x54, 0x70, 0x74]:
            error_message = "Unknown BndHeader.infos: {}".format(self.infos)
            raise NotImplementedError(error_message)

        if self.flags & StandaloneArchive.FLAGS["USE_24_BYTES_STRUCT"]:
            return ENTRY_BIN_24
        else:
            return ENTRY_BIN_20

    def extract_all_files(self, output_dir, force_output_dir = False):
        """ Extract all files contained in this archive.

        The output_dir parameter is used only as root for absolute file names.
        Relative file names are placed relatively to the BND file, except if
        force_output_dir is set to True.
        """
        for file_entry in self.entries:
            if file_entry.has_absolute_file_name() or force_output_dir:
                target_dir = output_dir
            else:
                target_dir = self.dirname
            full_path = os.path.join(target_dir, file_entry.joinable_name)
            os.makedirs(os.path.dirname(full_path), exist_ok = True)
            file_entry.extract_entry(full_path)


class StandaloneArchiveEntry(object):
    """ BND file entry, containing file name and data.

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

    def load_entry(self, bnd_file, offset, entry_type):
        bnd_file.seek(offset)
        data = bnd_file.read(entry_type.size)
        unpacked = entry_type.unpack(data)
        # self.unk1 = unpacked[0]
        self.data_size = unpacked[1]
        self.data_offset = unpacked[2]
        self.ident = unpacked[3]
        self.name_offset = unpacked[4]
        # if len(unpacked) > 5:
        #     self.unk2 = unpacked[5]
        self._load_names(bnd_file)
        self._load_data(bnd_file)

    def _load_names(self, bnd_file):
        name_bytes = bin_utils.read_string(bnd_file, self.name_offset)
        self.file_name = name_bytes.decode("shift_jis")
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
        self.file_data = bnd_file.read(self.data_size)

    def has_absolute_file_name(self):
        return self.file_name[:2].upper() == "N:"

    def extract_entry(self, output_file_path):
        # if os.path.isfile(output_file_path):  # TEMP, just go quicker
        #     return
        print("Extracting BND file at", output_file_path)
        if os.path.isfile(output_file_path):
            file_names.rename_older_versions(output_file_path)
        with open(output_file_path, "wb") as output_file:
            output_file.write(self.file_data)
