import json
import os
import re

from sieglib.bdt import Bdt
from sieglib.bhd import Bhd, BhdHeader, BhdRecord, BhdDataEntry
from sieglib.filelist import load_filelist
from sieglib.log import LOG
from pyshgck.time import time_it


class ExternalArchive(object):
    """ Combination of BHD and BDT. Contains methods to extract files to the
    filesystem and to generate them from a directory tree.

    Attributes:
    - bhd: Bhd object
    - bdt: Bdt object
    - filelist: dict which maps hashes to the original string
    - records_map: dict which maps record indices to the file names they contain
    """

    # Do not handle these files when crafting an archive.
    SPECIAL_FILE_TYPES = (".json",)

    # Files without a known name are named by their uppercase hex hash.
    UNNAMED_FILE_RE = re.compile(r"[0-9A-F]{8}")

    def __init__(self):
        self.bhd = None
        self.bdt = None
        self.filelist = {}
        self.records_map = {}

    def reset(self):
        self.bhd = Bhd()
        self.bdt = Bdt()
        self.filelist = {}
        self.records_map = {}

    def load(self, bhd_name):
        self.reset()
        self.bhd.load(bhd_name)
        bdt_name = os.path.splitext(bhd_name)[0] + ".bdt"
        self.bdt.open(bdt_name)

    def load_filelist(self, hashmap_path):
        self.filelist = load_filelist(hashmap_path)

    def load_records_map(self, map_path):
        """ Load the archive's records map, return True on success. """
        if not os.path.isfile(map_path):
            LOG.error("Records map file can't be found.")
            return False
        with open(map_path, "r") as records_map_file:
            self.records_map = json.load(records_map_file)
        return True

    #------------------------------
    # Extraction
    #------------------------------

    @time_it(LOG)
    def extract_all_files(self, output_dir):
        self.records_map = {}
        for index, record in enumerate(self.bhd.records):
            record_files = []
            for entry in record.entries:
                file_name = self.extract_file(entry, output_dir)
                if file_name:
                    record_files.append(file_name)
            self.records_map[index] = record_files
        self._save_records_map(output_dir)

    def _save_records_map(self, output_dir):
        """ Write the JSON map of records to their entries. """
        records_map_path = os.path.join(output_dir, "records.json")
        with open(records_map_path, "w") as records_map_file:
            json.dump(self.records_map, records_map_file)

    def extract_file(self, entry, output_dir):
        """ Extract the file corresponding to that BHD data entry, return the
        relative file path on success, None on failure """
        if not self.is_entry_valid(entry):
            LOG.error("Tried to extract a file not from this archive.")
            return None

        file_name = self.filelist.get(entry.hash) or "{:08X}".format(entry.hash)
        LOG.info("Extracting {}".format(file_name))

        file_content = self.bdt.read_entry(entry.offset, entry.size)
        content_len = len(file_content)
        if content_len != entry.size:
            LOG.error( "Tried to read {} bytes but only {} were available "
                       "(file '{}').".format(
                entry.size, content_len, file_name
            ))
            return None

        output_path = os.path.join(output_dir, file_name.lstrip("/"))
        if not os.path.isdir(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        with open(output_path, "wb") as output_file:
            output_file.write(file_content)
        return file_name

    def is_entry_valid(self, entry):
        """ Return True if that BhdDataEntry is part of this archive. """
        for record in self.bhd.records:
            if entry in record.entries:
                return True
        return False

    #------------------------------
    # Import
    #------------------------------

    @time_it(LOG)
    def import_files(self, data_dir, bhd_path):
        """ Create an external archive from the data in data_dir, return True on
        success. """
        self.reset()
        self._prepare_bdt_for_import(bhd_path)

        records_map_path = os.path.join(data_dir, "records.json")
        records_map_is_loaded = self.load_records_map(records_map_path)
        if not records_map_is_loaded:
            return False
        self._prepare_records()

        for root, _, files in os.walk(data_dir):
            for file_name in files:
                ext = os.path.splitext(file_name)[1]
                if ext in self.SPECIAL_FILE_TYPES:
                    continue
                self.import_file(data_dir, root, file_name)

        self._update_header()
        self._save_files(bhd_path)
        return True

    def _prepare_bdt_for_import(self, bhd_path):
        """ Open the BDT file in write mode and write basic data. """
        bdt_path = os.path.splitext(bhd_path)[0] + ".bdt"
        self.bdt.open(bdt_path, "wb")
        self.bdt.make_header()

    def _prepare_records(self):
        """ Prepare the BHD records list with the correct amount of records. """
        num_records = len(self.records_map.keys())
        self.bhd.records = [BhdRecord() for _ in range(num_records)]

    def import_file(self, data_dir, file_dir, file_name):
        """ Try to import the file file_name in file_dir, with data_dir as the
        archive root; create a data entry in the appropriate record, and write
        the file data in the BDT file. Return True on success. """
        file_path = os.path.join(file_dir, file_name)

        # Find rel_path: either a hashable name like "/chr/c5352.anibnd.dcx"
        # or directly a hash name like "192E66A4".
        # Create a data entry hash with an appropriate value at the same time.
        is_unnamed = self.UNNAMED_FILE_RE.match(file_name) is not None
        if is_unnamed:
            rel_path = file_name
            entry_hash = int(file_name, 16)
        else:
            rel_path = ExternalArchive._get_rel_path(data_dir, file_path)
            rel_path = "/" + rel_path
            entry_hash = BhdDataEntry.hash_name(rel_path)
        LOG.info("Importing {}".format(rel_path))

        data_entry = BhdDataEntry()
        data_entry.hash = entry_hash

        import_results = self.bdt.import_file(file_path)
        if import_results[1] == -1:  # written bytes
            return False
        data_entry.offset, data_entry.size = import_results

        record_is_updated = self._update_record(rel_path, data_entry)
        return record_is_updated

    @staticmethod
    def _get_rel_path(data_dir, file_path):
        """ Return the sanitized relative path of file_path. """
        relative_path = os.path.relpath(file_path, data_dir)
        # Invert backslashes on Windows.
        relative_path = relative_path.replace(os.path.sep, "/")
        return relative_path

    def _update_record(self, rel_path, data_entry):
        """ Add the data entry to the record associated with that relative path,
        return True on success. """
        try:
            index = next(( int(index)
                           for index, files in self.records_map.items()
                           if rel_path in files ))
        except StopIteration:
            LOG.error("File {} not in any record.".format(rel_path))
            return False
        record = self.bhd.records[index]
        record.entries.append(data_entry)
        return True

    def _update_header(self):
        """ Update the BHD header with values corresponding to the amount of
        records and entries stored; the header is then ready to write. """
        self.bhd.header = BhdHeader()

        num_records = len(self.bhd.records)
        num_data_entries = sum( ( len(record.entries)
                                  for record in self.bhd.records ) )
        file_size = (
            BhdHeader.HEADER_BIN.size +
            BhdRecord.RECORD_BIN.size * num_records +
            BhdDataEntry.DATA_ENTRY_BIN.size * num_data_entries
        )

        self.bhd.header.file_size = file_size
        self.bhd.header.num_records = num_records

    def _save_files(self, bhd_path):
        LOG.info("Saving files to disk...")
        self.bhd.save(bhd_path)
        self.bdt.close()
