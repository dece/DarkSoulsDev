from enum import Enum
import os

from dks_archives.bhd5 import CombinedExternalArchiveHeader
from dks_archives.bhf import CombinedInternalArchiveHeader
import dks_archives.file_names as file_names
import dks_archives.file_types as file_types
import dks_archives.hasher as hasher


class CombinedArchiveExtractorMode(Enum):

    BHD5 = 0
    BHF = 1


class CombinedArchiveExtractor(object):
    """ Extract content from BDT/BHD5 archives. """

    def __init__(self, mode):
        self.header = None
        self.output_dir = os.getcwd()
        self.hash_map = None
        self.mode = mode

    def extract_archive(self, header_file_path, data_file_path):
        self._load_header(header_file_path)
        with open(data_file_path, "rb") as data_file:
            self._extract_all_files(data_file)

    def _load_header(self, header_file_path):
        if self.mode == CombinedArchiveExtractorMode.BHD5:
            self.header = CombinedExternalArchiveHeader()
        elif self.mode == CombinedArchiveExtractorMode.BHF:
            self.header = CombinedInternalArchiveHeader()
        self.header.load_file(header_file_path)

    def _extract_all_files(self, data_file):
        if self.mode == CombinedArchiveExtractorMode.BHD5:
            entries = self.header.data_entries
        elif self.mode == CombinedArchiveExtractorMode.BHF:
            entries = self.header.entries

        for entry in entries:
            self._extract_entry(data_file, entry)

    def _extract_entry(self, data_file, entry):
        if self.mode == CombinedArchiveExtractorMode.BHD5:
            data_file.seek(entry.offset)
            data = data_file.read(entry.size)
            file_name = self._get_full_name(entry, data[:4])
        elif self.mode == CombinedArchiveExtractorMode.BHF:
            data_file.seek(entry.data_offset)
            data = data_file.read(entry.data_size)
            file_name = entry.name

        self._save_file(file_name, data)

    def _get_full_name(self, data_entry, magic = None):
        file_hash = hasher.format_hash(data_entry.hash)
        if self.hash_map is not None and file_hash in self.hash_map:
            name = self.hash_map[file_hash]
        else:
            print("No name for file with hash", file_hash)
            name = CombinedArchiveExtractor.get_dummy_name(file_hash, magic)
        return name

    @staticmethod
    def get_dummy_name(file_hash, magic):
        file_name = "file_" + file_hash
        file_ext = file_types.get_dummy_extension_from_data(magic)
        full_name = file_name + "." + file_ext
        return full_name

    def _save_file(self, full_name, data):
        joinable_name = os.path.normpath(full_name).lstrip(os.path.sep)
        full_path = os.path.join(self.output_dir, joinable_name)
        print("Extracting", full_path)
        if os.path.isfile(full_path):
            file_names.rename_older_versions(full_path)
        else:
            os.makedirs(os.path.dirname(full_path), exist_ok = True)
        with open(full_path, "wb") as output_file:
            output_file.write(data)
