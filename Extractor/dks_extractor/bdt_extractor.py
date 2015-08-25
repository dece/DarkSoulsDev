import os
from struct import Struct

from dks_extractor.bhd5 import ComposedArchiveHeader
from dks_extractor.file_types import get_dummy_extension_from_data
from dks_extractor.hasher import format_hash


ARCHIVE_DATA_MAGIC = b"BDF307D7R6\x00\x00\x00\x00\x00\x00"

MAGIC_BIN = Struct("16s")


class ComposedArchiveExtractor(object):
    """ Extract content from BDT/BHD5 archives. """

    def __init__(self):
        self.output_dir = os.getcwd()
        self.hash_map = None

    def extract_archive(self, header_file_path, data_file_path):
        archive_header = ComposedArchiveHeader()
        archive_header.load_file(header_file_path)

        with open(data_file_path, "rb") as data_file:
            self._extract_all_files(archive_header, data_file)

    def _extract_all_files(self, archive_header, data_file):
        for data_entry in archive_header.data_entries:
            data_file.seek(data_entry.offset)
            data = data_file.read(data_entry.size)
            full_name = self._get_full_name(data_entry)
            self._save_file(full_name, data)

    def _get_full_name(self, data_entry):
        eight_chars_hash = format_hash(data_entry.hash)
        if self.hash_map is not None and eight_chars_hash in self.hash_map:
            full_name = self.hash_map[eight_chars_hash]
            return full_name
        else:
            print("No name for file with hash", eight_chars_hash)
            return ComposedArchiveExtractor._get_dummy_full_name(data_entry)

    @staticmethod
    def _get_dummy_full_name(data_entry):
        eight_chars_hash = format_hash(data_entry.hash)
        file_name = "file_" + eight_chars_hash
        # file_ext = get_dummy_extension_from_data(data)
        file_ext = "xxx"
        full_name = file_name + "." + file_ext
        return full_name

    def _save_file(self, full_name, data):
        joinable_name = os.path.normpath(full_name).lstrip(os.path.sep)
        full_path = os.path.join(self.output_dir, joinable_name)
        os.makedirs(os.path.dirname(full_path), exist_ok = True)
        print("Extracting", full_path)
        with open(full_path, "wb") as output_file:
            output_file.write(data)
