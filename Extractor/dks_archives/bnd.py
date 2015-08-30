import os
from struct import Struct

from shgck_tools.bin import read_cstring, pad_data
import dks_archives.file_names as file_names


SOME_BND_MAGIC = b"BND307D7R6\x00\x00"

HEADER_BIN = Struct("<12s5I")
ENTRY_BIN_24 = Struct("<6I")
ENTRY_BIN_20 = Struct("<5I")


class Bnd(object):
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
        self.unk1 = 0
        self.unk2 = 0

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
        self.unk1 = unpacked[4]
        self.unk2 = unpacked[5]

    def _load_entries(self, bnd_file):
        bnd_file.seek(HEADER_BIN.size)
        entry_type = self._determine_entry_type()
        offset = bnd_file.tell()
        for _ in range(self.num_entries):
            entry = BndEntry()
            entry.load_entry(bnd_file, offset, entry_type)
            self.entries.append(entry)
            offset += entry_type.size

    def _determine_entry_type(self):
        if self.flags not in [0x54, 0x70, 0x74]:
            error_message = "Unknown BndHeader.infos: {}".format(self.flags)
            raise NotImplementedError(error_message)

        if self.flags & Bnd.FLAGS["USE_24_BYTES_STRUCT"]:
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


class BndEntry(object):
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
        self.unk1 = 0
        self.data_size = 0
        self.data_offset = 0
        self.ident = 0
        self.name_offset = 0
        self.unk2 = 0

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
        self.unk1 = unpacked[0]
        self.data_size = unpacked[1]
        self.data_offset = unpacked[2]
        self.ident = unpacked[3]
        self.name_offset = unpacked[4]
        if len(unpacked) > 5:
            self.unk2 = unpacked[5]
        self._load_names(bnd_file)
        self._load_data(bnd_file)

    def _load_names(self, bnd_file):
        name_bytes = read_cstring(bnd_file, self.name_offset)
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
        print("Extracting BND file at", output_file_path)
        if os.path.isfile(output_file_path):
            file_names.rename_older_versions(output_file_path)
        with open(output_file_path, "wb") as output_file:
            output_file.write(self.file_data)


class BndCreator(object):
    """ Create a BND file from various files. """

    def __init__(self):
        self.next_ident = 0
        self.entries = []
        self.strings_data = b""
        self.files_data = b""

    def reset(self):
        self.__init__()

    def create(self, bnd_file_path):
        bnd_data = self._generate_bnd_data()
        with open(bnd_file_path, "wb") as bnd_file:
            bnd_file.write(bnd_data)

    def _generate_bnd_data(self):
        self._pad_blocks()
        strings_data = self.strings_data
        files_data = self.files_data

        strings_offset, files_offset = self._get_blocks_offset()
        entries_data = self._generate_bnd_entries(strings_offset, files_offset)

        header_data = self._generate_bnd_header(files_offset)

        bnd_data = header_data + entries_data + strings_data + files_data
        return bnd_data

    def _pad_blocks(self):
        strings_offset, _ = self._get_blocks_offset()
        self.strings_data = pad_data(
            self.strings_data, 16, start_at = strings_offset % 16
        )

    def _get_blocks_offset(self):
        """ Compute offset to strings and data blocks, once all entries and
        strings are loaded. """
        entries_data_size = ENTRY_BIN_24.size * len(self.entries)
        strings_data_offset = HEADER_BIN.size + entries_data_size
        files_data_offset = strings_data_offset + len(self.strings_data)
        return strings_data_offset, files_data_offset

    def _generate_bnd_header(self, files_offset):
        magic = SOME_BND_MAGIC
        flags = ( Bnd.FLAGS["USE_24_BYTES_STRUCT"]
                | Bnd.FLAGS["UNK5"]
                | Bnd.FLAGS["UNK6"]
                | Bnd.FLAGS["UNK7"] )
        num_entries = len(self.entries)
        data_offset = files_offset

        data = (magic, flags, num_entries, data_offset, 0, 0)
        header_data = HEADER_BIN.pack(*data)
        return header_data

    def _generate_bnd_entries(self, strings_offset, files_offset):
        entries_data = b""
        for entry in self.entries:
            unk1 = entry.unk1
            data_size = entry.data_size
            data_offset = files_offset + entry.data_offset
            ident = entry.ident
            name_offset = strings_offset + entry.name_offset
            unk2 = entry.unk2

            data = (unk1, data_size, data_offset, ident, name_offset, unk2)
            packed = ENTRY_BIN_24.pack(*data)
            entries_data += packed
        return entries_data

    def add_file(self, real_file_path, virtual_file_path):
        entry = self._create_entry(real_file_path, virtual_file_path)
        self.entries.append(entry)

    def _create_entry(self, real_file_path, virtual_file_path):
        """ Generate an incomplete entry for file at real_file_path, that will
        be at virtual_file_path in game.

        The name_offset and data_offset values are relative to the creator
        string block and files data block respectively, and need to be shifted
        later to have their correct absolute value.
        """
        entry = BndEntry()
        entry.unk1 = 0x40  # general default value
        entry.ident = self._get_next_ident()
        self._register_entry_name(entry, virtual_file_path)
        self._load_entry_file(entry, real_file_path)
        return entry

    def _get_next_ident(self):
        next_ident = self.next_ident
        self.next_ident += 1
        return next_ident

    def _register_entry_name(self, entry, virtual_file_path):
        """ Register entry name in strings_data and sets both entry's file_name
        and relative name_offset. """
        entry.name_offset = len(self.strings_data)
        name_bytes = virtual_file_path.encode("shift_jis") + b"\x00"
        self.strings_data += name_bytes

    def _load_entry_file(self, entry, file_path):
        """ Load file_data in data_size for this entry with the given file. """
        with open(file_path, "rb") as entry_file:
            file_data = entry_file.read()

        entry.data_size = len(file_data)
        entry.unk2 = entry.data_size

        if self.files_data:
            self.files_data = pad_data(self.files_data, 16)
        entry.data_offset = len(self.files_data)
        self.files_data += file_data
