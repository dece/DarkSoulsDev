import os
from struct import Struct

from dks_extractor.bhd5 import ComposedArchiveHeader
from dks_extractor.file_types import get_dummy_extension_from_data


ARCHIVE_DATA_MAGIC = b"BDF307D7R6\x00\x00\x00\x00\x00\x00"

MAGIC_BIN = Struct("16s")


class ComposedArchiveExtractor(object):
    """ Extract content from BDT/BHD5 archives. """

    def __init__(self):
        self.output_dir = os.getcwd()

    def extract_archive(self, archive_header_file_path, archive_data_file_path):
        archive_header = ComposedArchiveHeader()
        archive_header.load_file(archive_header_file_path)

        with open(archive_data_file_path, "rb") as data_file:
            self._extract_all_files(archive_header, data_file)

    def _extract_all_files(self, archive_header, data_file):
        for data_entry in archive_header.data_entries:
            data_file.seek(data_entry.offset)
            data = data_file.read(data_entry.size)

            file_name = ComposedArchiveExtractor._get_dummy_name(data_entry)
            file_ext = get_dummy_extension_from_data(data)
            full_name = file_name + "." + file_ext
            self._save_file(full_name, data)

    def _save_file(self, full_name, data):
        full_path = os.path.join(self.output_dir, full_name)
        with open(full_path, "wb") as output_file:
            output_file.write(data)

    @staticmethod
    def _get_dummy_name(data_entry):
        return "file_{:08X}".format(data_entry.hash)
